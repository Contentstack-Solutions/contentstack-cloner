'''
oskar.eiriksson@contentstack.com
2020-09-25

Imports stack structure from chosen local folder.

See Readme for details.
'''
import os
from time import sleep
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
    cma.logging.info('Running mapper on {} export'.format(msg))
    for key, value in mapper.items():
        exportString = exportString.replace(key, value)
    importedDict = ast.literal_eval(exportString)
    cma.logging.info('Finished running mapper on {} export'.format(msg))
    return importedDict

def createMapperFile(apiKey, folder, mapDict, mapperName=''):
    '''
    Reusable function that creates the mapper file between exported and imported uids
    '''
    cma.logging.info('Writing {} mapper to file'.format(mapperName))
    mapperFolder = config.localFolder + '/' + config.mapperFolder + '/' + apiKey + '_' + folder
    config.checkDir(config.mapperFolder)
    config.checkDir(config.mapperFolder + '/' + apiKey + '_' + folder)
    config.writeToJsonFile(mapDict, mapperFolder + '/' + config.fileNames[mapperName])
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
    cma.logging.info('{}{} should have been created{}'.format(config.BOLD, stackName, config.END))
    return stackName, stack

def importLanguages(apiKey, authToken, region, folder, masterLocale):
    '''
    Imports languages
    '''
    cma.logging.info('{}Importing languages{}'.format(config.BOLD, config.END))
    f = config.localFolder + '/' + folder + '/' + config.fileNames['languages']
    languages = config.readFromJsonFile(f)
    if languages:
        for locale in languages['locales']:
            body = {
                'locale': {
                    'code': locale['code'],
                    'fallback_locale': locale['fallback_locale'],
                    'name': locale['name']
                }
            }
            languageImport = None
            if masterLocale != locale['code']: # Lets just skip trying to import the master language - it has already been created
                languageImport = cma.createLanguage(apiKey, authToken, body, region)
            if languageImport:
                cma.logging.info('{} imported'.format(locale['code']))
        return True
    cma.logging.error('{}Unable to read from JSON{}'.format(config.YELLOW, config.END))
    return False

def importEnvironments(apiKey, authToken, region, folder):
    '''
    Importing environments
    '''
    cma.logging.info('{}Importing environments{}'.format(config.BOLD, config.END))
    f = config.localFolder + '/' + folder + '/' + config.fileNames['environments']
    environments = config.readFromJsonFile(f)
    if environments:
        mapDict = {}
        for environment in environments['environments']:
            body = {
                'environment': environment
            }
            environmentImport = cma.createEnvironment(apiKey, authToken, body, region)
            if environmentImport:
                cma.logging.info('{} imported'.format(environment['name']))
                mapDict = addToMapper(mapDict, environment['uid'], environmentImport['environment']['uid'])
        return createMapperFile(apiKey, folder, mapDict, 'environments')
    cma.logging.error('{}Unable to read from JSON{}'.format(config.RED, config.END))
    return False

def importGlobalFields(apiKey, authToken, region, folder, extensionsMapper):
    '''
    Importing global fields
    '''
    uidArr = []
    cma.logging.info('{}Importing global fields{}'.format(config.BOLD, config.END))
    f = config.localFolder + '/' + folder + '/' + config.fileNames['globalFields']
    globalFields = config.readFromJsonFile(f)
    if globalFields:
        # Replace the uid of extension from export stack with the uid from the import stack
        globalFields = replaceFromMapper(extensionsMapper, globalFields, 'global fields')
        for globalField in globalFields['global_fields']:
            body = {
                'global_field': globalField
            }
            globalFieldImport = cma.createGlobalField(apiKey, authToken, body, region)
            if globalFieldImport:
                cma.logging.info('{} imported'.format(globalField['title']))
                uidArr.append(globalField['uid'])
        return uidArr
    cma.logging.error('{}Unable to read from JSON{}'.format(config.RED, config.END))
    return uidArr

def importExtensions(apiKey, authToken, region, folder):
    '''
    Importing extensions
    '''
    cma.logging.info('{}Importing extensions{}'.format(config.BOLD, config.END))
    f = config.localFolder + '/' + folder + '/' + config.fileNames['extensions']
    extensions = config.readFromJsonFile(f)
    if extensions:
        mapDict = {}
        for extension in extensions['extensions']:
            body = {
                'extension': extension
            }
            extensionImport = cma.createExtension(apiKey, authToken, body, region)
            if extensionImport:
                cma.logging.info('{} imported'.format(extension['title']))
                mapDict = addToMapper(mapDict, extension['uid'], extensionImport['extension']['uid'])
        return createMapperFile(apiKey, folder, mapDict, 'extensions')
    cma.logging.error('{}Unable to read from JSON{}'.format(config.RED, config.END))
    return False

def importDeliveryTokens(apiKey, authToken, region, folder):
    '''
    Importing delivery tokens
    '''
    cma.logging.info('{}Importing delivery tokens{}'.format(config.BOLD, config.END))
    f = config.localFolder + '/' + folder + '/' + config.fileNames['deliveryTokens']
    deliveryTokens = config.readFromJsonFile(f)
    if deliveryTokens:
        # Replace the uid of extension from export stack with the uid from the import stack
        # deliveryTokens = replaceFromMapper(environmentsMapper, deliveryTokens, 'delivery tokens')
        for deliveryToken in deliveryTokens['tokens']:
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
                cma.logging.info('{} imported'.format(deliveryToken['name']))
        return True
    cma.logging.error('{}Unable to read from JSON{}'.format(config.RED, config.END))
    return False


def findReferencedContentTypes(ctUid, contentType, importedContentTypes, globalFields):
    '''
    Finding out whether the content type has a reference to another
    content type that has not been imported yet.
    If we find a reference to a content type that has still not been
    imported, we queue it up and try to import the next one.
    Then visit the queued up content types after importing everything possible.
    '''
    allRefs = nested_lookup(key='reference_to', document=contentType, wild=True) # finding all reference_to fields, where we see the referenced content type
    newRefsList = []
    for ref in allRefs: # find all empty strings and lists within the list
        if (isinstance(ref, str)) and (len(ref) > 0) and (ref != ctUid) and (ref not in globalFields):
            newRefsList.append(ref)
        elif isinstance(ref, list):
            for i in ref:
                if (len(i) > 0) and (i != ctUid) and (i not in globalFields):
                    newRefsList.append(i)
    newRefsList = list(set(newRefsList)) # remove duplicates
    cma.logging.debug('Content Type: ', ctUid)
    cma.logging.debug('References: ', newRefsList)
    cma.logging.debug('Already Imported: ', importedContentTypes)
    for i in newRefsList:
        if i not in importedContentTypes: # We have a reference to a content type that has not been imported yet
            cma.logging.warning('{}Not possible to import {} at this time because one ore more referenced content types have not been imported yet (All referenced content types: {}). Adding to queue.{}'.format(config.YELLOW, ctUid, newRefsList, config.END))
            return False
    return True # All references already imported

def performContentTypeImport(apiKey, authToken, body, region):
    contentTypeImport = cma.createContentType(apiKey, authToken, body, region)
    if contentTypeImport:
        cma.logging.info('{} imported'.format(body['content_type']['uid']))
        return True
    cma.logging.warning('{}Unable to import {}. Moving to back of queue and trying again later.{}'.format(config.YELLOW, body['content_type']['uid'], config.END))
    return False

def getNamesInQueue(contentTypeQueue):
    '''
    A simple function used a few times over.
    Getting only the uids of content types from the whole payload
    '''
    queueNames = []
    for i in contentTypeQueue:
        queueNames.append(i['uid'])
    return queueNames

def importContentTypes(apiKey, authToken, region, folder, extensionsMapper, globalFields):
    '''
    Importing content types
    '''
    cma.logging.info('{}Importing content types{}'.format(config.BOLD, config.END))
    f = config.localFolder + '/' + folder + '/' + config.fileNames['contentTypes']
    contentTypes = config.readFromJsonFile(f)
    importedContentTypes = []
    contentTypeQueue = []
    if contentTypes:
        contentTypes = replaceFromMapper(extensionsMapper, contentTypes, 'content types') # extension uids from old and new stack mapped
        for contentType in contentTypes['content_types']:
            continueImport = findReferencedContentTypes(contentType['uid'], contentType['schema'], importedContentTypes, globalFields)
            if continueImport: # OK to continue with import of this content type
                '''
                Lets import it!
                '''
                importAction = performContentTypeImport(apiKey, authToken, {'content_type': contentType}, region)
                if importAction:
                    importedContentTypes.append(contentType['uid']) # Add it to this list after import finishes
                else:
                    contentTypeQueue.append(contentType)
            else: # Not OK to continue with import of this content type
                contentTypeQueue.append(contentType)

    maxTries = int(1.5 * len(contentTypeQueue))# We have to give up on some point - Length of array + 150% of the length of the queue should do it.
    tryNumber = 1
    if contentTypeQueue:
        queueNames = getNamesInQueue(contentTypeQueue)
        cma.logging.info('Trying to import from the content type queue since earlier ({}). Maximum tries: {}'.format(queueNames, maxTries))
    while contentTypeQueue and tryNumber <= maxTries:
        '''
        Lets now attack the unfinshed content types
        '''
        cma.logging.info('Try: {}/{}. Content Type: {}'.format(tryNumber, maxTries, contentTypeQueue[0]['uid']))
        body = {'content_type': contentTypeQueue[0]}
        continueImport = findReferencedContentTypes(contentTypeQueue[0]['uid'], contentTypeQueue[0]['schema'], importedContentTypes, globalFields)
        importAction = None
        if continueImport:
            importAction = performContentTypeImport(apiKey, authToken, body, region)
        if not importAction:
            contentTypeQueue.append(contentTypeQueue[0])
        else:
            importedContentTypes.append(contentTypeQueue[0]['uid'])
        contentTypeQueue.pop(0)
        tryNumber += 1
    if (tryNumber > maxTries) and contentTypeQueue:
        queueNames = getNamesInQueue(contentTypeQueue)
        cma.logging.error('{}Not able to import all content types. Possibly a circular dependency in the references?{}'.format(config.RED, config.END))
        cma.logging.error('{}Content Types not imported: {}{}'.format(config.RED, queueNames, config.END))
    return True

def importLabels(apiKey, authToken, region, folder):
    '''
    Importing labels
    '''
    cma.logging.info('{}Importing labels{}'.format(config.BOLD, config.END))
    f = config.localFolder + '/' + folder + '/' + config.fileNames['labels']
    labels = config.readFromJsonFile(f)
    if labels:
        for label in labels['labels']:
            labelImport = cma.createLabel(apiKey, authToken, {'label': label}, region)
            if labelImport:
                cma.logging.info('{} imported'.format(label['name']))
        return True
    cma.logging.error('{}Unable to read from Label JSON{}'.format(config.RED, config.END))
    return False

def importRoles(apiKey, authToken, region, folder):
    '''
    Importing roles
    '''
    cma.logging.info('{}Importing roles{}'.format(config.BOLD, config.END))
    f = config.localFolder + '/' + folder + '/' + config.fileNames['roles']
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
    roles = config.readFromJsonFile(f)
    if roles:
        mapDict = {}
        for role in roles['roles']:
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
                    cma.logging.debug('Not able to map uid for role {}'.format(role['name']))
                cma.logging.info('{} role imported'.format(role['name']))
        return createMapperFile(apiKey, folder, mapDict, 'roles')
    cma.logging.error('{}Unable to read from Role JSON{}'.format(config.RED, config.END))
    return False

def importWorkflows(apiKey, token, region, folder, roleMapper):
    '''
    Importing workflows
    '''
    cma.logging.info('{}Importing workflows{}'.format(config.BOLD, config.END))
    f = config.localFolder + '/' + folder + '/' + config.fileNames['workflows']
    workflows = config.readFromJsonFile(f)
    if workflows:
        mapDict = {}
        workflows = replaceFromMapper(roleMapper, workflows, 'workflows') # role uids from old and new stack mapped
        for workflow in workflows['workflows']:
            workflowImport = cma.createWorkflow(apiKey, token, {'workflow': workflow}, region)
            if workflowImport:
                mapDict = addToMapper(mapDict, workflow['uid'], workflowImport['workflow']['uid'])
                cma.logging.info('{} imported'.format(workflow['name']))
        return createMapperFile(apiKey, folder, mapDict, 'workflows')
    cma.logging.error('{}Unable to read from Workflow JSON{}'.format(config.RED, config.END))
    return False

def importPublishingRules(apiKey, token, region, folder, mappers):
    '''
    Importing publishing rules
    '''
    cma.logging.info('{}Importing publishing rules{}'.format(config.BOLD, config.END))
    f = config.localFolder + '/' + folder + '/' + config.fileNames['publishingRules']
    publishingRules = config.readFromJsonFile(f)
    if publishingRules:
        for key, value in mappers.items():
            publishingRules = replaceFromMapper(value, publishingRules, key)
        # publishingRules = replaceFromMapper(roleMapper, publishingRules, 'roles') # role uids from old and new stack mapped
        # publishingRules = replaceFromMapper(workflowMapper, publishingRules, 'workflows') # workflow uids from old and new stack mapped
        count = 1
        for publishingRule in publishingRules['publishing_rules']:
            publishingRuleImport = cma.createPublishingRule(apiKey, token, {'publishing_rule': publishingRule}, region)
            if publishingRuleImport:
                cma.logging.info('Publishing rule {} imported'.format(count)) # No names on publishing rules - we just use the count then to inform.
            count += 1
        return True
    cma.logging.error('{}Unable to read from Publishing Rule JSON{}'.format(config.RED, config.END))
    return False
