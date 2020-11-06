'''
Contentstack's Content Management API Python wrapper
https://www.contentstack.com/docs/developers/apis/content-management-api/
oskar.eiriksson@contentstack.com
2020-09-28
'''
import os
from time import sleep
import requests
import config

regionMap = {
    'US': 'https://api.contentstack.io/',
    'us': 'https://api.contentstack.io/',
    'EU': 'https://eu-api.contentstack.com/',
    'eu': 'https://eu-api.contentstack.com/'
}

def login(username, password, region):
    url = '{region}v3/user-session'.format(region=region)
    body = {
        'user': {
            'email': username,
            'password': password,
            }
        }
    res = requests.post(url, json=body)
    config.logging.debug(res.json())
    return res.status_code, res.json()

def constructAuthTokenHeader(token, apiKey=None):
    '''
    Simple function creating the correct header for authentication vs the API
    '''
    header = {
        'Content-Type': 'application/json',
        'authtoken': token
    }
    if apiKey:
        header['api_key'] = apiKey
    return header

def logUrl(url):
    '''
    Logging out for debug purposes the constructed URL for any function
    '''
    config.logging.debug('-------')
    config.logging.debug('The CMA URL:')
    config.logging.debug(url)
    config.logging.debug('-------')

def getUserInfo(authToken, region):
    '''
    Get information about logged in user
    Used also to validate that authToken works
    '''
    url = '{}v3/user'.format(region)
    logUrl(url)
    header = constructAuthTokenHeader(authToken)
    res = requests.get(url, headers=header)
    if res.status_code in (200, 201):
        return res.json()
    config.logging.error('{}Unable to get user info. Eror Message: {}{}'.format(config.RED, res.text, config.END))
    return None

def logError(endpointName, name, url, res):
    config.logging.error('{}Failed creating/updating {} (Name: {}){}'.format(config.RED, endpointName, name, config.END))
    config.logging.error('{}URL: {}{}'.format(config.RED, url, config.END))
    config.logging.error('{}HTTP Status Code: {}{}'.format(config.RED, res.status_code, config.END))
    config.logging.error('{red}Error Message: {txt}{end}'.format(red=config.RED, txt=res.text, end=config.END))
    return None

def iterateURL(url, skip=0):
    return url + '&skip={}'.format(skip)

def typicalGetSimple(url, apiKey, authToken, environment=None):
    '''
    Re-usable function to GET objects that never include more than 100 items
    '''
    header = constructAuthTokenHeader(authToken, apiKey)
    if environment:
        url = url + '&environment={}'.format(environment)
    logUrl(url)
    res = requests.get(url, headers=header)
    if res.status_code in (200, 201):
        config.logging.debug('Result: {}'.format(res.json()))
        return res.json()
    config.logging.error('{red}Export failed.{end}'.format(red=config.RED, end=config.END))
    config.logging.error('{}URL: {}{}'.format(config.RED, url, config.END))
    config.logging.error('{}HTTP Status Code: {}{}'.format(config.RED, res.status_code, config.END))
    config.logging.error('{red}Error Message: {txt}{end}'.format(red=config.RED, txt=res.text, end=config.END))
    return None

def typicalGetIterate(url, apiKey, authToken, dictKey, environment=None):
    '''
    Re-usable function to GET objects that might have more than 100 items in it
    '''
    header = constructAuthTokenHeader(authToken, apiKey)
    result = []
    skip = 0
    count = 1 # Just making sure we check at least once. Setting the real count value in while loop
    if environment:
        url = url + '&environment={}'.format(environment)
    originalURL = url
    while skip <= count:
        url = iterateURL(originalURL, skip)
        logUrl(url)
        res = requests.get(url, headers=header)
        if res.status_code in (200, 201):
            if 'count' in res.json(): # Did get a KeyError once... when there was nothing there.
                count = res.json()['count'] # Setting the real value of count here
            else:
                count = 0
            config.logging.debug('{}Response Now: {} {}'.format(config.YELLOW, res.json(), config.END))
            result = result + res.json()[dictKey]
            config.logging.debug('{}Result as of Now: {} {}'.format(config.YELLOW, result, config.END))
            skip += 100
        else:
            config.logging.error('{red}All {key} Export: Failed getting {key}{end}'.format(red=config.RED, key=dictKey, end=config.END))
            config.logging.error('{}URL: {}{}'.format(config.RED, url, config.END))
            config.logging.error('{}HTTP Status Code: {}{}'.format(config.RED, res.status_code, config.END))
            config.logging.error('{red}Error Message: {txt}{end}'.format(red=config.RED, txt=res.text, end=config.END))
            return None
    if result:
        return {dictKey: result}
    config.logging.info('No {} results'.format(dictKey))
    return None

def typicalCreate(apiKey, authToken, body, url, endpointName='', retry=False):
    '''
    Combining identical POST methods into one
    '''
    logUrl(url)
    header = constructAuthTokenHeader(authToken, apiKey)
    res = requests.post(url, headers=header, json=body)
    if res.status_code in (200, 201):
        return res.json()
    elif (res.status_code == 429) and not retry:
        config.logging.warning('{}We are getting rate limited. Retrying in 2 seconds.{}'.format(config.YELLOW, config.END))
        sleep(2) # We'll retry once in a second if we're getting rate limited.
        return typicalCreate(apiKey, authToken, body, url, endpointName, True)
    if 'name' in body[endpointName]:
        name = body[endpointName]['name']
    elif 'title' in body[endpointName]:
        name = body[endpointName]['title']
    else:
        name = 'noName'
    return logError(endpointName, name, url, res)

def typicalUpdate(apiKey, authToken, body, url, endpointName='', retry=False):
    '''
    Combining identical PUT methods into one
    '''
    logUrl(url)
    header = constructAuthTokenHeader(authToken, apiKey)
    res = requests.put(url, headers=header, json=body)
    if res.status_code in (200, 201):
        return res.json()
    elif (res.status_code == 429) and not retry:
        config.logging.warning('{}We are getting rate limited. Retrying in 2 seconds.{}'.format(config.YELLOW, config.END))
        sleep(2) # We'll retry once in a second if we're getting rate limited.
        return typicalUpdate(apiKey, authToken, body, url, endpointName, True)
    config.logging.error('{}Failed updating {} - {}{}'.format(config.RED, endpointName, str(res.text), config.END))
    return logError(endpointName, '', url, res) # Empty string was name variable

def getAllContentTypes(apiKey, token, region):
    '''
    Gets all content types, includes the count of content types and global field schema
    sample url: https://api.contentstack.io/v3/content_types?include_count={boolean_value}&include_global_field_schema={boolean_value}
    '''
    url = '{region}v3/content_types?include_count=true&include_global_field_schema=true'.format(region=region)
    return typicalGetIterate(url, apiKey, token, 'content_types')

def getAllEntries(stackInfo, contentType, language, token, environment=None):
    '''
    Get All Entries (Content Management API).
    sample url: https://api.contentstack.io/v3/content_types/{content_type_uid}/entries?locale={language_code}&include_workflow=true&include_publish_details=true&include_count=true
    '''
    url = '{region}v3/content_types/{contentType}/entries?locale={language}&include_workflow=true&include_publish_details=true&include_count=true'.format(region=stackInfo['region'], contentType=contentType, language=language)
    return typicalGetIterate(url, stackInfo['apiKey'], token, 'entries', environment)

def getSingleEntry(stackInfo, contentType, language, token, uid, environment=None):
    '''
    Get a Single Entry (Content Management API).
    sample url: https://api.contentstack.io/v3/content_types/{content_type_uid}/entries/{entry_uid}?locale={language_code}&include_workflow=true&include_publish_details=true&include_count=true
    '''
    url = '{region}v3/content_types/{contentType}/entries/{uid}?locale={language}&include_workflow=true&include_publish_details=true&include_count=true'.format(region=stackInfo['region'], contentType=contentType, uid=uid, language=language)
    return typicalGetSimple(url, stackInfo['apiKey'], token)

def getEntryLocales(stackInfo, contentType, uid, token):
    '''
    Gets a single entry and returns all the locales that entry is available in
    sample url: https://api.contentstack.io/v3/content_types/{content_type_uid}/entries/{entry_uid}/locales
    Only done once for every entry, when getting the master locale - so we know what languages to fetch from after that.
    '''
    url = '{region}v3/content_types/{contentType}/entries/{uid}/locales'.format(region=stackInfo['region'], contentType=contentType, uid=uid)
    # Returns: {'locales': [{'code': 'nl-nl'}, {'code': 'nl-be'}, {'code': 'mr-in'}, {'code': 'en-si'}, {'code': 'en-ch'}, {'code': 'ar-iq'}, {'code': 'ar'}, {'code': 'af-za'}, {'code': 'ms-sg'}, {'code': 'is-is', 'localized': True}, {'code': 'en-us'}]}
    return typicalGetSimple(url, stackInfo['apiKey'], token)

def getAllAssets(stackInfo, token, environment):
    '''
    Get All Assets (Content Management API)
    sample url: https://api.contentstack.io/v3/assets?include_folders=true&include_publish_details=true&include_count=true&relative_urls=false&environment={environment}&query={"is_dir": False}
    '''
    url = '{region}v3/assets?include_folders=true&include_publish_details=true&include_count=true&relative_urls=false&query={{"is_dir": false}}'.format(region=stackInfo['region'])
    return typicalGetIterate(url, stackInfo['apiKey'], token, 'assets', environment)


def getAllFolders(stackInfo, token):
    '''
    Get all Folders
    sample url: https://api.contentstack.io/v3/assets?query={"is_dir": true}&include_count=true
    '''
    url = '{}v3/assets?query={{"is_dir": true}}&include_count=true'.format(stackInfo['region'])
    return typicalGetIterate(url, stackInfo['apiKey'], token, 'assets') #(url, apiKey, authToken, dictKey, environment=None):

def getAllGlobalFields(apiKey, token, region):
    '''
    Gets all Global Fields
    sample url: https://api.contentstack.io/v3/global_fields

    Limitation: This has not been tested on stack with over 100 global fields.
    '''
    url = '{}v3/global_fields?include_count=true'.format(region)
    return typicalGetIterate(url, apiKey, token, 'global_fields') #(url, apiKey, authToken, dictKey, environment=None):

def getAllExtensions(apiKey, token, region):
    '''
    Gets all extensions
    sample url: https://api.contentstack.io/v3/extensions
    '''
    url = '{region}v3/extensions?include_count=true'.format(region=region)
    return typicalGetIterate(url, apiKey, token, 'extensions')

def getAllWorkflows(apiKey, token, region):
    '''
    Gets all workflows
    sample url: https://api.contentstack.io/v3/workflows/
    Limitation: Using simple get without iteration because it sometimes fails using the iterate one where there are no workflows. I do not know why.
    '''
    url = '{region}v3/workflows?include_count=true'.format(region=region)
    typicalGetSimple(url, apiKey, token)
    # return typicalGetIterate(url, apiKey, token, 'workflows')

def getAllPublishingRules(contentTypeUids, apiKey, token, region):
    '''
    Gets all publishing rules
    sample url: https://api.contentstack.io/v3/workflows/publishing_rules?content_types=[{content_type_uid}]&limit={rule_limit}&include_count={boolean_value}

    contentTypeUids is an array of all content type uids
    Limitation: This has not been tested on stack with over 100 publishing rules
    '''
    uids = ','.join(map(str, contentTypeUids))
    url = '{region}v3/workflows/publishing_rules?{uids}&include_count=true'.format(region=region, uids=uids)
    return typicalGetIterate(url, apiKey, token, 'publishing_rules')

def getAllLabels(apiKey, token, region):
    '''
    Gets all labels
    sample url: https://api.contentstack.io/v3/labels?include_count={boolean_value}

    Limitation: This has not been tested on stack with over 100 labels
    '''
    url = '{region}v3/labels?include_count=true'.format(region=region)
    return typicalGetIterate(url, apiKey, token, 'labels')

def getAllLanguages(apiKey, token, region):
    '''
    Gets all languages
    sample url: https://api.contentstack.io/v3/locales?include_count={boolean_value}
    '''
    url = '{region}v3/locales?include_count=true'.format(region=region)
    return typicalGetIterate(url, apiKey, token, 'locales')

def getAllEnvironments(apiKey, token, region):
    '''
    Gets all environments
    sample url: https://api.contentstack.io/v3/environments?include_count={boolean_value}&asc={field_uid}&desc={field_uid}
    '''
    url = '{region}v3/environments?include_count=true'.format(region=region)
    return typicalGetIterate(url, apiKey, token, 'environments')

def getAllDeliveryTokens(apiKey, token, region):
    '''
    Gets all delivery tokens
    sample url: https://api.contentstack.io/v3/stacks/delivery_tokens
    Needs auth token instead of management token
    '''
    url = '{region}v3/stacks/delivery_tokens?include_count=true'.format(region=region)
    return typicalGetIterate(url, apiKey, token, 'tokens')

def getAllRoles(apiKey, token, region):
    '''
    Gets all roles
    sample url: https://api.contentstack.io/v3/roles?include_permissions={boolean_value}&include_rules={boolean_value}
    '''
    url = '{region}v3/roles?include_permissions=true&include_rules=true&include_count=true'.format(region=region)
    return typicalGetIterate(url, apiKey, token, 'roles')

def getAllWebhooks(apiKey, token, region):
    '''
    Gets all webhooks
    sample url: https://api.contentstack.io/v3/webhooks
    '''
    url = '{region}v3/webhooks?include_count=true'.format(region=region)
    return typicalGetIterate(url, apiKey, token, 'webhooks')

def getAllStacks(header, orgUid, region):
    '''
    Gets all stacks from an organization
    sample url: https://api.contentstack.io/v3/stacks
    '''
    header['organization_uid'] = orgUid
    url = '{}v3/stacks'.format(region)
    res = requests.get(url, headers=header)
    config.logging.debug(res.json())
    return res.json()

def createStack(token, orgUid, region, body):
    '''
    Creates a stack in an organization
    sample url: https://api.contentstack.io/v3/stacks
    '''
    header = {
        'authtoken': token,
        'organization_uid': orgUid,
        'Content-Type': 'application/json'
    }
    url = '{}v3/stacks'.format(region)
    res = requests.post(url, headers=header, json=body)
    if res.status_code in (200, 201):
        url = '{}#!/stack/{}/dashboard'.format(region.replace('-api.','-app.'), res.json()['stack']['api_key']) ### Direct LINK to it on this format: https://eu-app.contentstack.com/#!/stack/blt95fffae23f35168a/dashboard
        config.logging.info('Stack (Name: {}) successfully created'.format(body['stack']['name']))
        config.logging.info('{}Direct Link to Stack: {}{}'.format(config.GREEN, url, config.END))
        return res.json()
    config.logging.error('{}Error creating stack.{}'.format(config.RED, config.END))
    config.logging.error('{}HTTP Status: {}{}'.format(config.RED, res.status_code, config.END))
    config.logging.error('{}Error Message: {}{}'.format(config.RED, res.text, config.END))
    return None

def createLanguage(apiKey, authToken, body, region):
    '''
    Creates a language
    sample url: https://api.contentstack.io/v3/locales
    '''
    url = '{}v3/locales'.format(region)
    return typicalCreate(apiKey, authToken, body, url, 'locale')

def createLabel(apiKey, authToken, body, region):
    '''
    Creates a label
    sample url: https://api.contentstack.io/v3/labels
    '''
    url = '{}v3/labels'.format(region)
    return typicalCreate(apiKey, authToken, body, url, 'label')

def createRole(apiKey, authToken, body, region):
    '''
    Creates a role
    sample url: https://api.contentstack.io/v3/roles
    '''
    url = '{}v3/roles'.format(region)
    return typicalCreate(apiKey, authToken, body, url, 'role')

def updateRole(apiKey, authToken, body, region, currentRoles):
    '''
    Updates a role
    sample url: https://api.contentstack.io/v3/roles?include_permissions=false&include_rules=false
    '''
    currentUid = currentRoles[body['role']['name']]
    if 'uid' in body['role']: # Just to be sure - No need to have the old uid in the request
        body['role'].pop('uid')
    url = '{}v3/roles/{}'.format(region, currentUid)
    return typicalUpdate(apiKey, authToken, body, url, 'role')

def createEnvironment(apiKey, authToken, body, region):
    '''
    Creates an environment
    sample url: https://api.contentstack.io/v3/environments
    '''
    url = '{}v3/environments'.format(region)
    return typicalCreate(apiKey, authToken, body, url, 'environment')

def createGlobalField(apiKey, authToken, body, region):
    '''
    Creates a global field
    sample url: https://api.contentstack.io/v3/global_fields
    '''
    url = '{}v3/global_fields'.format(region)
    return typicalCreate(apiKey, authToken, body, url, 'global_field')

def createExtension(apiKey, authToken, body, region):
    '''
    Creates an extension
    sample url: https://api.contentstack.io/v3/extensions/
    '''
    url = '{}v3/extensions'.format(region)
    return typicalCreate(apiKey, authToken, body, url, 'extension')

def createContentType(apiKey, authToken, body, region):
    '''
    Creates a content type
    sample url: https://api.contentstack.io/v3/content_types
    '''
    url = '{}v3/content_types'.format(region)
    return typicalCreate(apiKey, authToken, body, url, 'content_type')

def createDeliveryToken(apiKey, authToken, body, region):
    '''
    Creates a delivery token
    sample url: https://api.contentstack.io/v3/stacks/delivery_tokens
    '''
    url = '{}v3/stacks/delivery_tokens'.format(region)
    return typicalCreate(apiKey, authToken, body, url, 'token')

def createWorkflow(apiKey, authToken, body, region):
    '''
    Creates a workflow
    sample url: https://api.contentstack.io/v3/workflows
    '''
    url = '{}v3/workflows'.format(region)
    return typicalCreate(apiKey, authToken, body, url, 'workflow')

def createPublishingRule(apiKey, token, body, region):
    '''
    Creates a publishing rule
    sample url: https://api.contentstack.io/v3/workflows/publishing_rules
    '''
    url = '{}v3/workflows/publishing_rules'.format(region)
    return typicalCreate(apiKey, token, body, url, 'publishing_rule')

def createWebhook(apiKey, token, body, region):
    '''
    Creates a webook
    sample url: https://api.contentstack.io/v3/webhooks
    '''
    url = '{}v3/webhooks'.format(region)
    return typicalCreate(apiKey, token, body, url, 'webhook')

def createFolder(apiKey, token, region, folderName, parentFolder=None):
    '''
    Creates an asset folder
    sample url: https://api.contentstack.io/v3/assets/folders/
    '''
    url = '{}v3/assets/folders'.format(region)
    body = {'asset': {'name': folderName}}
    if parentFolder:
        body['asset']['parent_uid'] = parentFolder
    return typicalCreate(apiKey, token, body, url, 'asset')

def createAsset(region, authToken, apiKey, filePath, metaData, filename):
    '''
    Upload Image/Asset
    sample url: https://cdn.contentstack.io/v3/assets?relative_urls=false
    '''
    url = '{}v3/assets?relative_urls=false'.format(region)
    contentTypeMeta = metaData['asset']['content_type']
    header = constructAuthTokenHeader(authToken, apiKey)
    del header['Content-Type']
    with open(filePath, 'rb') as f:
        fileData = f.read()
    files = {"asset[upload]": (filename, fileData, contentTypeMeta)}
    payload = {}
    if 'parent_uid' in metaData['asset']:
        payload["asset[parent_uid]"] = (metaData['asset']['parent_uid'])
    if 'description' in metaData['asset']:
        payload["asset[description]"] = (metaData['asset']['description'])
    if 'title' in metaData['asset']:
        payload["asset[title]"] = (metaData['asset']['title'])
    if 'tags' in metaData['asset']:
        payload["asset[tags]"] = (metaData['asset']['tags'])
    res = requests.post(url, files=files, data=payload, headers=header)
    if res.status_code in (200, 201):
        config.logging.info('Asset Uploaded. ({})'.format(filename))
        return res.json()
    return logError('asset', filename, url, res)

def createEntry(apiKey, token, body, region, contentType, language):
    '''
    Creating an entry
    sample url: https://api.contentstack.io/v3/content_types/{content_type_uid}/entries?locale={locale_code}
    '''
    url = '{}v3/content_types/{}/entries?locale={}'.format(region, contentType, language)
    return typicalCreate(apiKey, token, {'entry': body}, url, 'entry')

def updateEntry(apiKey, token, body, region, contentType, language, uid):
    '''
    Updating an entry
    sample url: https://api.contentstack.io/v3/content_types/{content_type_uid}/entries/{entry_uid}?locale={locale_code}
    '''
    url = '{}v3/content_types/{}/entries/{}?locale={}'.format(region, contentType, uid, language)
    return typicalUpdate(apiKey, token, {'entry': body}, url, 'entry')
