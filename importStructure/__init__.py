'''
oskar.eiriksson@contentstack.com
2020-09-25

Imports stack structure from chosen local folder.

See Readme for details.
'''
import os
from time import sleep, time
import ast
import inquirer
import cma
import config

def noEmptyStr(_, current):
    '''
    For inquirer
    Making sure that text input is not empty when giving new stack a name
    '''
    if len(current) > 0:
        return True
    return False

def replaceFromMapper(mapper, exportedJson, msg=''):
    '''
    Finding all uids in the export that have new uids in the import
    replacing the uid with correct one reading the dictionary with all the mapping (format: exportedUid: importedUid)
    --> Extensions get a new uid when created on a new stack
    '''
    exportString = str(exportedJson)
    config.logging.info('Running mapper on {} export'.format(msg))
    for key, value in mapper.items():
        exportString = exportString.replace(key, value)
    importedDict = ast.literal_eval(exportString)
    config.logging.info('Finished running mapper on {} export'.format(msg))
    return importedDict

def createMapperFile(apiKey, folder, mapDict, mapperName=''):
    '''
    Reusable function that creates the mapper file between exported and imported uids
    '''
    config.logging.info('Writing {} mapper to file'.format(mapperName))
    mapperFolder = config.dataRootFolder + config.stackRootFolder + config.mapperFolder + 'MAPPER_ImportTo-' + apiKey + '_ExportFrom-' + folder
    config.checkDir(config.dataRootFolder)
    config.checkDir(config.dataRootFolder + config.stackRootFolder)
    config.checkDir(config.dataRootFolder + config.stackRootFolder + config.mapperFolder)
    config.checkDir(mapperFolder)
    config.writeToJsonFile(mapDict, mapperFolder + '/' + config.fileNames[mapperName], True) # True -> Overwrite
    return mapDict

def addToMapper(mapDict, exportedUid, importedUid):
    '''
    Simple reusable function that adds to mapper dictionary
    The mapDict is used in import, to change export uids to import uids. Also written to file for audit purposed
    '''
    mapDict[exportedUid] = importedUid
    return mapDict

def createNewStack(authToken, orgUid, region):
    '''
    Creates a new stack
    '''
    body = {
        "stack": {}
        }
    stackList = [
        inquirer.Text('stackName', message="{}Give your stack a name{}".format(config.BOLD, config.END), validate=noEmptyStr),
        inquirer.Text('stackDescription', message="{}Give your stack some description{}".format(config.BOLD, config.END), default=""),
        inquirer.Text('stackMasterLocale', message="{}What language should be the master locale?{}".format(config.BOLD, config.END), default="en-us")
    ]
    stackInfo = inquirer.prompt(stackList)
    stackName = stackInfo['stackName']
    stackDescription = stackInfo['stackDescription']
    stackMasterLocale = stackInfo['stackMasterLocale']
    body['stack']['name'] = stackName
    body['stack']['description'] = stackDescription
    body['stack']['master_locale'] = stackMasterLocale
    stack = cma.createStack(authToken, orgUid, region, body)
    if stack:
        return stackName, stack
    config.logging.error('{}Exiting. Stack {} not created.{}'.format(config.RED, stackName, config.END))
    return None

def importLanguage(language, apiKey, authToken, region):
    '''
    Reused function in function below
    '''
    body = {
        'locale': {
            'code': language['code'],
            'fallback_locale': language['fallback_locale'],
            'name': language['name']
            }
        }
    languageImport = cma.createLanguage(apiKey, authToken, body, region)
    if languageImport:
        config.logging.info('Language {} imported'.format(language['code']))
        return {language['uid']: languageImport['locale']['uid']}
        
    return False

def importLanguages(apiKey, authToken, region, folder, masterLocale):
    '''
    Imports languages
    '''
    config.logging.info('{}Importing languages{}'.format(config.BOLD, config.END))
    f = config.dataRootFolder + config.stackRootFolder + folder + config.folderNames['languages']
    createdLanguages = [masterLocale]
    delayedList = []
    mapDict = {}
    for langFile in config.readDirIfExists(f):
        language = config.readFromJsonFile(f + langFile)
        if language:
            if language['code'] != masterLocale:
                if language['fallback_locale'] not in createdLanguages:# and language['code'] != masterLocale:
                    config.logging.info('Fallback Locale {} not yet created for locale {}. Delaying import.'.format(language['fallback_locale'], language['code']))
                    delayedList.append(language)
                else:
                    importedLanguage = importLanguage(language, apiKey, authToken, region)
                    if importedLanguage:
                        createdLanguages.append(language['code'])
                        mapDict.update(importedLanguage)
                    else:
                        delayedList.append(language)
        else:
            config.logging.error('{}Unable to read from Language file {}{}'.format(config.RED, langFile, config.END))
    counter = 1
    while delayedList and counter <= len(delayedList) * 5: # If we need to try this too often, we stop after len*5 times
        language = delayedList[0]
        config.logging.info('Retrying to import locale skipped earlier: {}.'.format(language['code']))
        if language['fallback_locale'] in createdLanguages:
            importedLanguage = importLanguage(language, apiKey, authToken, region)
            if importedLanguage:
                createdLanguages.append(language['code'])
                mapDict.update(importedLanguage)
            else:
                delayedList.append(language)
        else:
            delayedList.append(language)
        delayedList.pop(0)
        counter += 1

    # if we still have some languages unimported still, we just add them with the master locale as the fallback
    if delayedList:
        config.logging.warning('{}Unable to import languages with correct fallback locale defined: Importing with master locale as fallback: {}{}'.format(config.YELLOW, str(delayedList, config.END)))
        for language in delayedList:
            language['fallback_locale'] = masterLocale
            importedLanguage = importLanguage(language, apiKey, authToken, region)
            if importedLanguage:
                createdLanguages.append(language['code'])
                mapDict.update(importedLanguage)
            else:
                delayedList.append(language)
    return createMapperFile(apiKey, folder, mapDict, 'languages')

def importEnvironments(apiKey, authToken, region, folder):
    '''
    Importing environments
    '''
    config.logging.info('{}Importing environments{}'.format(config.BOLD, config.END))
    f = config.dataRootFolder + config.stackRootFolder + folder + config.folderNames['environments']
    mapDict = {}
    for envFile in config.readDirIfExists(f):
        environment = config.readFromJsonFile(f + envFile)
        if environment:
            body = {
                'environment': environment
            }
            environmentImport = cma.createEnvironment(apiKey, authToken, body, region)
            if environmentImport:
                config.logging.info('Environment {} imported'.format(environment['name']))
                mapDict = addToMapper(mapDict, environment['uid'], environmentImport['environment']['uid'])
        else:
            config.logging.error('{}Unable to read from Environments file {}{}'.format(config.RED, envFile, config.END))
    return createMapperFile(apiKey, folder, mapDict, 'environments')

def importDeliveryTokens(apiKey, authToken, region, folder):
    '''
    Importing delivery tokens
    '''
    config.logging.info('{}Importing delivery tokens{}'.format(config.BOLD, config.END))
    f = config.dataRootFolder + config.stackRootFolder + folder + config.folderNames['deliveryTokens']
    for delFile in config.readDirIfExists(f):
        deliveryToken = config.readFromJsonFile(f + delFile)
        if deliveryToken:
            body = {
                'token': {
                    'name': deliveryToken['name'],
                    'description': deliveryToken['description'],
                    'scope':    [{
                        'environments': [deliveryToken['scope'][0]['environments'][0]['name']],
                        'module': deliveryToken['scope'][0]['module'],
                        'acl': deliveryToken['scope'][0]['acl']
                    }]
                }
            }
            deliveryTokenImport = cma.createDeliveryToken(apiKey, authToken, body, region)
            if deliveryTokenImport:
                config.logging.info('Delivery Token {} imported'.format(deliveryToken['name']))
        else:
            config.logging.error('{}Unable to read from Delivery Token file {}{}'.format(config.RED, delFile, config.END))
    return True

def importExtensions(apiKey, authToken, region, folder):
    '''
    Importing extensions
    '''
    config.logging.info('{}Importing extensions{}'.format(config.BOLD, config.END))
    f = config.dataRootFolder + config.stackRootFolder + folder + config.folderNames['extensions']
    mapDict = {}
    for extFile in config.readDirIfExists(f):
        extension = config.readFromJsonFile(f + extFile)
        if extension:
            body = {
                'extension': extension
            }
            # if 'scope' in extension: # It's a custom widget - We cannot import it because it uses content types
            #     config.logging.info('Custom Widget detected. Delaying import.')
            # else:
            extensionImport = cma.createExtension(apiKey, authToken, body, region)
            if extensionImport:
                config.logging.info('Extension {} imported'.format(extension['title']))
                mapDict = addToMapper(mapDict, extension['uid'], extensionImport['extension']['uid'])
        else:
            config.logging.error('{}Unable to read from Extension file {}{}'.format(config.RED, extFile, config.END))
    return createMapperFile(apiKey, folder, mapDict, 'extensions')

def importLabel(mapDict, apiKey, authToken, label, region):
    '''
    Reused below in importLabels
    '''
    labelImport = cma.createLabel(apiKey, authToken, {'label': label}, region)
    if labelImport:
        config.logging.info('Label {} imported'.format(label['name']))
        mapDict = addToMapper(mapDict, label['uid'], labelImport['label']['uid'])
    return mapDict

def importLabels(apiKey, authToken, region, folder):
    '''
    Importing labels
    '''
    config.logging.info('{}Importing labels{}'.format(config.BOLD, config.END))
    f = config.dataRootFolder + config.stackRootFolder + folder + config.folderNames['labels']
    delayedList = []
    mapDict = {}
    for labFile in config.readDirIfExists(f):
        label = config.readFromJsonFile(f + labFile)
        if label:
            if label['parent']:
                delayedList.append(label)
            else:
                mapDict = importLabel(mapDict, apiKey, authToken, label, region)
        else:
            config.logging.error('{}Unable to read from Label file {}{}'.format(config.RED, labFile, config.END))
    counter = 1
    while delayedList and counter <= len(delayedList) * 5: # If we need to try this too often, we stop after len*5 times
        label = delayedList[0]
        try:
            newParents = []
            for parent in label['parent']:
                newParents.append(mapDict[parent])
            label['parent'] = newParents
            mapDict = importLabel(mapDict, apiKey, authToken, label, region)
        except KeyError:
            config.logging.debug('Unable to find parent label for {}'.format(label['name']))
            delayedList.append(label)
        delayedList.pop(0)
        counter += 1
    
    # If some labels are still in that list, we just import them without the hierarchy
    if delayedList:
        config.logging.warning('{}Unable to import all labels with correct parents. Importing them in the top level.{}'.format(config.YELLOW, config.END))
        labelStr = ''
        for label in delayedList:
            label['parent'] = []
            labelStr = labelStr + ', ' + label['name']
            mapDict = importLabel(mapDict, apiKey, authToken, label, region)

        config.logging.warning('{}Labels imported without parents: {}{}'.format(config.YELLOW, labelStr, config.END))

    return createMapperFile(apiKey, folder, mapDict, 'labels')

def replaceRoleRuleUids(rules, languageMapper, environmentMapper):
    '''
    Replacing environment and locale uids with new ones
    Limitation: Only works for environments and locales (plus other non blt* modules). Entries and assets haven't been imported yet.
    '''
    newRules = []
    for rule in rules:
        if rule['module'] == 'locale':
            locales = []
            for locale in rule['locales']:
                try:
                    locales.append(languageMapper[locale])
                except KeyError:
                    pass
            rule['locales'] = locales
        elif rule['module'] == 'environment':
            environments = []
            for environment in rule['environments']:
                try:
                    environments.append(environmentMapper[environment])
                except KeyError:
                    pass
            rule['environments'] = environments
        newRules.append(rule)
    return newRules


def importRoles(apiKey, authToken, region, folder, languageMapper, environmentMapper):
    '''
    Importing roles
    '''
    config.logging.info('{}Importing roles{}'.format(config.BOLD, config.END))
    f = config.dataRootFolder + config.stackRootFolder + folder + config.folderNames['roles']

    # # Getting current roles in import stack - Just to get the uid's of the buit in roles
    # currentRoles = cma.getAllRoles(apiKey, authToken, region)
    # roleUids = {
    #     'Developer': None,
    #     'Content Manager': None
    # }
    # if currentRoles: # Getting the uids for built-in roles to be able to update them
    #     for role in currentRoles['roles']:
    #         if role['name'] == 'Developer':
    #             roleUids['Developer'] = role['uid']
    #         elif role['name'] == 'Content Manager':
    #             roleUids['Content Manager'] = role['uid']

    mapDict = {}
    for roleFile in config.readDirIfExists(f):
        if roleFile not in ('Admin.json', 'Content Manager.json', 'Developer.json'): # Skipping update in built-in roles - Because it's buggy
            role = config.readFromJsonFile(f + roleFile)
            if role:
                del role['permissions']
                if 'rules' in role:
                    rules = replaceRoleRuleUids(role['rules'], languageMapper, environmentMapper)
                else:
                    rules = []
                roleImport = cma.createRole(apiKey, authToken, {'role': role}, region)
                if roleImport:
                    try:
                        mapDict = addToMapper(mapDict, role['uid'], roleImport['role']['uid'])
                    except KeyError:
                        config.logging.debug('Not able to map uid for role {}'.format(role['name']))
                    config.logging.info('{} role imported'.format(role['name']))
            else:
                config.logging.error('{}Unable to read from Role file {}{}'.format(config.RED, roleFile, config.END))
        else:
            config.logging.info('Skipping system role import: {}'.format(roleFile))
    return createMapperFile(apiKey, folder, mapDict, 'roles')

def importWorkflows(apiKey, authToken, region, folder, roleMapper):
    '''
    Importing workflows
    '''
    config.logging.info('{}Importing workflows{}'.format(config.BOLD, config.END))
    f = config.dataRootFolder + config.stackRootFolder + folder + config.folderNames['workflows']
    mapDict = {}
    for wfFile in config.readDirIfExists(f):
        workflow = config.readFromJsonFile(f + wfFile)
        if workflow:
            workflowImport = cma.createWorkflow(apiKey, authToken, {'workflow': workflow}, region)
            if workflowImport:
                mapDict = addToMapper(mapDict, workflow['uid'], workflowImport['workflow']['uid'])
                config.logging.info('{} workflow imported'.format(workflow['name']))
        else:
            config.logging.error('{}Unable to read from Workflow file {}{}'.format(config.RED, wfFile, config.END))
    return createMapperFile(apiKey, folder, mapDict, 'workflows')

def importPublishingRules(apiKey, authToken, region, folder, mappers):
    '''
    Importing publishing rules
    '''
    config.logging.info('{}Importing publishing rules{}'.format(config.BOLD, config.END))
    f = config.dataRootFolder + config.stackRootFolder + folder + config.folderNames['publishingRules']
    count = 1
    for pubFile in config.readDirIfExists(f):
        publishingRule = config.readFromJsonFile(f + pubFile)
        for key, value in mappers.items():
            publishingRule = replaceFromMapper(value, publishingRule, key) # role uids from old and new stack mapped
        publishingRuleImport = cma.createPublishingRule(apiKey, authToken, {'publishing_rule': publishingRule}, region)
        if publishingRuleImport:
            config.logging.info('Publishing Rule {} imported'.format(count))
        else:
            config.logging.error('{}Unable to read from Publishing Rule file {}{}'.format(config.RED, pubFile, config.END))
        count += 1
    return True

def importWebhooks(apiKey, authToken, region, folder):
    '''
    Importing publishing rules
    '''
    config.logging.info('{}Importing webhooks{}'.format(config.BOLD, config.END))
    if config.disableWebhooks:
        config.logging.info('{}All Enabled Webhooks will be disabled on import{}'.format(config.BOLD, config.END))
    else:
        config.logging.info('{}Webhooks will be enabled on import. Please make sure they do not trigger on live environments{}'.format(config.YELLOW, config.END))
    f = config.dataRootFolder + config.stackRootFolder + folder + config.folderNames['webhooks']
    for whfile in config.readDirIfExists(f):
        webhook = config.readFromJsonFile(f + whfile)
        if config.disableWebhooks:
            webhook['disabled'] = True
        webhookImport = cma.createWebhook(apiKey, authToken, {'webhook': webhook}, region)
        if webhookImport:
            config.logging.info('Webhook {} imported'.format(webhook['name']))
        else:
            config.logging.error('{}Unable to read from Webhook file {}{}'.format(config.RED, whfile, config.END))
    return True

def createContentTypesAndGlobalFields(apiKey, token, region, folder):
    '''
    v2 - Create empty ones before updating them again. Able to avoid issues with circular dependencies
    '''
    config.logging.info('{}Creating Content Types{}'.format(config.BOLD, config.END))
    ctFolder = config.dataRootFolder + config.stackRootFolder + folder + config.folderNames['contentTypes']
    for ctFile in config.readDirIfExists(ctFolder):
        config.logging.info('Creating content type from file: {}'.format(ctFile))
        contentType = config.readFromJsonFile(ctFolder + ctFile)
        if contentType:
            # contentType = replaceFromMapper(extensionMapper, contentType, 'content types')
            body = {
                'content_type': {
                    'title': contentType['title'],
                    'uid': contentType['uid'],
                }
            }
            schema = []
            for field in contentType['schema']:
                if field['uid'] in ('url', 'title'):
                    schema.append(field)
            body['content_type']['schema'] = schema
            ctCreate = cma.createContentType(apiKey, token, body, region)
            if ctCreate:
                config.logging.info('Content Type {} created'.format(contentType['title']))
            else:
                config.logging.critical('{}Content Type {} NOT created!{}'.format(config.RED, contentType['title'], config.END))
    config.logging.info('{}Finished creating all Content Types{}'.format(config.BOLD, config.END))
    config.logging.info('{}Creating Global Fields{}'.format(config.BOLD, config.END))
    gfFolder = config.dataRootFolder + config.stackRootFolder + folder + config.folderNames['globalFields']
    for gfFile in config.readDirIfExists(gfFolder):
        globalField = config.readFromJsonFile(gfFolder + gfFile)
        if globalField:
            body = {
                'global_field': {
                    'title': globalField['title'],
                    'uid': globalField['uid'],
                    'schema': [{"data_type": "text", "display_name": "temp field", "uid": "temp_field",}]
                }
            }
            gfCreate = cma.createGlobalField(apiKey, token, body, region)
            if gfCreate:
                config.logging.info('Global Field {} created'.format(globalField['title']))
            else:
                config.logging.critical('{}Global Field {} NOT created!{}'.format(config.RED, globalField['title'], config.END))
    config.logging.info('{}Finished creating all Global Fields{}'.format(config.BOLD, config.END))

def updateContentTypesAndGlobalFields(apiKey, token, region, folder, extensionMapper):
    '''
    Now need to update content types and global field with correct schema
    '''
    config.logging.info('{}Updating Content Types with correct schema{}'.format(config.BOLD, config.END))
    ctFolder = config.dataRootFolder + config.stackRootFolder + folder + config.folderNames['contentTypes']
    for ctFile in config.readDirIfExists(ctFolder):
        contentType = config.readFromJsonFile(ctFolder + ctFile)
        if contentType:
            contentType = replaceFromMapper(extensionMapper, contentType, 'content types')
            body = {'content_type': contentType}
            # cma.deleteContentType(apiKey, token, region, contentType['uid'])
            # ctUpdate = cma.createContentType(apiKey, token, body, region)
            ctUpdate = cma.updateContentType(apiKey, token, body, region, contentType['uid'])
            if ctUpdate:
                config.logging.info('Content Type {} updated'.format(contentType['title']))
            else:
                config.logging.critical('{}Content Type {} NOT updated!{}'.format(config.RED, contentType['title'], config.END))
    config.logging.info('{}Finished updating Content Types{}'.format(config.BOLD, config.END))
    config.logging.info('{}Updating Global Fields with correct schema{}'.format(config.BOLD, config.END))
    gfFolder = config.dataRootFolder + config.stackRootFolder + folder + config.folderNames['globalFields']
    for gfFile in config.readDirIfExists(gfFolder):
        globalField = config.readFromJsonFile(gfFolder + gfFile)
        if globalField:
            globalField = replaceFromMapper(extensionMapper, globalField, 'global fields')
            body = {'global_field': globalField}
            # cma.deleteGlobalField(apiKey, token, region, globalField['uid'])
            # gfUpdate = cma.createGlobalField(apiKey, token, body, region)
            gfUpdate = cma.updateGlobalField(apiKey, token, body, region, globalField['uid'])
            if gfUpdate:
                config.logging.info('Global Field {} updated'.format(globalField['title']))
            else:
                config.logging.critical('{}Global Field {} NOT updated!{}'.format(config.RED, globalField['title'], config.END))
    config.logging.info('{}Finished updating Global Fields{}'.format(config.BOLD, config.END))

def importStack(importedStack, token, region, folder):
    '''
    Import stack function
    '''
    apiKey = importedStack['uid']
    config.logging.info('{}Starting structure import{}'.format(config.BOLD, config.END))
    startTime = time()
    createContentTypesAndGlobalFields(apiKey, token, region, folder)
    languageMapper = importLanguages(apiKey, token, region, folder, importedStack['masterLocale'])
    environmentMapper = importEnvironments(apiKey, token, region, folder)
    if not environmentMapper:
        config.logging.info('{}No Environmentsmapper present. Were there any environments in the export?{}'.format(config.YELLOW, config.END))
    importDeliveryTokens(apiKey, token, region, folder)
    extensionMapper = importExtensions(apiKey, token, region, folder) # Need to map extension uids from export to import
    if not extensionMapper:
        config.logging.info('{}No Extensionmapper present. Were there any extensions in the export?{}'.format(config.YELLOW, config.END))
    # globalFields = importGlobalFields(apiKey, token, region, folder, extensionMapper)
    # importContentTypes(apiKey, token, region, folder, extensionMapper, globalFields) # Using global fields to differentiate them from other references
    importLabels(apiKey, token, region, folder)
    roleMapper = importRoles(apiKey, token, region, folder, languageMapper, environmentMapper) # Need to map role uids from export to import
    if not roleMapper:
        config.logging.info('{}No Rolemapper present. Were there any custom roles in the export?{}'.format(config.YELLOW, config.END))
    workflowMapper = importWorkflows(apiKey, token, region, folder, roleMapper) # Need to map workflow uids from export to import
    if not workflowMapper:
        config.logging.info('{}No Workflowmapper present. Were there any workflows in the export?{}'.format(config.YELLOW, config.END))
    mappers = {
        'environments': environmentMapper,
        'workflows': workflowMapper,
        'roles': roleMapper
    }
    importPublishingRules(apiKey, token, region, folder, mappers)
    importWebhooks(apiKey, token, region, folder)
    updateContentTypesAndGlobalFields(apiKey, token, region, folder, extensionMapper)
    endTime = time()
    totalTime = endTime - startTime
    config.logging.info('{}Import finished in {} seconds{}'.format(config.BOLD, totalTime, config.END))
