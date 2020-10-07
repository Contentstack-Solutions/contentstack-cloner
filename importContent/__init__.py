'''
oskar.eiriksson@contentstack.com
2020-10-02

Imports stack content from chosen local folder.
'''
import os
from time import sleep
import re
import ast
from benedict import benedict
import inquirer
import cma
import config
import exportStructure
import importStructure

def readExportReport(folder):
    '''
    Reading the export report before importing content
    '''
    folder = config.dataRootFolder + config.stackRootFolder + folder
    exportReport = folder + config.exportReportFile
    if not os.path.isfile(exportReport):
        config.logging.error('{}Unable to read Export Report ({}) Not possible to Import Content from this Export Folder.{}'.format(config.RED, exportReport, config.END))
        return None
    exportReport = config.readFromJsonFile(exportReport)
    return exportReport

def findImportContent(organizations, token, region):
    '''
    When only importing content - finding the folder and information about stack
    Folder is easy.
    Information on stack should look something like this: {'org': 'blte1b70a5425251ffd', 'uid': 'blt8814602fd91ed842', 'masterLocale': 'en-us'}
    '''
    folder = exportStructure.chooseFolder()

    exportReport = readExportReport(folder)
    if not exportReport:
        config.logging.critical('{}Unable to Read Export Report. Canceling import. ({}){}'.format(config.RED, folder, config.END))
        return folder, None
    return folder, exportReport

def defineContentTypesToImport(contentTypes):
    '''
    Choose content types to export.
    '''
    chooseAllContentTypesOrNot = [
        inquirer.List('chooseAllContentTypesOrNot',
                      message="{}Do you want to Entries of Content Types of handpick some Content Types:{}".format(config.BOLD, config.END),
                      choices=['All Content Types', 'Choose Content Type(s) to Import', 'Cancel and Exit'],
                      ),
    ]
    allOrNothing = inquirer.prompt(chooseAllContentTypesOrNot)['chooseAllContentTypesOrNot']
    if allOrNothing == 'All Content Types':
        return contentTypes
    if allOrNothing == 'Cancel and Exit':
        return None
    pickedContentTypes = []
    while not pickedContentTypes:
        pickContentTypes = [
            inquirer.Checkbox('pickContentTypes',
                              message="Pick Content Types With Space Bar and Press Return when Finished.",
                              choices=contentTypes,
                              ),
        ]
        pickedContentTypes = inquirer.prompt(pickContentTypes)['pickContentTypes']
        if not pickedContentTypes:
            config.logging.warning('{}You must pick one content types or more{}'.format(config.YELLOW, config.END))
    return pickedContentTypes

def defineLanguagesToImport(languages):
    '''
    Decide of what entry languages to import
    '''
    chooseAllLanguagesOrNot = [
        inquirer.List('chooseAllLanguagesOrNot',
                      message="{}Do you want to Entries of Content Types of handpick some Content Types:{}".format(config.BOLD, config.END),
                      choices=['All Languages', 'Choose Language(s) to Import', 'Cancel and Exit'],
                      ),
    ]
    allOrNothing = inquirer.prompt(chooseAllLanguagesOrNot)['chooseAllLanguagesOrNot']
    if allOrNothing == 'All Languages':
        return languages
    if allOrNothing == 'Cancel and Exit':
        return None
    pickedLanguages = []
    while not pickedLanguages:
        pickLanguages = [
            inquirer.Checkbox('pickLanguages',
                              message="Pick Language With Space Bar and Press Return when Finished.",
                              choices=languages,
                              ),
        ]
        pickedLanguages = inquirer.prompt(pickLanguages)['pickLanguages']
        if not pickedLanguages:
            config.logging.warning('{}You must pick one language or more{}'.format(config.YELLOW, config.END))
    return pickedLanguages

def defineAssetsToImport(assetEnvironments, localAssets, assetNumbers):
    '''
    Deciding to import Assets or Not
    '''
    if not assetNumbers:
        config.logging.info('No Assets Available in the Export')
        '''
        We could just attempt to fetch everything here... but that's actually just the export content module again...
        '''
        return None

    if assetEnvironments != 'all':
        config.logging.info('Assets available from Environment: {}'.format(assetEnvironments))
    if not localAssets:
        config.logging.info('Assets not locally available in Export. We can try to download them from the originally Export Stack')
    else:
        config.logging.info('Asset files Available in the Export.')


def prettyPrintNumbers(numbers, indent=0):
    '''
    For logging purposes. Pretty-Printing out Export Numbers
    '''
    for contentType, value in numbers.items():
        print(config.GREEN + '\t' + contentType + config.END)
        for lang, num in value.items():
            print('\t\t' + lang + ': ' + str(num))

def printOutReport(exportReport):
    '''
    Before Importing - Telling the User what's there
    '''
    if 'includeWorkFlows' not in exportReport:
        exportReport['includeWorkFlows'] = True
    workflowsIncluded = exportReport['includeWorkFlows']
    if not workflowsIncluded:
        workflows = 'NOT'
    else:
        workflows = ''
    # if 'AssetExportMethod' in exportReport:
    #     assetExportMethod = exportReport['AssetExportMethod']
    # else:
    #     assetExportMethod = None
    masterLocale = exportReport['stackStructureExportInfo']['stack']['masterLocale']
    contentExportInfo = exportReport['contentExportInfo']
    '''
    exportReport looks something like this:
    {'includeWorkFlows': False, 'useDeliveryToken': True, 'stackStructureExportInfo': {'stack': {'org': 'blte1b70a5425251ffd', 'uid': 'blt9727d0a43a2fa0dd', 'masterLocale': 'en-us'}, 'stackName': 'Test', 'apiKey': 'blt9727d0a43a2fa0dd', 'folder': {'name': 'Test - 2020-10-05 00:40:25.511500/', 'fullPath': 'data/stacks/Test - 2020-10-05 00:40:25.511500/'}, 'masterLocale': 'en-us', 'region': 'https://eu-api.contentstack.com/'}, 'contentExportInfo': {'environments': 'development', 'assets': None, 'downloadAssets': False, 'languages': ['is-is', 'en-us', 'en-si'], 'contentTypes': ['quill', 'landing_page', 'multilingual']}, 'Numbers': {'Number of contentTypes Exported': 32, 'Number of deliveryTokens Exported': 1, 'Number of environments Exported': 3, 'Number of extensions Exported': 20, 'Number of globalFields Exported': 3, 'Number of labels Exported': 6, 'Number of languages Exported': 11, 'Number of publishingRules Exported': 2, 'Number of roles Exported': 5, 'Number of webhooks Exported': 5, 'Number of workflows Exported': 1, 'Number of Assets Exported': None, 'Number of Asset Folders Exported': None, 'Number of Content types with Exported Entries': 3, 'Number of Entries Per Content Type and Language': {'multilingual': {'is-is': 1, 'en-us': 1}, 'landing_page': {'is-is': 10, 'en-us': 12}, 'quill': {'en-us': 1}}}}
    '''
    entriesEnvironments = contentExportInfo['environments']
    assetEnvironments = contentExportInfo['assets']
    localAssets = contentExportInfo['downloadAssets']
    languages = contentExportInfo['languages']
    contentTypes = contentExportInfo['contentTypes'] # Entries Exported of these contentTypes
    entryNumbers = exportReport['Numbers']['Number of Entries Per Content Type and Language']
    assetNumbers = exportReport['Numbers']['Number of Assets Exported']


    config.logging.info('{}Publishing Environments available in Entries: {}{}{}{}'.format(config.GREEN, config.WHITE, config.UNDERLINE, entriesEnvironments, config.END))
    config.logging.info('{}Publishing Environments available in Assets: {}{}{}{}'.format(config.GREEN, config.WHITE, config.UNDERLINE, assetEnvironments, config.END))
    config.logging.info('{}Workflow Stages are {} included with this Export{}'.format(config.GREEN, workflows, config.END))
    config.logging.info('{}Asset Files included in Export: {}{}{}{}'.format(config.GREEN, config.WHITE, config.UNDERLINE, localAssets, config.END))
    config.logging.info('{}Number of Assets (Maybe only metadata): {}{}{}{}'.format(config.GREEN, config.WHITE, config.UNDERLINE, assetNumbers, config.END))
    config.logging.info('{}Master Locale of Export: {}{}{}{}'.format(config.GREEN, config.WHITE, config.UNDERLINE, masterLocale, config.END))
    config.logging.info('{}Entries Numbers by Content Type and Language:{}'.format(config.GREEN, config.END))
    prettyPrintNumbers(entryNumbers)
    return assetEnvironments, localAssets, assetNumbers, contentTypes, languages

def importAllOrSomething():
    '''
    All or something
    '''
    chooseAllImportsOrSomething = [
        inquirer.List('chooseAllImportsOrSomething',
                      message="{}Do you want to Import Everything or Handpick some things?{}".format(config.BOLD, config.END),
                      choices=['Import Everything', 'Handpick by Content Types and/or Languages', 'Cancel'],
                      ),
    ]
    allOrSomething = inquirer.prompt(chooseAllImportsOrSomething)['chooseAllImportsOrSomething']
    if allOrSomething == 'Import Everything':
        return 'ALL'
    if 'Handpick' in allOrSomething:
        return 'HANDPICK'
    return None

def importAnAsset(region, authToken, apiKey, metaData, assetFile, folderMapper): #(region, apiKey, publishDetails, metaData, assetFile)
    '''
    Create Asset in Import Stack
    region is full URL
    publishDetails, metaData and assetFile are just the fullpath to the json file OR None
    folderMapper is a dict object
    '''
    tmpFolder = '.tmp/'
    if metaData:
        metaData = config.readFromJsonFile(metaData)
    if folderMapper and metaData:
        metaData = importStructure.replaceFromMapper(folderMapper, metaData, 'assets')
    if not assetFile:
        config.checkDir(tmpFolder)
        assetFile = config.downloadFileToDisk(metaData['asset']['url'], tmpFolder, metaData['asset']['filename'])
        if assetFile:
            assetFile = tmpFolder + metaData['asset']['filename']
    config.logging.debug('Region {}'.format(region))
    config.logging.debug('authToken {}'.format(authToken))
    config.logging.debug('apiKey {}'.format(apiKey))
    config.logging.debug('assetFile {}'.format(assetFile))
    config.logging.debug('metaData {}'.format(metaData))
    config.logging.debug('Filename {}'.format(metaData['asset']['filename']))
    create = cma.createAsset(region, authToken, apiKey, assetFile, metaData, metaData['asset']['filename'])
    if create and (tmpFolder in assetFile): # Cleaning from tmp folder
        os.remove(assetFile)
    return create

def importFolders(folder, apiKey, token, region):
    '''
    Creating folders
    '''
    folderFile = folder + config.folderNames['assets'] + 'folders.json'
    if os.path.isfile(folderFile):
        mapDict = {}
        folderData = config.readFromJsonFile(folderFile)
        config.logging.info('Found Folders in Export')
        folderExport = folderData['assets']
        maxTries = len(folderExport) * 2
        tryNo = 0
        while folderExport and tryNo <= maxTries:
            tryNo += 1
            if tryNo == maxTries:
                config.logging.warning('{}Last possible try importing folders! (Try number: {}){}'.format(config.YELLOW, tryNo, config.END))
            if 'parent_uid' in folderExport[0]:
                parentUid = folderExport[0]['parent_uid']
            else:
                parentUid = None
            if parentUid:
                if parentUid not in mapDict:
                    folderExport.append(folderExport[0])
                    folderExport.pop(0)
                    continue
            importedFolder = cma.createFolder(apiKey, token, region, folderExport[0]['name'])
            if importedFolder:
                config.logging.info('Folder Imported: {}'.format(importedFolder['asset']['name']))
                mapDict = importStructure.addToMapper(mapDict, folderExport[0]['uid'], importedFolder['asset']['uid'])
                folderExport.pop(0)
                continue
            folderExport.append(folderExport[0])
            folderExport.pop(0)
        return importStructure.createMapperFile(apiKey, folder.split('/')[-2], mapDict, 'folders')
    config.logging.info('No Folders Found in Export')
    return None

def findAssetFiles(assetFolder):
    exportUid = assetFolder.split('/')[-2]
    publishDetails = None
    metaData = None
    assetFile = None
    for f in os.listdir(assetFolder):
        if f == 'publishDetails.json':
            config.logging.info('Found Publishing Information for Asset')
            publishDetails = assetFolder + f
        elif f.startswith(exportUid):
            config.logging.info('Found Asset Metadata: {}'.format(f))
            metaData = assetFolder + f
        else:
            config.logging.info('Found Asset File: {}'.format(f))
            assetFile = assetFolder + f
    return publishDetails, assetFile, metaData

def importAssets(token, importedStack, folder, exportReport, localAssets, region):
    '''
    Importing Assets
    '''
    apiKey = importedStack['uid']
    config.logging.info('Importing All Assets')
    if not localAssets:
        config.logging.info('Assets not present locally - we will need to fetch them from the export stack.')
    '''
    Importing Folders
    buggy! fix it!
    '''
    folderMapper = importFolders(folder, apiKey, token, region)
    '''
    Importing Assets
    '''
    mapDict = {}
    for assetFolder in os.listdir(folder + config.folderNames['assets']): # Finding all asset folders
        assetFolder = folder + config.folderNames['assets'] + assetFolder + '/'
        if os.path.isdir(assetFolder): # Finding all folders in the asset folder (we also potentially have folders.json there)
            publishDetails, assetFile, metaData = findAssetFiles(assetFolder)
            if metaData:
                importedAsset = importAnAsset(region, token, apiKey, metaData, assetFile, folderMapper)
                if importedAsset:
                    importStructure.addToMapper(mapDict, metaData.split('/')[-2], importedAsset['asset']['uid'])
    print(folder)
    print(folder.split('/')[-2])
    return importStructure.createMapperFile(apiKey, folder.split('/')[-2], mapDict, 'assets')

# def replaceAssetFromMapper(mapper, exportedJson, msg=''):
#     '''
#     Finding all references of old asset IDs - Removing it from the entry (the whole nested dict) and replacing with the new uid, and only that uid
#     This is 1000% not the best way to do this...
#     I got stuck trying to search the dict iteratively and replacing a whole nested value that could both be a nested dict and a list with dicts
#     '''
#     if exportedJson['uid'] == 'bltbdc83dc124ef0168':
#         print('WHERE ARE GONNA FAIL HERE FOR SOME FXXXX REASON')
#     exportString = str(exportedJson)
#     config.logging.info('Running mapper on {} export'.format(msg))
#     for key, value in mapper.items():
#         searchString = r"{'uid': '" + key + "',.*?}.*?\].*?}"#.format(value) # using regex to replace the things
#         newString = re.sub(searchString, "'{}'".format(value), exportString)
#     importedDict = ast.literal_eval(newString) # Converting the string back to a dictionary
#     config.logging.info('Finished running mapper on {} export'.format(msg))
#     return importedDict

def replaceStrInDict(d, search, value):
    string = str(search)
    dString = str(d)
    dString = dString.replace(string, "'" + value + "'")
    return ast.literal_eval(dString) # Converting the string back to a dictionary

def replaceAssetFromMapper(d, mapper, msg=''):
    '''
    Using benedict to replace old asset uids with new
    '''
    config.logging.info('Running Asset Mapper on {} export'.format(msg))
    bDict = benedict(d)
    keys = bDict.keypaths(indexes=True)
    for key, value in mapper.items():
        search = bDict.search(key, in_keys=False, in_values=True, exact=True, case_sensitive=True)
        while search:
            for k in keys:
                if bDict[k] == search[0][0]:
                    # print('found')
                    # print(k)
                    # print(bDict[k])
                    d = replaceStrInDict(d, bDict[k], value)
            search.pop(0)
    return d

def importEntries(contentTypes, languages, folder, region, token, apiKey, assetMapper=None):
    '''
    Importing Entries
    '''
    entryFolder = folder + config.folderNames['entries']
    mapDict = {}
    for contentType in contentTypes:
        ctFolder = entryFolder + contentType + '/'
        config.logging.info('{}Importing Entries of type: {}{}'.format(config.BOLD, contentType, config.END))
        for language in languages:
            languageFile = ctFolder + language + '.json'
            if os.path.isfile(languageFile):
                config.logging.info('{}Importing Entries in Language: {}{}'.format(config.BOLD, language, config.END))
                entries = config.readFromJsonFile(languageFile)
                for entry in entries['entries']:
                    if (entry['uid'] not in mapDict) and (entry['locale'] == language):
                        # print('ENTRY BEFORE MAP:')
                        # print(entry)
                        # print('----')
                        if assetMapper:
                            entry = replaceAssetFromMapper(entry, assetMapper, 'entry assets')
                        # print('ENTRY AFTER MAP:')
                        # print(entry)
                        create = cma.createEntry(apiKey, token, entry, region, contentType, language)
                        if create:
                            config.logging.info('Entry Created - Title: {} - Language: {}'.format(create['entry']['title'], language))
                            mapDict = importStructure.addToMapper(mapDict, entry['uid'], create['entry']['uid'])
                    elif (entry['uid'] in mapDict) and (entry['locale'] == language):
                        if assetMapper:
                            entry = importStructure.replaceFromMapper(assetMapper, entries, 'entries')
                        update = cma.updateEntry(apiKey, token, entry, region, contentType, language, mapDict[entry['uid']])
                        if update:
                            print(update)
                            config.logging.info('Entry Updated - Title: {} - Language: {}'.format(update['entry']['title'], language))
            else:
                config.logging.info('No entries in language: {}'.format(language))
    return importStructure.createMapperFile(apiKey, folder.split('/')[-2], mapDict, 'entries')


def sortLanguages(languages, masterLocale):
    '''
    Putting the master locale in front of the list
    '''
    newLangArr = []
    found = False
    for lang in languages:
        if lang != masterLocale:
            newLangArr.append(lang)
        else:
            found = True
    if found:
        languages = [masterLocale] + newLangArr
    return languages



def whatToImport(token, folder, importedStack, exportReport, region):
    '''
    Define what to Import
    '''
    apiKey = importedStack['uid']
    assetEnvironments, localAssets, assetNumbers, contentTypes, languages = printOutReport(exportReport)
    if importedStack['masterLocale'] != exportReport['stackStructureExportInfo']['stack']['masterLocale']:
        config.logging.warning('{}Master Locales are different between Export ({}) and Import Stack ({}). It might result in corrupt Import!{}'.format(config.YELLOW, exportReport['stackStructureExportInfo']['stack']['masterLocale'], importedStack['masterLocale'], config.END))
    importAll = importAllOrSomething()
    if not importAll:
        config.logging.info('Canceling')
        return None
    elif importAll == 'HANDPICK':
        # Import Handpicked stuff
        # assetImports = defineAssetsToImport(assetEnvironments, localAssets, assetNumbers) # It will just import all Assets.
        contentTypeImports = defineContentTypesToImport(contentTypes) # Returns a list of content types to be imported.
        if not contentTypeImports:
            config.logging.info('Canceling')
            return None
        languageImports = defineLanguagesToImport(languages)
        if not languageImports:
            return None
    else: # importAll = ALL
        config.logging.info('{}Importing All Content Available{}'.format(config.BOLD, config.END))
        assetMapper = None
        if assetNumbers:
            assetMapper = importAssets(token, importedStack, folder, exportReport, localAssets, region)
        else:
            config.logging.info('No Assets Available for Import')
        if assetMapper:
            config.logging.info('{}Assets Import Finished{}'.format(config.BOLD, config.END))
        languages = sortLanguages(languages, importedStack['masterLocale'])
        entries = importEntries(contentTypes, languages, folder, region, token, apiKey, assetMapper)
