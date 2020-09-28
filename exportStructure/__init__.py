'''
oskar.eiriksson@contentstack.com
2020-08-13

Exports stack structure to local folder..

See Readme for details.
'''
from time import sleep
import cma
import config


def exportContentTypes(apiKey, token, region, folder):
    '''
    Exporting content types with global fields schema
    '''
    cma.logging.info('Exporting content types')
    contentTypesExport = cma.getAllContentTypes(apiKey, token, region)
    if contentTypesExport:
        return config.writeToJsonFile(contentTypesExport, config.localFolder + '/' + folder + '/' + config.fileNames['contentTypes'])
    cma.logging.error('Missing content type response from Contentstack.')
    return False

def getContentTypeUids(folder):
    '''
    Reads from content type JSON file and returns an array with uids of all content types
    '''
    cma.logging.info('Reading content type json file and getting uids of all types')
    ct = config.readFromJsonFile(config.localFolder + '/' + folder + '/' + config.fileNames['contentTypes'])
    ctArr = []
    for contentType in ct['content_types']:
        ctArr.append(contentType['uid'])
    cma.logging.debug('All Content Type UIDs:')
    cma.logging.debug(ctArr)
    return ctArr

def exportGlobalFields(apiKey, token, region, folder):
    '''
    Exporting global fields
    '''
    cma.logging.info('Exporting global fields')
    globalFieldsExport = cma.getAllGlobalFields(apiKey, token, region)
    if globalFieldsExport:
        return config.writeToJsonFile(globalFieldsExport, config.localFolder + '/' + folder + '/' + config.fileNames['globalFields'])
    cma.logging.error('Missing global fields response from Contentstack.')
    return False

def exportExtensions(apiKey, token, region, folder):
    '''
    Exporting Extensions
    '''
    cma.logging.info('Exporting extensions')
    extensionsExport = cma.getAllExtensions(apiKey, token, region)
    if extensionsExport:
        return config.writeToJsonFile(extensionsExport, config.localFolder + '/' + folder + '/' + config.fileNames['extensions'])
    cma.logging.error('Missing extensions response from Contentstack.')
    return False

def exportWorkflows(apiKey, token, region, folder):
    '''
    Exporting workflows
    '''
    cma.logging.info('Exporting workflows')
    workflowsExport = cma.getAllWorkflows(apiKey, token, region)
    if workflowsExport:
        return config.writeToJsonFile(workflowsExport, config.localFolder + '/' + folder + '/' + config.fileNames['workflows'])
    cma.logging.error('Missing workflows response from Contentstack.')
    return False

def exportPublishingRules(contentTypeUids, apiKey, token, region, folder):
    '''
    Exporting publishing rules
    '''
    cma.logging.info('Exporting all publishing rules')
    publishingRulesExport = cma.getAllPublishingRules(contentTypeUids, apiKey, token, region)
    if publishingRulesExport:
        return config.writeToJsonFile(publishingRulesExport, config.localFolder + '/' + folder + '/' + config.fileNames['publishingRules'])
    cma.logging.error('Missing publishing rules response from Contentstack.')
    return False

def exportLabels(apiKey, token, region, folder):
    '''
    Exporting Labels
    '''
    cma.logging.info('Exporting all labels')
    labelsExport = cma.getAllLabels(apiKey, token, region)
    if labelsExport:
        return config.writeToJsonFile(labelsExport, config.localFolder + '/' + folder + '/' + config.fileNames['labels'])
    cma.logging.error('Missing labels response from Contentstack.')
    return False

def exportLanguages(apiKey, token, region, folder):
    '''
    Exporting Languages
    '''
    cma.logging.info('Exporting all languages')
    languagesExport = cma.getAllLanguages(apiKey, token, region)
    if languagesExport:
        return config.writeToJsonFile(languagesExport, config.localFolder + '/' + folder + '/' + config.fileNames['languages'])
    cma.logging.error('Missing languages response from Contentstack.')
    return False

def exportEnvironments(apiKey, token, region, folder):
    '''
    Exporting Environments
    '''
    cma.logging.info('Exporting All Environments')
    environmentsExport = cma.getAllEnvironments(apiKey, token, region)
    if environmentsExport:
        return config.writeToJsonFile(environmentsExport, config.localFolder + '/' + folder + '/' + config.fileNames['environments'])
    cma.logging.error('Missing environments response from Contentstack.')
    return False

def exportDeliveryTokens(apiKey, token, region, folder):
    '''
    Exporting Delivery Tokens
    '''
    cma.logging.info('Exporting All Delivery Tokens')
    deliveryTokensExport = cma.getAllDeliveryTokens(apiKey, token, region)
    if deliveryTokensExport:
        return config.writeToJsonFile(deliveryTokensExport, config.localFolder + '/' + folder + '/' + config.fileNames['deliveryTokens'])
    cma.logging.error('Missing delivery tokens response from Contentstack.')
    return False

def exportRoles(apiKey, token, region, folder):
    '''
    Exporting Roles
    '''
    cma.logging.info('Exporting All Roles')
    rolesExport = cma.getAllRoles(apiKey, token, region)
    if rolesExport:
        return config.writeToJsonFile(rolesExport, config.localFolder + '/' + folder + '/' + config.fileNames['roles'])
    cma.logging.error('Missing roles response from Contentstack.')
    return False

def exportWebhooks(apiKey, token, region, folder):
    '''
    Exporting Webhooks
    '''
    cma.logging.info('Exporting All Webhooks')
    webhooksExport = cma.getAllWebhooks(apiKey, token, region)
    if webhooksExport:
        return config.writeToJsonFile(webhooksExport, config.localFolder + '/' + folder + '/' + config.fileNames['webhooks'])
    cma.logging.error('Missing webhooks response from Contentstack.')
    return False
