'''
oskar.eiriksson@contentstack.com
2020-09-28

Exports content to a local folder

'''
import inquirer
import config
import cma
import cda

def defineEntriesFromEnvironmentsToExport(info):
    '''
    Choose from what publishing environments we should export entries:
        - All Entries?
        - All Published Entries?
        - Only Entries from a certain Environment?
    '''
    publishedEntriesAnswer = None
    while publishedEntriesAnswer != 'Cancel and Exit':
        folder = config.localFolder + '/' + info['folder'] + '/'
        environments = config.readFromJsonFile(folder + config.fileNames['environments'])
        envArr = []
        envArrOnlyNames = []
        if environments:
            for environment in environments['environments']:
                item = {
                    'name': environment['name'],
                    'uid': environment['uid']
                }
                envArr.append(item)
                envArrOnlyNames.append(environment['name'])
        exportEntriesArr = ['All Entries']
        for env in envArr:
            exportEntriesArr.append(env['name'] + ' Environment')
        exportEntriesArr.append('Cancel and Exit')

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

def defineAssetsToExport():
    '''
    Choose what assets to export:
        - No Assets? (It only means we are not taking local copies of the assets)
        - All Assets?
        - All Referenced Assets in Exported Entries?
    '''

    chooseAssets = [
        inquirer.List('chooseAssets',
                      message="{}Choose what Assets to Export:{}".format(config.BOLD, config.END),
                      choices=['No Assets (Only means we are not taking a local copy)', 'All Assets', 'Only Assets Referenced in Exported Entries', 'Cancel and Exit'],
                      ),
    ]
    assetsToExport = inquirer.prompt(chooseAssets)['chooseAssets']

    if assetsToExport == 'All Assets':
        answer = 'allAssets'
    elif assetsToExport == 'Only Assets Referenced in Exported Entries':
        answer = 'referencedAssets'
    elif assetsToExport == 'Cancel and Exit':
        answer = None
    else:
        answer = 'noAssets'
    return answer

def defineLanguagesToExport(info):
    '''
    Choose languages to export. For both entries and assets.
    '''
    folder = config.localFolder + '/' + info['folder'] + '/'
    languages = config.readFromJsonFile(folder + config.fileNames['languages'])
    langArr = []
    for locale in languages['locales']:
        langArr.append(locale['code'])
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
            cma.logging.warning('{}You must pick one language or more{}'.format(config.YELLOW, config.END))
    return pickedLanguages


def defineContentTypesToExport(info):
    '''
    Choose content types to export.
    '''
    folder = config.localFolder + '/' + info['folder'] + '/'
    contentTypes = config.readFromJsonFile(folder + config.fileNames['contentTypes'])
    ctArr = []
    for contentType in contentTypes['content_types']:
        ctArr.append(contentType['uid'])
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
            cma.logging.warning('{}You must pick one content types or more{}'.format(config.YELLOW, config.END))
    return pickedContentTypes


def whatContentToExport(info):
    '''
    Giving the user the possibility to export certain entries, or just a subset of them.
    Giving the user the possibility to export copies of the assets, if they want.
    '''
    publishingEnvironmentsToExport = defineEntriesFromEnvironmentsToExport(info)
    if not publishingEnvironmentsToExport:
        return None
    assetsToExport = defineAssetsToExport()
    if not assetsToExport:
        return None
    languagesToExport = defineLanguagesToExport(info)
    if not languagesToExport:
        return None
    contentTypesToExport = defineContentTypesToExport(info)
    if not contentTypesToExport:
        return None
    return {'environments': publishingEnvironmentsToExport, 'assets': assetsToExport, 'languages': languagesToExport, 'contentTypes': contentTypesToExport}

def findDeliveryToken(folder, contentInfo):
    deliveryTokens = config.readFromJsonFile(folder + config.fileNames['deliveryTokens'])
    if deliveryTokens:
        for deliveryToken in deliveryTokens['tokens']:
            try:
                envName = deliveryToken['scope'][0]['environments'][0]['name']
            except KeyError:
                envName = ''
            if envName == contentInfo['environments']:
                return deliveryToken['token']
    return None

def exportEntriesUsingDeliveryToken(stackInfo, token, environment, folder, contentInfo):
    '''
    Using delivery token to export entries from a single environment
    '''
    apiKey = stackInfo['apiKey']
    languages = contentInfo['languages']
    contentTypes = contentInfo['contentTypes']
    for language in languages:
        config.checkDir(folder.split('/')[1] + '/' + language)
        cma.logging.info('{}{}Exporting Entries of Language: {}{}'.format(config.BOLD, config.GREEN, language, config.END))
        for contentType in contentTypes:
            cma.logging.info('{}Exporting Entries of Content Type {} in Language {}{}'.format(config.BOLD, contentType, language, config.END))
            entries = cda.getAllEntries(stackInfo, contentType, language, environment, token)
            if entries:
                config.checkDir(folder.split('/')[1] + '/' + language + '/' + contentType) # Create the content type folder
                fileName = folder + language + '/' + contentType + '/' + config.fileNames['entries']
                config.writeToJsonFile(entries, fileName)
                cma.logging.info('Entries Exported to File. {}'.format(fileName))

def exportEntriesUsingAuthToken(stackInfo, authToken, folder, contentInfo):
    '''
    Exporting entries using the Content Management API.
    Just ALL Entries
    '''
    apiKey = stackInfo['apiKey']
    languages = contentInfo['languages']
    contentTypes = contentInfo['contentTypes']
    for language in languages:
        config.checkDir(folder.split('/')[1] + '/' + language)
        cma.logging.info('{}{}Exporting Entries of Language: {}{}'.format(config.BOLD, config.GREEN, language, config.END))
        for contentType in contentTypes:
            cma.logging.info('{}Exporting Entries of Content Type {} in Language {}{}'.format(config.BOLD, contentType, language, config.END))
            entries = cma.getAllEntries(stackInfo, contentType, language, authToken)
            if entries:
                config.checkDir(folder.split('/')[1] + '/' + language + '/' + contentType) # Create the content type folder
                fileName = folder + language + '/' + contentType + '/' + config.fileNames['entries']
                config.writeToJsonFile(entries, fileName)
                cma.logging.info('Entries Exported to File. {}'.format(fileName))

def iniateExportEntries(stackInfo, contentInfo, authToken):
    '''
    Exporting entries
    '''
    folder = config.localFolder + '/' + stackInfo['folder'] + '/'
    useDeliveryToken = False
    if contentInfo['environments'] != 'all':
        cma.logging.info('Found a single environment to be exported ({}). We will attempt to use the exported delivery token.'.format(contentInfo['environments']))
        deliveryToken = findDeliveryToken(folder, contentInfo)
        if deliveryToken:
            useDeliveryToken = True
        else:
            cma.logging.info('Unable to find a delivery token for that environment. We will use the Content Management API for Export')
    if useDeliveryToken:
        cma.logging.info('Found a Delivery Token for chosen Environment ({}). Will use that to Export Entries.'.format(contentInfo['environments']))
        entriesExport = exportEntriesUsingDeliveryToken(stackInfo, deliveryToken, contentInfo['environments'], folder, contentInfo)
    if contentInfo['environments'] == 'all':
        cma.logging.info('Iniating Entries Export using the Content Management API on all entries. Will use that to Export Entries.')
        entriesExport = exportEntriesUsingAuthToken(stackInfo, authToken, folder, contentInfo)
