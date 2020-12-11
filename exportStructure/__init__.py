'''
oskar.eiriksson@contentstack.com
2020-10-02

Exports stack structure to local folder.
Limitation: Does not export Management Tokens.
'''
from time import sleep, time
import os
import inquirer
import cma
import config

def chooseFolder():
    '''
    Lists up folders in export folder.
    Optionally, there's a folder to be ignored from the list.
    The user just picks one.
    '''
    ignoreFolder = config.mapperFolder
    allFolders = []
    for f in os.listdir(config.dataRootFolder + config.stackRootFolder):
        f = f + '/'
        if f != ignoreFolder:
            allFolders.append(f)
    folder = [
        inquirer.List('chosenFolder',
                      message="{}Choose export folder to import from{}".format(config.BOLD, config.END),
                      choices=allFolders,
                      ),
    ]
    folder = inquirer.prompt(folder)['chosenFolder']
    return folder

def writeExport(exportItem, folderPath, keyToLabelFile):
    '''
    re-usable function where we attempt to write exports to file
    example for content types: (contentTypeBody, data/<exportedStackName + Datestamp>/contentTypes/, 'uid')
        --> 'uid' is just the key from the export to be used as file name... sometimes the uid, the name, the title... just has to be a unique field
    '''

    for item in exportItem:
        filePath = folderPath + item[keyToLabelFile].replace('/', '-') + '.json' # I personally put a "/" in a custom role name. It breaks everything here...
        write = config.writeToJsonFile(item, filePath)
        if not write:
            config.logging.error('{}Not able to write to file: {}{}'.format(config.BOLD, filePath, config.END))
    return True

def exportContentTypes(apiKey, token, region, folder):
    '''
    Exporting content types with global fields schema
    '''
    config.logging.info('Exporting content types')
    folderPath = config.defineFullFolderPath(folder, 'contentTypes')
    contentTypesExport = cma.getAllContentTypes(apiKey, token, region)
    if contentTypesExport:
        return writeExport(contentTypesExport['content_types'], folderPath, 'uid')
    config.logging.info('{}Missing content type response from Contentstack. Do you have content types in that stack?{}'.format(config.YELLOW, config.END))
    return False

def getContentTypeUids(folder):
    '''
    Creates a list with all content type uids
    '''
    path = config.defineFullFolderPath(folder, 'contentTypes')
    ctArr = []
    for ct in path:
        ctArr.append(ct.strip('json'))
    return ctArr

def exportGlobalFields(apiKey, token, region, folder):
    '''
    Exporting global fields
    '''
    config.logging.info('Exporting global fields')
    folderPath = config.defineFullFolderPath(folder, 'globalFields')
    globalFieldsExport = cma.getAllGlobalFields(apiKey, token, region)
    if globalFieldsExport:
        return writeExport(globalFieldsExport['global_fields'], folderPath, 'uid')
    config.logging.info('{}Missing global field response from Contentstack.{}'.format(config.YELLOW, config.END))
    return False

def exportExtensions(apiKey, token, region, folder):
    '''
    Exporting Extensions
    '''
    config.logging.info('Exporting extensions')
    folderPath = config.defineFullFolderPath(folder, 'extensions')
    extensionsExport = cma.getAllExtensions(apiKey, token, region)
    if extensionsExport:
        return writeExport(extensionsExport['extensions'], folderPath, 'title')
    config.logging.info('{}Missing extensions response from Contentstack.{}'.format(config.YELLOW, config.END))
    return False

def exportWorkflows(apiKey, token, region, folder):
    '''
    Exporting workflows
    '''
    config.logging.info('Exporting workflows')
    folderPath = config.defineFullFolderPath(folder, 'workflows')
    workflowsExport = cma.getAllWorkflows(apiKey, token, region)
    if workflowsExport:
        return writeExport(workflowsExport['workflows'], folderPath, 'name')
    config.logging.info('{}Missing workflow response from Contentstack.{}'.format(config.YELLOW, config.END))
    return False

def exportPublishingRules(contentTypeUids, apiKey, token, region, folder):
    '''
    Exporting publishing rules
    '''
    config.logging.info('Exporting all publishing rules')
    folderPath = config.defineFullFolderPath(folder, 'publishingRules')
    publishingRulesExport = cma.getAllPublishingRules(contentTypeUids, apiKey, token, region)
    if publishingRulesExport:
        return writeExport(publishingRulesExport['publishing_rules'], folderPath, 'uid')
    config.logging.info('{}Missing publishing rule response from Contentstack.{}'.format(config.YELLOW, config.END))
    return False

def exportLabels(apiKey, token, region, folder):
    '''
    Exporting Labels
    '''
    config.logging.info('Exporting all labels')
    folderPath = config.defineFullFolderPath(folder, 'labels')
    labelsExport = cma.getAllLabels(apiKey, token, region)
    if labelsExport:
        return writeExport(labelsExport['labels'], folderPath, 'name')
    config.logging.info('{}Missing label response from Contentstack.{}'.format(config.YELLOW, config.END))
    return False

def exportLanguages(apiKey, token, region, folder):
    '''
    Exporting Languages
    '''
    config.logging.info('Exporting all languages')
    folderPath = config.defineFullFolderPath(folder, 'languages')
    languagesExport = cma.getAllLanguages(apiKey, token, region)
    if languagesExport:
        return writeExport(languagesExport['locales'], folderPath, 'code')
    config.logging.info('{}Missing language response from Contentstack.{}'.format(config.YELLOW, config.END))
    return False

def exportEnvironments(apiKey, token, region, folder):
    '''
    Exporting Environments
    '''
    config.logging.info('Exporting All Environments')
    folderPath = config.defineFullFolderPath(folder, 'environments')
    environmentsExport = cma.getAllEnvironments(apiKey, token, region)
    if environmentsExport:
        return writeExport(environmentsExport['environments'], folderPath, 'name')
    config.logging.info('{}Missing environment response from Contentstack.{}'.format(config.YELLOW, config.END))
    return False

def exportDeliveryTokens(apiKey, token, region, folder):
    '''
    Exporting Delivery Tokens
    '''
    config.logging.info('Exporting All Delivery Tokens')
    folderPath = config.defineFullFolderPath(folder, 'deliveryTokens')
    deliveryTokensExport = cma.getAllDeliveryTokens(apiKey, token, region)
    if deliveryTokensExport:
        return writeExport(deliveryTokensExport['tokens'], folderPath, 'name')
    config.logging.info('{}Missing delivery token response from Contentstack.{}'.format(config.YELLOW, config.END))
    return False

def exportRoles(apiKey, token, region, folder):
    '''
    Exporting Roles
    '''
    config.logging.info('Exporting All Roles')
    folderPath = config.defineFullFolderPath(folder, 'roles')
    rolesExport = cma.getAllRoles(apiKey, token, region)
    if rolesExport:
        return writeExport(rolesExport['roles'], folderPath, 'name')
    config.logging.info('{}Missing role response from Contentstack.{}'.format(config.YELLOW, config.END))
    return False

def exportWebhooks(apiKey, token, region, folder):
    '''
    Exporting Webhooks
    '''
    config.logging.info('Exporting All Webhooks')
    folderPath = config.defineFullFolderPath(folder, 'webhooks')
    webhooksExport = cma.getAllWebhooks(apiKey, token, region)
    if webhooksExport:
        return writeExport(webhooksExport['webhooks'], folderPath, 'name')
    config.logging.info('{}Missing webhook response from Contentstack.{}'.format(config.YELLOW, config.END))
    return False

def exportStack(apiKey, token, region, folder):
    '''
    Export stack function
    '''
    config.logging.info('{}Starting structure export to folder: {}{}'.format(config.BOLD, folder['fullPath'], config.END))
    startTime = time()
    exportContentTypes(apiKey, token, region, folder)
    exportGlobalFields(apiKey, token, region, folder)
    exportExtensions(apiKey, token, region, folder)
    exportWorkflows(apiKey, token, region, folder)
    contentTypeUids = getContentTypeUids(folder) # Need to get all content types to fetch publishing rules
    exportPublishingRules(contentTypeUids, apiKey, token, region, folder)
    exportEnvironments(apiKey, token, region, folder)
    exportDeliveryTokens(apiKey, token, region, folder)
    exportRoles(apiKey, token, region, folder)
    exportWebhooks(apiKey, token, region, folder)
    exportLabels(apiKey, token, region, folder)
    exportLanguages(apiKey, token, region, folder)
    endTime = time()
    totalTime = endTime - startTime
    config.logging.info('{}Export finished in {} seconds{}'.format(config.BOLD, totalTime, config.END))
