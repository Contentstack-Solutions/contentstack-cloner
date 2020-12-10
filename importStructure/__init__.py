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
from nested_lookup import nested_lookup
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

def importLanguages(apiKey, authToken, region, folder, masterLocale):
    '''
    Imports languages
    '''
    config.logging.info('{}Importing languages{}'.format(config.BOLD, config.END))
    f = config.dataRootFolder + config.stackRootFolder + folder + config.folderNames['languages']
    for langFile in os.listdir(f):
        language = config.readFromJsonFile(f + langFile)
        if language:
            languageImport = None
            if masterLocale != language['code']:
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
        else:
            config.logging.error('{}Unable to read from Language file {}{}'.format(config.RED, langFile, config.END))
    return True

def importEnvironments(apiKey, authToken, region, folder):
    '''
    Importing environments
    '''
    config.logging.info('{}Importing environments{}'.format(config.BOLD, config.END))
    f = config.dataRootFolder + config.stackRootFolder + folder + config.folderNames['environments']
    mapDict = {}
    for envFile in os.listdir(f):
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
    for delFile in os.listdir(f):
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
    for extFile in os.listdir(f):
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

def importLabels(apiKey, authToken, region, folder):
    '''
    Importing labels
    '''
    config.logging.info('{}Importing labels{}'.format(config.BOLD, config.END))
    f = config.dataRootFolder + config.stackRootFolder + folder + config.folderNames['labels']
    for labFile in os.listdir(f):
        label = config.readFromJsonFile(f + labFile)
        if label:
            labelImport = cma.createLabel(apiKey, authToken, {'label': label}, region)
            if labelImport:
                config.logging.info('Label {} imported'.format(label['name']))
        else:
            config.logging.error('{}Unable to read from Label file {}{}'.format(config.RED, labFile, config.END))
    return True

def importRoles(apiKey, authToken, region, folder):
    '''
    Importing roles
    '''
    config.logging.info('{}Importing roles{}'.format(config.BOLD, config.END))
    f = config.dataRootFolder + config.stackRootFolder + folder + config.folderNames['roles']

    # Getting current roles in import stack - Just to get the uid's of the buit in roles
    currentRoles = cma.getAllRoles(apiKey, authToken, region)
    roleUids = {
        'Developer': None,
        'Content Manager': None
    }
    if currentRoles: # Getting the uids for built-in roles to be able to update them
        for role in currentRoles['roles']:
            if role['name'] == 'Developer':
                roleUids['Developer'] = role['uid']
            elif role['name'] == 'Content Manager':
                roleUids['Content Manager'] = role['uid']

    mapDict = {}
    for roleFile in os.listdir(f):
        role = config.readFromJsonFile(f + roleFile)
        if role:
            if role['name'] in ['Developer', 'Content Manager']: # Built in roles - Maybe they've been updated in the export and we need to alter them in the import stack
                newRules = []
                for rule in role['rules']:
                    newRule = {}
                    for key, value in rule.items():
                        newRule[key] = value
                    if 'acl' not in newRule: # If this is missing from the role, we need to believe they're allowed to do anything, because the update fails otherwise.
                        newRule['acl'] = {
                            "create": True,
                            "read": True,
                            "update": True,
                            "delete": True,
                            "publish": True
                            }
                    role['rules'] = newRules
                roleImport = cma.updateRole(apiKey, authToken, {'role': role}, region, roleUids)
            elif role['name'] == 'Admin':
                # Built in role and not possible to update. We'll pass on this one
                roleImport = None
            else:
                # Custom roles here. We'll create those
                roleImport = cma.createRole(apiKey, authToken, {'role': role}, region)
            if roleImport:
                try:
                    mapDict = addToMapper(mapDict, role['uid'], roleImport['role']['uid'])
                except KeyError:
                    config.logging.debug('Not able to map uid for role {}'.format(role['name']))
                config.logging.info('{} role imported'.format(role['name']))
        else:
            config.logging.error('{}Unable to read from Role file {}{}'.format(config.RED, roleFile, config.END))
    return createMapperFile(apiKey, folder, mapDict, 'roles')

def importWorkflows(apiKey, authToken, region, folder, roleMapper):
    '''
    Importing workflows
    '''
    config.logging.info('{}Importing workflows{}'.format(config.BOLD, config.END))
    f = config.dataRootFolder + config.stackRootFolder + folder + config.folderNames['workflows']
    mapDict = {}
    for wfFile in os.listdir(f):
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
    for pubFile in os.listdir(f):
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
    f = config.dataRootFolder + config.stackRootFolder + folder + config.folderNames['webhooks']
    for whfile in os.listdir(f):
        webhook = config.readFromJsonFile(f + whfile)
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
    for ctFile in os.listdir(ctFolder):
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
    for gfFile in os.listdir(gfFolder):
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
    for ctFile in os.listdir(ctFolder):
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
    for gfFile in os.listdir(gfFolder):
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
    importLanguages(apiKey, token, region, folder, importedStack['masterLocale'])
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
    roleMapper = importRoles(apiKey, token, region, folder) # Need to map role uids from export to import
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
