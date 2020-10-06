'''
oskar.eiriksson@contentstack.com
2020-09-28

Exports content to a local folder

'''
import os
from time import sleep, time
import inquirer
import requests
import config
import cma
import cda

def getEnvironmentsFromExport(folder):
    '''
    Re-usable function that returns two objects from the export.
    Object 1: An array with all the environments with all information
    Object 2: An array of just the environment names
    '''
    folder = folder + config.folderNames['environments']
    envArr = []
    envArrOnlyNames = []
    for envFile in os.listdir(folder):
        environment = config.readFromJsonFile(folder + envFile)
        item = {
            'name': environment['name'],
            'uid': environment['uid']
        }
        envArr.append(item)
        envArrOnlyNames.append(environment['name'])
    return envArr, sorted(envArrOnlyNames)

def includeWorkflowStages():
    '''
    Just asking the user whether he wants to include workflow stages included in the export.
    Not possible to include stages using the delivery token.
    '''
    choice = inquirer.list_input("{}Do you want to include the entry workflow stages in the export? (It is not possible to include them using the Delivery Token (Content Delivery API)).{}".format(config.BOLD, config.END), choices=['Include Workflow Stages', 'Exclude Workflow Stages'])
    if 'Include' in choice:
        return True
    return False

def findDeliveryTokenInExport(folder, contentInfo):
    '''
    Re-usable function that tries to find the deliveryToken in the export.
    If found - we can ask the user if he wants to include the workflow stages - can't export those using the delivery token
    '''
    f = folder + config.folderNames['deliveryTokens']
    for dtFile in os.listdir(f):
        deliveryToken = config.readFromJsonFile(f + dtFile)
        config.logging.debug('Delivery Token found: {}'.format(deliveryToken))
        try:
            envName = deliveryToken['scope'][0]['environments'][0]['name']
        except KeyError:
            envName = ''
        if envName == contentInfo['environments']:
            config.logging.info('Delivery token found ({}).'.format(envName))
            includeWorkFlows = includeWorkflowStages()
            config.addToExportReport('includeWorkFlows', includeWorkFlows, folder)
            if includeWorkFlows:
                return None
            return deliveryToken['token']
    return None

def defineEntriesToExport(info):
    '''
    Choose from what publishing environments we should export entries:
        - All Entries?
        - Only Entries from a certain Environment?
    '''
    publishedEntriesAnswer = None
    folder = info['folder']['fullPath']
    while publishedEntriesAnswer != 'Cancel and Exit':
        _, envArrOnlyNames = getEnvironmentsFromExport(folder)
        exportEntriesArr = ['All Entries'] + envArrOnlyNames + ['Cancel and Exit']

        choosePublishEnv = [
            inquirer.List('choosePublishEnv',
                          message="{}Choose what Entries to Export:{}".format(config.BOLD, config.END),
                          choices=exportEntriesArr,
                          ),
        ]
        publishedEntriesAnswer = inquirer.prompt(choosePublishEnv)['choosePublishEnv']

        if publishedEntriesAnswer == 'All Entries':
            publishEnvironment = 'all'
        elif publishedEntriesAnswer.split(' Environment')[0] in envArrOnlyNames:
            publishEnvironment = publishedEntriesAnswer.split(' Environment')[0]
        else:
            publishEnvironment = None
        return publishEnvironment
    return None

def defineAssetsToExport(entriesToExport):
    '''
    Choose what assets to export:
        - No Assets? (It only means we are not taking local copies of the assets)
        - All Assets?
        - All published assets to the environment they already chose from?
    '''
    choices = ['No Assets (Only means we are not taking a local copy)', 'All Assets']
    if entriesToExport != 'all':
        choices.append(entriesToExport + ' Environment')
    choices.append('Cancel and Exit')

    chooseAssets = [
        inquirer.List('chooseAssets',
                      message="{}Choose what Assets to Export:{}".format(config.BOLD, config.END),
                      choices=choices,
                      ),
    ]
    assetsToExport = inquirer.prompt(chooseAssets)['chooseAssets']

    if assetsToExport == 'All Assets':
        answer = 'all'
    elif ' Environment' in assetsToExport:
        answer = assetsToExport.split(' Environment')[0]
    else:
        answer = None
    return answer

def defineLanguagesToExport(info):
    '''
    Choose languages to export. For both entries and assets.
    '''
    folder = info['folder']['fullPath'] + config.folderNames['languages']
    langArr = []
    for lang in os.listdir(folder):
        langArr.append(lang.replace('.json', ''))
    langArr = sorted(langArr)
    chooseAllLanguagesOrNot = [
        inquirer.List('chooseAllLanguagesOrNot',
                      message="{}Do you want to export all languages, or handpick some?:{}".format(config.BOLD, config.END),
                      choices=['All Languages', 'Choose Languages(s) to Export', 'Cancel and Exit'],
                      ),
    ]
    allOrNothing = inquirer.prompt(chooseAllLanguagesOrNot)['chooseAllLanguagesOrNot']
    if allOrNothing == 'All Languages':
        return langArr
    elif allOrNothing == 'Cancel and Exit':
        return None
    pickedLanguages = []
    while not pickedLanguages:
        pickLanguages = [
            inquirer.Checkbox('pickLanguages',
                              message="Pick Languages With Space Bar and Press Return when Finished.",
                              choices=langArr,
                              ),
        ]
        pickedLanguages = inquirer.prompt(pickLanguages)['pickLanguages']
        if not pickedLanguages:
            config.logging.warning('{}You must pick one language or more{}'.format(config.YELLOW, config.END))
    return pickedLanguages


def defineContentTypesToExport(info):
    '''
    Choose content types to export.
    '''
    folder = info['folder']['fullPath'] + config.folderNames['contentTypes']
    ctArr = []
    for ct in os.listdir(folder):
        ctArr.append(ct.replace('.json', ''))
    chooseAllContentTypesOrNot = [
        inquirer.List('chooseAllContentTypesOrNot',
                      message="{}Do you want to export all languages, or handpick some?:{}".format(config.BOLD, config.END),
                      choices=['All Content Types', 'Choose Content Type(s) to Export', 'Cancel and Exit'],
                      ),
    ]
    allOrNothing = inquirer.prompt(chooseAllContentTypesOrNot)['chooseAllContentTypesOrNot']
    if allOrNothing == 'All Content Types':
        return ctArr
    elif allOrNothing == 'Cancel and Exit':
        return None
    pickedContentTypes = []
    while not pickedContentTypes:
        pickContentTypes = [
            inquirer.Checkbox('pickContentTypes',
                              message="Pick Content Types With Space Bar and Press Return when Finished.",
                              choices=ctArr,
                              ),
        ]
        pickedContentTypes = inquirer.prompt(pickContentTypes)['pickContentTypes']
        if not pickedContentTypes:
            config.logging.warning('{}You must pick one content types or more{}'.format(config.YELLOW, config.END))
    return pickedContentTypes

def defineAssetDownload():
    '''
    Just asking the user if he wants to download the assets themselves, or just the metadata
    If he chooses just the metadata, he choose to course import them later, no matter if they are on the local drive or not.
        --> Caveat: They have to still be present on the original export stack when that is done.
    '''
    downloadAssets = [
        inquirer.List('downloadAssets',
                      message="{}Do you want to download the assets to your local drive, or just the metadata? (Can be imported later directly from the export stack - they need to be present on the stack for that):{}".format(config.BOLD, config.END),
                      choices=['Download Asset Files', 'Only Download Metadata'],
                      ),
    ]
    answer = inquirer.prompt(downloadAssets)['downloadAssets']
    if answer == 'Download Asset Files':
        return True
    return False


def whatContentToExport(info):
    '''
    Giving the user the possibility to export certain entries, or just a subset of them.
    Giving the user the possibility to export copies of the assets, if they want.
    '''
    entriesToExport = defineEntriesToExport(info)
    languagesToExport = defineLanguagesToExport(info)
    contentTypesToExport = defineContentTypesToExport(info)
    assetsToExport = defineAssetsToExport(entriesToExport)
    downloadAssets = False
    if assetsToExport:
        downloadAssets = defineAssetDownload()
    report = {'environments': entriesToExport, 'assets': assetsToExport, 'downloadAssets': downloadAssets, 'languages': languagesToExport, 'contentTypes': contentTypesToExport}
    return report

def exportEntriesUsingDeliveryToken(stackInfo, token, environment, folder, contentInfo):
    '''
    Using delivery token to export entries from a single environment
    '''
    languages = contentInfo['languages']
    contentTypes = contentInfo['contentTypes']
    entryFolder = folder + config.folderNames['entries']
    config.logging.debug('{}Using Delivery Token to Export. Variables for debug:{}'.format(config.CYAN, config.END))
    config.logging.debug('{}stackInfo: {}{}'.format(config.CYAN, stackInfo, config.END))
    config.logging.debug('{}contentInfo: {}{}'.format(config.CYAN, contentInfo, config.END))
    config.logging.debug('{}entryFolder: {}{}'.format(config.CYAN, entryFolder, config.END))
    config.checkDir(entryFolder)
    counter = 0
    for contentType in contentTypes:
        entryFolderPerContentType = entryFolder + contentType + '/'
        config.checkDir(entryFolderPerContentType)
        config.logging.info('{}Exporting Entries of Content Type: {}{}'.format(config.GREEN, contentType, config.END))
        for language in languages:
            config.logging.info('{}Exporting Entries of Language: {}{}'.format(config.BOLD, language, config.END))
            entries = cda.getAllEntries(stackInfo, contentType, language, environment, token)
            if entries:
                # I wish I could see all entries, based on where the master locale is published.
                # But I need to get all entries and see the publishing details in them
                # e.g. to see whether en-us (master or fallback) is published on the is-is
                fileName = entryFolderPerContentType + language + '.json'
                if config.writeToJsonFile(entries, fileName):
                    config.logging.info('Entries Exported to File. {}'.format(fileName))
                    counter = counter + len(entries['entries'])
                else:
                    config.logging.error('{}Unable to write to file. {}{}'.format(config.RED, fileName, config.END))
            else:
                config.logging.info('No Entries. {} - {}'.format(contentType, language))
    return True

def exportEntriesUsingAuthToken(stackInfo, authToken, folder, contentInfo, environment=None):
    '''
    Exporting entries using the Content Management API.
    Just ALL Entries on one hand, and based on published environment on the other hand.
    We need to get the entries for the master locale first. Then see what locales are available for those entries.
    '''
    languages = contentInfo['languages']
    # masterLocale = stackInfo['masterLocale']
    contentTypes = contentInfo['contentTypes']
    assetsToExport = contentInfo['assets'] # 'all', 'referenced' or 'noAssets'
    config.logging.debug('Assets to export: {}'.format(assetsToExport))
    entryFolder = folder + config.folderNames['entries']
    config.checkDir(entryFolder)
    counter = 0
    for contentType in contentTypes:
        ctFolder = entryFolder + contentType + '/'
        config.checkDir(ctFolder)
        if environment:
            config.logging.info('{}{}Exporting Entries of Content Type: {} from Environment: {}{}'.format(config.BOLD, config.GREEN, contentType, environment, config.END))
        else:
            config.logging.info('{}{}Exporting Entries of Content Type: {}{}'.format(config.BOLD, config.GREEN, contentType, config.END))

        for language in languages:
            config.logging.info('Exporting from Language: {}'.format(language))
            entries = cma.getAllEntries(stackInfo, contentType, language, authToken, environment)
            if entries:
                fileName = ctFolder + language + '.json'
                # if (language != masterLocale) and (fallbackLanguage is not None):
                # We need to confirm that entry is not using the fallback_locale.
                # If it's in a different language, we do not want to export it.
                # I wish I could add an extra parameter to the request, e.g. ?include_fallback_locale=false and just get empty responses.
                # We see in the master locale in what languages it is published in.
                newEntries = {'entries': []}
                for entry in entries['entries']:
                    if entry['locale'] == language: # We know it's the right language
                        newEntries['entries'].append(entry)
                if newEntries['entries']:
                    if config.writeToJsonFile(newEntries, fileName):
                        config.logging.info('Entries Exported to File. {}'.format(fileName))
                        counter = counter + len(entries['entries'])
                else:
                    config.logging.debug('No Entries. {} - {}'.format(contentType, language))
            config.logging.info('No Entries. {} - {}'.format(contentType, language))
    return True

def processAssetExport(assets, stackInfo, folder, masterLocale, downloadAssets):
    '''
    Re-usable function where exported entries (both via CMA and CDA) are worked on and written to export folders.
    '''
    if not assets:
        return False
    for asset in assets['assets']:
        uid = asset['uid']
        assetFolder = folder + uid + '/'
        config.checkDir(assetFolder)
        assetFileName = asset['filename']
        metadataFileName = uid + '_v{}.json'.format(asset['_version'])
        if config.writeToJsonFile({'asset': asset}, assetFolder + metadataFileName):
            config.logging.info('Image metadata written to {}'.format(metadataFileName))
        if downloadAssets:
            assetUrl = asset['url']
            config.logging.info('Downloading Asset: {} To file path: {}'.format(assetUrl, assetFileName))
            config.downloadFileToDisk(assetUrl, assetFolder, assetFileName)
        if 'publish_details' in asset:

            config.logging.info('Adding publishing details to export file: {}'.format(assetFolder + 'publishDetails.json'))
            if isinstance(asset['publish_details'], list):
                for i in asset['publish_details']:
                    key = i['locale'] + '-' + i['environment']
                    config.addToJsonFile({key: i}, assetFolder + 'publishDetails.json')
            else:
                key = asset['publish_details']['locale'] + '-' + asset['publish_details']['environment']
                config.addToJsonFile({key:asset['publish_details']}, assetFolder + 'publishDetails.json')
    return True

def exportAssetsUsingAuthToken(stackInfo, authToken, folder, contentInfo, environment=None):
    '''
    Exporting Assets using the Auth token
    Environment optional
    '''
    config.addToExportReport('AssetExportMethod', 'AuthToken', folder)
    masterLocale = stackInfo['masterLocale']
    downloadAssets = contentInfo['downloadAssets']
    folder = folder + config.folderNames['assets']
    config.checkDir(folder)
    if environment:
        config.logging.info('{}Exporting Assets on Environment {} using Auth Token{}'.format(config.BOLD, environment, config.END))
    else:
        config.logging.info('{}Exporting all Assets using Auth Token{}'.format(config.BOLD, config.END))
    assets = cma.getAllAssets(stackInfo, authToken, environment)
    if processAssetExport(assets, stackInfo, folder, masterLocale, downloadAssets):
        config.logging.info('Finished Exporting Assets')
        return True
    config.logging.error('{}Unable to export Assets!{}')
    return False


def exportAssetsDeliveryToken(stackInfo, deliveryToken, environment, folder, contentInfo):
    '''
    Exporting Assets using the Delivery Token
    '''
    config.addToExportReport('AssetExportMethod', 'DeliveryToken', folder)
    masterLocale = stackInfo['masterLocale']
    downloadAssets = contentInfo['downloadAssets']
    folder = folder + config.folderNames['assets']
    config.checkDir(folder)
    config.logging.info('{}Exporting Assets on Environment {} using the Delivery Token{}'.format(config.BOLD, environment, config.END))
    assets = cda.getAllAssets(stackInfo, deliveryToken, environment)
    if processAssetExport(assets, stackInfo, folder, masterLocale, downloadAssets):
        config.logging.info('Finished Exporting Assets')
        return True
    config.logging.error('{}Unable to export Assets!{}')
    return False



def exportAssetFolders(authToken, stackInfo, folder):
    '''
    Exporting All Folders to a single JSON file
    '''
    foldersFolder = folder + config.folderNames['folders']
    fileName = foldersFolder + config.fileNames['folders']
    config.checkDir(folder)
    folders = cma.getAllFolders(stackInfo, authToken)
    if folders:
        if config.writeToJsonFile(folders, fileName):
            config.logging.info('Folders Exported to file. ({})'.format(fileName))
            return True
        config.logging.error('{}Unable to write Folders to file: {}{}'.format(config.RED, fileName, config.END))
        return None
    config.logging.warning('{}No Asset Folders found on Stack.{}'.format(config.YELLOW, config.END))
    return None


def iniateExportContent(stackInfo, contentInfo, authToken):
    '''
    Exporting content
    '''
    folder = stackInfo['folder']['fullPath'] # Where the export is stored on the local drive
    assetsToExport = contentInfo['assets']
    entriesToExport = contentInfo['environments'] # Entries to be exported are either 'all' or based on environment, e.g. 'development'

    '''
    Starting Entries Export
    '''
    entriesStartTime = time()
    config.logging.debug('Entries to export: {}'.format(entriesToExport))
    useDeliveryToken = False # If we have environment and find a delivery token for that environment in the export, we can use the Content Delivery API -> Much faster
    if entriesToExport != 'all': # !=all -> We have environment, e.g. 'development'
        config.logging.info('Found a single environment to be exported ({}). We will attempt to use the exported delivery token.'.format(entriesToExport))
        deliveryToken = findDeliveryTokenInExport(folder, contentInfo)  # Trying to find the delivery token in the export
        if deliveryToken:
            config.addToExportReport('useDeliveryToken', True, folder)
            useDeliveryToken = True # We found a delivery token!
        else: # We did not find a delivery token - so we need to use the content management API to export the entries
            config.addToExportReport('useDeliveryToken', False, folder)
            config.logging.info('We will use the Content Management API to Export Entries')
            exportEntriesUsingAuthToken(stackInfo, authToken, folder, contentInfo, entriesToExport)
    if useDeliveryToken:
        config.logging.info('Found a Delivery Token for chosen Environment ({}). Will use the Content Delivery API to Export Entries.'.format(entriesToExport))
        exportEntriesUsingDeliveryToken(stackInfo, deliveryToken, entriesToExport, folder, contentInfo)
    if contentInfo['environments'] == 'all':
        config.logging.info('Iniating Entries Export using the Content Management API on all Entries/Assets.')
        exportEntriesUsingAuthToken(stackInfo, authToken, folder, contentInfo)
    entriesEndTime = time()
    totalEntriesTime = entriesEndTime - entriesStartTime
    config.logging.info('{}Export Entries finished in {} seconds{}'.format(config.BOLD, totalEntriesTime, config.END))


    '''
    Starting Assets Export
    '''
    assetsStartTime = time()
    assetsExported = foldersExported = True # Just to set something...
    if not assetsToExport:
        config.logging.info('{}No Assets Exported.{}'.format(config.BOLD, config.END))
    elif assetsToExport == 'all':
        config.logging.info('{}All Assets will be Exported.{}'.format(config.BOLD, config.END))
        assetsExported = exportAssetsUsingAuthToken(stackInfo, authToken, folder, contentInfo)
    else: # Exporting assets based on environment - Possibly with the delivery token found
        if useDeliveryToken: # delivery token found - can be used on assets
            config.logging.info('Assets from the {} Environment will now be Exported, using the Content Delivery API (Delivery Token).')
            assetsExported = exportAssetsDeliveryToken(stackInfo, deliveryToken, assetsToExport, folder, contentInfo)
        else: # delivery token NOT found
            config.logging.info('Assets from the {} Environment will now be Exported, using the Content Management API (Auth Token).')
            assetsExported = exportAssetsUsingAuthToken(stackInfo, authToken, folder, contentInfo, assetsToExport)
    if assetsToExport: # The folder structure needs to be exported as well.
        config.logging.info('Exporting Asset Folders')
        foldersExported = exportAssetFolders(authToken, stackInfo, folder)
    if assetsExported:# and foldersExported:
        config.logging.info('{}Assets and Folders exported{}'.format(config.BOLD, config.END))
    else:
        config.logging.warning('{}Something did not work like intended in Asset and Folder Export. Please verify the export.{}'.format(config.YELLOW, config.END))
    assetsEndTime = time()
    totalAssetsTime = assetsEndTime - assetsStartTime
    totalTime = totalEntriesTime + totalAssetsTime
    config.logging.info('{}Export Assets finished in {} seconds{}'.format(config.BOLD, totalAssetsTime, config.END))
    config.logging.info('{}Total Export Content finished in {} seconds{}'.format(config.BOLD, totalTime, config.END))
