import sys
from time import sleep
import inquirer
import cma
import config
import exportStructure
import importStructure
import exportContent
import importContent
import login

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
    if action == 'EXPORT' or action == 'IMPORT CONTENT':
        stackList = []
    elif action == 'IMPORT':
        stackList = ['Create a new stack']
    unsortedList = []
    for name, _ in stacks.items():
        unsortedList.append(name)
    stackList = stackList + sorted(unsortedList) + ['Cancel and Exit']
    chooseStack = [
        inquirer.List('chosenStack',
                      message="{}Choose Stack to work on ({}){}".format(config.BOLD, action, config.END),
                      choices=stackList,
                      ),
    ]
    stackName = inquirer.prompt(chooseStack)['chosenStack']
    if stackName == 'Create a new stack':
        config.logging.info('{}New stack to be created for import{}'.format(config.BOLD, config.END))
        stackName, stack = importStructure.createNewStack(authToken, orgUid, region)
        if stackName:
            return stackName, restructureCreatedStack(stack)
        return None, None
    elif stackName == 'Cancel and Exit':
        return None, None
    return stackName, stacks[stackName]

def initiateExportStackStructure(organizations, token, region):
    '''
    Exporting stack structure initation
    '''
    exportedStackName, exportedStack = findStack(organizations, token, region, 'EXPORT') # Choosing the org and stack to export from
    if not exportedStackName:
        return False
    masterLocale = exportedStack['masterLocale']
    config.logging.info('Chosen stack export structure from: {} ({}), with master locale {}'.format(exportedStackName, exportedStack['uid'], masterLocale))
    folder = config.createFolder(exportedStackName)
    config.checkDir(config.dataRootFolder + config.stackRootFolder + folder)

    folder = {
        'name': folder,
        'fullPath': config.dataRootFolder + config.stackRootFolder + folder
    }

    config.logging.info('Stack structure will be exported to ' + folder['fullPath'])
    exportStructure.exportStack(exportedStack['uid'], token, region, folder) # Exporting the stack
    info = {
        'stack': exportedStack,
        'stackName': exportedStackName,
        'apiKey': exportedStack['uid'],
        'folder': folder,
        'masterLocale': masterLocale,
        'region': region,
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
    exportContent.iniateExportContent(stackStructureExportInfo, contentExportInfo, token)
    config.addToExportReport('stackStructureExportInfo', stackStructureExportInfo, stackStructureExportInfo['folder']['fullPath'])
    config.addToExportReport('contentExportInfo', contentExportInfo, stackStructureExportInfo['folder']['fullPath'])

    config.logging.info('Generating Export Report.')
    config.structureReport(stackStructureExportInfo['folder']['fullPath'])
    config.logging.info('Finished Report: {}'.format(stackStructureExportInfo['folder']['fullPath'] + config.exportReportFile))
    return True

def initiateImportStackStructure(organizations, t, r):
    '''
    Initating Stack Structure Import
    '''
    folder = exportStructure.chooseFolder()
    _, importedStack = findStack(organizations, t, r, 'IMPORT') # Choosing the org and stack to import to
    if not importedStack:
        return False
    importStructure.importStack(importedStack, t, r, folder)
    return folder, importedStack

def initiateImportStackContent(token, folder, importedStack, exportReport, region):
    '''
    Initating Stack Content Import
    '''
    folder = exportReport['stackStructureExportInfo']['folder']['fullPath']
    importContent.whatToImport(token, folder, importedStack, exportReport, region)
    return None
    # print(folder)
    # masterLocale = importedStack['masterLocale']
    # apiKey = importedStack['uid']
    # whatToImport = importContent.whatToImport(folder, exportReport)

def whatToExport(organizations, token, region):
    '''
    Listing up export options
    '''
    exportAnswer = None
    while exportAnswer != 'Go Back':
        chooseAction = [
            inquirer.List('chosenAction',
                          message="{}Choose Action to perform{}".format(config.BOLD, config.END),
                          choices=['Export Stack Structure and Content', 'Export Stack Structure', 'Go Back'],
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
                      choices=['Import Stack Structure', 'Import Stack Structure and Content', 'Import Only Content', 'Go Back'],
                      ),
    ]
    importAnswer = inquirer.prompt(chooseAction)['chosenAction']
    if importAnswer == 'Import Stack Structure':
        initiateImportStackStructure(organizations, token, region)
    elif importAnswer == 'Import Stack Structure and Content':
        folder, importedStack = initiateImportStackStructure(organizations, token, region)
        exportReport = importContent.readExportReport(folder)
        initiateImportStackContent(token, folder, importedStack, exportReport, region)
    elif importAnswer == 'Import Only Content':
        folder, exportReport = importContent.findImportContent(organizations, token, region)
        _, importedStack = findStack(organizations, token, region, 'IMPORT CONTENT')
        initiateImportStackContent(token, folder, importedStack, exportReport, region)
    elif importAnswer == 'Go Back':
        return None
    return None

def exitProgram():
    sleep(0.3)
    config.logging.info('Exiting...')
    sleep(0.3)
    sys.exit()

def startupQuestion():
    action = [
        inquirer.List('action',
                      message="{}Choose Action to perform:{}".format(config.BOLD, config.END),
                      choices=['Export', 'Import', 'Exit'],
                      ),
    ]
    answer = inquirer.prompt(action)['action']
    return answer

if __name__ == '__main__':
    '''
    Everything starts here
    '''
    print('''
    {yellow}Export/Import Stack Structure and/or Content.{end}
    {cyan}- Exports a Stack Structure, to the local disk.{end}
    {blue}- Export Entries/Assets, to the local disk.{end}
    {cyan}- Imports a Stack Structure, from the local disk.{end}
    {blue}- Imports Entries/Assets, from the local disk.{end}

    {bold}First! Answer a few questions.{end}
    '''.format(yellow=config.YELLOW, cyan=config.CYAN, blue=config.BLUE, bold=config.BOLD, end=config.END))

    '''
    Login starts
    '''
    region, userInfo, liveUserInfo, token = login.startup()
    config.logging.info('Logged in as: {}'.format(userInfo['username']))
    orgs = restructureOrgs(liveUserInfo) # Making the org output simpler
    '''
    Login finished - Lets ask the user what he/she wants to do
    '''
    config.checkDir(config.dataRootFolder)
    config.checkDir(config.dataRootFolder + config.stackRootFolder)
    startupAction = None
    while startupAction != 'Exit':
        startupAction = startupQuestion()
        if startupAction == 'Export':
            whatToExport(orgs, token, region)
        elif startupAction == 'Import':
            whatToImport(orgs, token, region)
    exitProgram()
