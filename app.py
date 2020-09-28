import os
import re
from time import sleep, time
import inquirer
import cma
import config
import exportStructure
import importStructure
import exportContent

def executeLogin(loginInfo, maxTries, count=1):
    '''
    Executes the login versus Contentstack with the login information fetches in the initiateLogin function
    '''
    loginInfo['region'] = cma.regionMap[loginInfo['region']]
    while count < maxTries: # Maximum Attempts
        statusCode, loginAttempt = cma.login(loginInfo['username'], loginInfo['password'], loginInfo['region'])
        if statusCode == 200:
            return loginAttempt, loginInfo['region']
        elif 'error_message' in loginAttempt:
            cma.logging.error(str(config.RED) + str(loginAttempt['error_message']) + str(config.END))
        else:
            cma.logging.error(str(config.RED) + str(loginAttempt) + str(config.END))
        count += 1
    cma.logging.error('{}Login failed{}'.format(config.RED, config.END))
    return None, None

def initiateLogin():
    '''
    Initiates the Login - That is, it gets the relevant information before executing the login.
    Allows the usage of saving authentication information on local disk.
    '''
    maxTries = 2
    if os.path.isfile(config.exportLoginFile):
        use = [inquirer.Confirm('useFile', message="{}Login File found on local storage. Try to use that?{}".format(config.BOLD, config.END), default=True)]
        if inquirer.prompt(use)['useFile']:
            loginInfo = config.readFromJsonFile(config.exportLoginFile)
            return executeLogin(loginInfo, maxTries)
        delete = [inquirer.Confirm('deleteFile', message="{}Should we delete the Login File?{}".format(config.BOLD, config.END), default=True)]
        if inquirer.prompt(delete)['deleteFile']:
            os.remove(config.exportLoginFile)

    loginList = [
        inquirer.List('region', message="{}Choose Contentstack region{}".format(config.BOLD, config.END), choices=['US', 'EU']),
        inquirer.Text('username', message="{}Type in your username (email address){}".format(config.BOLD, config.END), validate=lambda _, x: re.match('[^@]+@[^@]+\.[^@]+', x)),
        inquirer.Password('password', message="{}Type in your password{}".format(config.BOLD, config.END)),
        inquirer.Confirm('store', message='{}Do you want to store this authentication information?{}'.format(config.BOLD, config.END), default=True)
    ]
    loginInfo = inquirer.prompt(loginList)
    try:
        if loginInfo['store']:
            config.writeToJsonFile(loginInfo, config.exportLoginFile)
    except:
        pass
    return executeLogin(loginInfo, maxTries)

def restructureOrgs(auth):
    '''
    Restructuring the org payload to something easier
    '''
    orgDict = {}
    for org in auth['user']['organizations']:
        if org['enabled']: # No point in adding disabled orgs to this variable
            orgDict[org['name']] = {
                'uid': org['uid'],
            }
            if 'is_owner' in org:
                orgDict[org['name']]['isOwner'] = True
            else:
                orgDict[org['name']]['isOwner'] = False
    return orgDict

def restructureExportStacks(stacks):
    stackDict = {}
    for stack in stacks['stacks']:
        stackDict[stack['name']] = {
            'org': stack['org_uid'],
            'uid': stack['api_key'],
            'masterLocale': stack['master_locale']
        }
    return stackDict

def restructureCreatedStack(stack):
    stackDict = {
        'org': stack['stack']['org_uid'],
        'uid': stack['stack']['api_key'],
        'masterLocale': stack['stack']['master_locale']
    }
    return stackDict

def findStack(orgs, authToken, region, action='EXPORT'):
    '''
    Choosing the org and finding the stack to either export from or import to
    '''
    orgList = []
    for name, value in orgs.items():
        if value['isOwner']:
            name = name + ' (You are the owner)'
        orgList.append(name)
    orgList.append('Cancel and Exit')

    chooseOrg = [
        inquirer.List('chosenOrg',
                      message="{}Choose Organization to work on ({}){}".format(config.BOLD, action, config.END),
                      choices=orgList,
                      ),
    ]
    orgName = inquirer.prompt(chooseOrg)['chosenOrg'].replace(' (You are the owner)', '')
    if orgName == 'Cancel and Exit':
        return None, None
    orgUid = orgs[orgName]['uid']
    stacks = cma.getAllStacks(cma.constructAuthTokenHeader(authToken), orgUid, region)
    stacks = restructureExportStacks(stacks)
    if action == 'EXPORT':
        stackList = []
    elif action == 'IMPORT':
        stackList = ['Create a new stack']
    for name, _ in stacks.items():
        stackList.append(name)
    stackList.append('Cancel and Exit')
    chooseStack = [
        inquirer.List('chosenStack',
                      message="{}Choose Stack to work on ({}){}".format(config.BOLD, action, config.END),
                      choices=stackList,
                      ),
    ]
    stackName = inquirer.prompt(chooseStack)['chosenStack']
    if stackName == 'Create a new stack':
        cma.logging.info('{}New stack to be created for import{}'.format(config.BOLD, config.END))
        stackName, stack = importStructure.createNewStack(authToken, orgUid, region)
        return stackName, restructureCreatedStack(stack)
    elif stackName == 'Cancel and Exit':
        return None, None
    return stackName, stacks[stackName]

def exportStack(apiKey, token, region, folder):
    '''
    Export stack function
    '''
    cma.logging.info('{}Starting structure export{}'.format(config.BOLD, config.END))
    startTime = time()
    exportStructure.exportContentTypes(apiKey, token, region, folder)
    exportStructure.exportGlobalFields(apiKey, token, region, folder)
    exportStructure.exportExtensions(apiKey, token, region, folder)
    exportStructure.exportWorkflows(apiKey, token, region, folder)
    contentTypeUids = exportStructure.getContentTypeUids(folder) # Need to get all content types to fetch publishing rules
    exportStructure.exportPublishingRules(contentTypeUids, apiKey, token, region, folder)
    exportStructure.exportEnvironments(apiKey, token, region, folder)
    exportStructure.exportDeliveryTokens(apiKey, token, region, folder)
    exportStructure.exportRoles(apiKey, token, region, folder)
    exportStructure.exportWebhooks(apiKey, token, region, folder)
    exportStructure.exportLabels(apiKey, token, region, folder)
    exportStructure.exportLanguages(apiKey, token, region, folder)
    endTime = time()
    totalTime = endTime - startTime
    cma.logging.info('{}Export finished in {} seconds{}'.format(config.BOLD, totalTime, config.END))

def initiateExportStackStructure(organizations, token, region):
    '''
    Exporting stack structure initation
    '''
    exportedStackName, exportedStack = findStack(organizations, token, region, 'EXPORT') # Choosing the org and stack to export from
    if not exportedStackName:
        return False
    masterLocale = exportedStack['masterLocale']
    cma.logging.info('Chosen stack export structure from: {} ({}), with master locale {}'.format(exportedStackName, exportedStack['uid'], masterLocale))
    folder = config.createFolder(exportedStackName)
    config.checkDir(folder)

    cma.logging.info('Stack structure will be exported to ' + config.localFolder + '/' + folder)
    exportStack(exportedStack['uid'], token, region, folder) # Exporting the stack
    info = {
        'stack': exportedStack,
        'stackName': exportedStackName,
        'apiKey': exportedStack['uid'],
        'folder': folder,
        'masterLocale': masterLocale,
        'region': region
    }
    return info

def initiateExportAll(organizations, token, region):
    '''
    Export All initation
    '''
    stackStructureExportInfo = initiateExportStackStructure(organizations, token, region) # Begin stack structure export
    if not stackStructureExportInfo:
        return None
    contentExportInfo = exportContent.whatContentToExport(stackStructureExportInfo) # Choose what entries and assets to export
    if not contentExportInfo:
        return None
    entries = exportContent.iniateExportEntries(stackStructureExportInfo, contentExportInfo, token)

def importStack(importedStack, token, region, folder):
    '''
    Import stack function
    '''
    apiKey = importedStack['uid']
    cma.logging.info('{}Starting structure import{}'.format(config.BOLD, config.END))
    startTime = time()
    importStructure.importLanguages(apiKey, token, region, folder, importedStack['masterLocale'])
    environmentMapper = importStructure.importEnvironments(apiKey, token, region, folder)
    if not environmentMapper:
        cma.logging.error('{}Missing the Environmentmapper{}'.format(config.RED, config.END))
    importStructure.importDeliveryTokens(apiKey, token, region, folder)
    extensionMapper = importStructure.importExtensions(apiKey, token, region, folder) # Need to map extension uids from export to import
    if not extensionMapper:
        cma.logging.error('{}Missing the Extensionmapper{}'.format(config.RED, config.END))
    globalFields = importStructure.importGlobalFields(apiKey, token, region, folder, extensionMapper)
    importStructure.importContentTypes(apiKey, token, region, folder, extensionMapper, globalFields) # Using global fields to differentiate them from other references
    importStructure.importLabels(apiKey, token, region, folder)
    roleMapper = importStructure.importRoles(apiKey, token, region, folder) # Need to map role uids from export to import
    if not roleMapper:
        cma.logging.error('{}Missing the Rolemapper{}'.format(config.RED, config.END))
    workflowMapper = importStructure.importWorkflows(apiKey, token, region, folder, roleMapper) # Need to map workflow uids from export to import
    if not workflowMapper:
        cma.logging.error('{}Missing the Workflowmapper{}'.format(config.RED, config.END))
    mappers = {
        'environments': environmentMapper,
        'workflows': workflowMapper,
        'roles': roleMapper
    }
    importStructure.importPublishingRules(apiKey, token, region, folder, mappers)
    # importStructure.importWebhooks(apiKey, token, region, folder)
    endTime = time()
    totalTime = endTime - startTime
    cma.logging.info('{}Import finished in {} seconds{}'.format(config.BOLD, totalTime, config.END))

def initiateImportStackStructure(orgs, t, r):
    folder = config.chooseFolder(config.mapperFolder)
    _, importedStack = findStack(orgs, t, r, 'IMPORT') # Choosing the org and stack to export from
    if not importedStack:
        return False
    importStack(importedStack, t, r, folder)
    return True

def whatToExport(organizations, token, region):
    '''
    Listing up export options
    '''
    exportAnswer = None
    while exportAnswer != 'Exit':
        chooseAction = [
            inquirer.List('chosenAction',
                          message="{}Choose Action to perform:{}".format(config.BOLD, config.END),
                          choices=['Export Stack Structure and Content', 'Export Stack Structure', 'Exit'],
                          ),
        ]
        exportAnswer = inquirer.prompt(chooseAction)['chosenAction']
        if exportAnswer == 'Export Stack Structure and Content':
            initiateExportAll(organizations, token, region)
        elif exportAnswer == 'Export Stack Structure':
            initiateExportStackStructure(organizations, token, region)
    return None

def whatToImport(organizations, token, region):
    '''
    Listing up import options
    '''
    chooseAction = [
        inquirer.List('chosenAction',
                      message="{}Choose Action to perform:{}".format(config.BOLD, config.END),
                      choices=['Import Stack Structure', 'Exit'],
                      ),
    ]
    importAnswer = inquirer.prompt(chooseAction)['chosenAction']
    if importAnswer == 'Export Stack Structure':
        initiateExportStackStructure(organizations, token, region)
    elif importAnswer == 'Import Stack Structure':
        initiateImportStackStructure(organizations, token, region)
    elif importAnswer == 'Go Back':
        return None
    return None

if __name__ == '__main__':
    '''
    Everything starts here
    '''
    print('''
    {bold}Export/Import Stack Structure and/or Content.{boldEnd}
    - Exports a Stack Structure, to the local disk.
    - Export Entries/Assets, to the local disk.
    - Imports a Stack Structure, from the local disk.
    - Imports Entries/Assets, from the local disk.

    {bold}First! Answer a few questions.{boldEnd}
    '''.format(bold=config.BOLD, boldEnd=config.END))
    authentication = initiateLogin() # Logging in
    region = authentication[1]  # Just the URL - either the US or EU endpoint
    userInfo = authentication[0] # Response from CS after logging in
    token = userInfo['user']['authtoken'] # AuthToken

    cma.logging.info('Logged in as: {}'.format(userInfo['user']['email']))
    organizations = restructureOrgs(userInfo) # Making the org output simpler
    '''
    Login finished - Lets ask the user what he/she wants to do
    '''
    importExportAnswer = None
    while importExportAnswer != 'Exit':
        importExportAction = [
            inquirer.List('importExportAction',
                          message="{}Choose Action to perform:{}".format(config.BOLD, config.END),
                          choices=['Export', 'Import', 'Exit'],
                          ),
        ]
        importExportAnswer = inquirer.prompt(importExportAction)['importExportAction']
        if importExportAnswer == 'Export':
            whatToExport(organizations, token, region)
        elif importExportAnswer == 'Import':
            whatToImport(organizations, token, region)
    sleep(0.3)
    cma.logging.info('Exiting...')
    sleep(0.3)
