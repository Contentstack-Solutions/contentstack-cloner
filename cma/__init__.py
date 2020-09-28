'''
Contentstack's Content Management API Python wrapper
https://www.contentstack.com/docs/developers/apis/content-management-api/
oskar.eiriksson@contentstack.com
2020-06-05

Content Management Collection of Functions
'''
import os
import logging
import requests
import config


logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)

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
    logging.debug(res.json())
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

def printError(res, fName, msg=None):
    '''
    Custom function - Printing out the error when something fails
    '''
    try:
        httpStatus = res.status_code
    except Exception:
        httpStatus = 'N/A'
    try:
        resText = res.text
    except Exception:
        resText = 'N/A'
    logging.error('Error: ' + str(httpStatus) + ' - Response Text: ' + resText + ' - Function Name: ' + fName + ' - Message: ' + str(msg))
    return {
        'http_status': httpStatus,
        'response_text': resText,
        'function_name': fName,
        'message': msg
    }

def logUrl(url):
    logging.debug('-------')
    logging.debug('The CMA URL:')
    logging.debug(url)
    logging.debug('-------')

def getAllContentTypes(apiKey, token, region):
    '''
    Gets all content types, includes the count of content types and global field schema
    sample url: https://api.contentstack.io/v3/content_types?include_count={boolean_value}&include_global_field_schema={boolean_value}

    Limitation: This has not been tested on content models with over 100 content types.
    '''
    url = '{region}v3/content_types?include_count=true&include_global_field_schema=true'.format(region=region)
    header = constructAuthTokenHeader(token, apiKey)
    logUrl(url)
    res = requests.get(url, headers=header)
    if res.status_code == 200:
        logging.debug(res.json())
        return res.json()
    print(printError(res, getAllContentTypes.__name__))
    return None

def getAllEntries(stackInfo, contentType, language, token):
    '''
    Get All Entries using the CMA.
    sample url: https://api.contentstack.io/v3/content_types/{content_type_uid}/entries?locale={language_code}&include_workflow=true&include_publish_details=true&include_count=true
    '''
    header = constructAuthTokenHeader(token, stackInfo['apiKey'])
    result = []
    skip = 0
    count = 1 # Just making sure we check at least once. Setting the real count value in while loop
    while skip <= count:
        url = url = '{}v3/content_types/{}/entries?skip={}&locale{}&include_workflow=true&include_publish_details=true&include_count=true'.format(stackInfo['region'], contentType, skip, language)
        logUrl(url)
        res = requests.get(url, headers=header)
        if res.status_code == 200:
            count = res.json()['count'] # Setting the real value of count here
            result = result + res.json()['entries']
            skip += 100
            logging.debug('Result as of now: {}'.format(result))
        else:
            logging.error('{}All Entries Export: Failed getting entries for Content Type {} in language {}{}'.format(config.RED, contentType, language, config.END))
            logging.error('{}Error Message: {}{}'.format(config.RED, res.text, config.END))
            return None
    if result:
        return {'entries': result}
    logging.info('No Entries in content type and language {} - {}'.format(contentType, language))
    return None

def getAllGlobalFields(apiKey, token, region):
    '''
    Gets all Global Fields
    sample url: https://api.contentstack.io/v3/global_fields

    Limitation: This has not been tested on stack with over 100 global fields.
    '''
    url = '{}v3/global_fields?include_count=true'.format(region)
    logUrl(url)
    header = constructAuthTokenHeader(token, apiKey)
    res = requests.get(url, headers=header)
    if res.status_code == 200:
        logging.debug(res.json())
        return res.json()
    print(printError(res, getAllGlobalFields.__name__))
    return None

def getAllExtensions(apiKey, token, region):
    '''
    Gets all extensions
    sample url: https://api.contentstack.io/v3/extensions

    Limitation: This has not been tested on stack with over 100 extensions.
    '''
    url = '{region}v3/extensions?include_count=true'.format(region=region)
    logUrl(url)
    header = constructAuthTokenHeader(token, apiKey)
    res = requests.get(url, headers=header)
    if res.status_code == 200:
        logging.debug(res.json())
        return res.json()
    print(printError(res, getAllExtensions.__name__))
    return None

def getAllWorkflows(apiKey, token, region):
    '''
    Gets all workflows
    sample url: https://api.contentstack.io/v3/workflows/

    Limitation: This has not been tested on stack with over 100 workflows
    '''
    url = '{region}v3/workflows?include_count=true'.format(region=region)
    logUrl(url)
    header = constructAuthTokenHeader(token, apiKey)
    res = requests.get(url, headers=header)
    if res.status_code == 200:
        logging.debug(res.json())
        return res.json()
    print(printError(res, getAllWorkflows.__name__))
    return None

def getAllPublishingRules(contentTypeUids, apiKey, token, region):
    '''
    Gets all publishing rules
    sample url: https://api.contentstack.io/v3/workflows/publishing_rules?content_types=[{content_type_uid}]&limit={rule_limit}&include_count={boolean_value}

    contentTypeUids is an array of all content type uids
    Limitation: This has not been tested on stack with over 100 publishing rules
    '''
    uids = ','.join(map(str, contentTypeUids))
    url = '{region}v3/workflows/publishing_rules?{uids}&include_count=true'.format(region=region, uids=uids)
    logUrl(url)
    header = constructAuthTokenHeader(token, apiKey)
    res = requests.get(url, headers=header)
    if res.status_code == 200:
        logging.debug(res.json())
        return res.json()
    print(printError(res, getAllPublishingRules.__name__))
    return None

def getAllLabels(apiKey, token, region):
    '''
    Gets all labels
    sample url: https://api.contentstack.io/v3/labels?include_count={boolean_value}

    Limitation: This has not been tested on stack with over 100 labels
    '''
    url = '{region}v3/labels?include_count=true'.format(region=region)
    logUrl(url)
    header = constructAuthTokenHeader(token, apiKey)
    res = requests.get(url, headers=header)
    if res.status_code == 200:
        logging.debug(res.json())
        return res.json()
    print(printError(res, getAllLabels.__name__))
    return None

def getAllLanguages(apiKey, token, region):
    '''
    Gets all languages
    sample url: https://api.contentstack.io/v3/locales?include_count={boolean_value}
    '''
    url = '{region}v3/locales?include_count=true'.format(region=region)
    logUrl(url)
    header = constructAuthTokenHeader(token, apiKey)
    res = requests.get(url, headers=header)
    if res.status_code == 200:
        logging.debug(res.json())
        return res.json()
    print(printError(res, getAllLanguages.__name__))
    return None

def getAllEnvironments(apiKey, token, region):
    '''
    Gets all environments
    sample url: https://api.contentstack.io/v3/environments?include_count={boolean_value}&asc={field_uid}&desc={field_uid}
    '''
    url = '{region}v3/environments?include_count=true'.format(region=region)
    logUrl(url)
    header = constructAuthTokenHeader(token, apiKey)
    res = requests.get(url, headers=header)
    if res.status_code == 200:
        logging.debug(res.json())
        return res.json()
    print(printError(res, getAllEnvironments.__name__))
    return None

def getAllDeliveryTokens(apiKey, token, region):
    '''
    Gets all delivery tokens
    sample url: https://api.contentstack.io/v3/stacks/delivery_tokens
    Needs auth token instead of management token
    '''
    url = '{region}v3/stacks/delivery_tokens?include_count=true'.format(region=region)
    logUrl(url)
    header = constructAuthTokenHeader(token, apiKey)
    res = requests.get(url, headers=header)
    if res.status_code == 200:
        logging.debug(res.json())
        return res.json()
    print(res)
    print(printError(res, getAllDeliveryTokens.__name__))
    return None

def getAllRoles(apiKey, token, region):
    '''
    Gets all roles
    sample url: https://api.contentstack.io/v3/roles?include_permissions={boolean_value}&include_rules={boolean_value}
    '''
    url = '{region}v3/roles?include_permissions=true&include_rules=true&include_count=true'.format(region=region)
    logUrl(url)
    header = constructAuthTokenHeader(token, apiKey)
    res = requests.get(url, headers=header)
    if res.status_code == 200:
        logging.debug(res.json())
        return res.json()
    print(printError(res, getAllRoles.__name__))
    return None

def getAllWebhooks(apiKey, token, region):
    '''
    Gets all webhooks
    sample url: https://api.contentstack.io/v3/webhooks
    '''
    url = '{region}v3/webhooks?include_count=true'.format(region=region)
    logUrl(url)
    header = constructAuthTokenHeader(token, apiKey)
    res = requests.get(url, headers=header)
    if res.status_code == 200:
        logging.debug(res.json())
        return res.json()
    print(printError(res, getAllWebhooks.__name__))
    return None

def getAllStacks(header, orgUid, region):
    '''
    Gets all stacks from an organization
    sample url: https://api.contentstack.io/v3/stacks
    '''
    header['organization_uid'] = orgUid
    url = '{}v3/stacks'.format(region)
    res = requests.get(url, headers=header)
    logging.debug(res.json())
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
    logging.debug(res.json())
    return res.json()

def typicalCreate(apiKey, authToken, body, url, endpointName=''):
    '''
    Combining identical POST methods into one
    '''
    logUrl(url)
    header = constructAuthTokenHeader(authToken, apiKey)
    res = requests.post(url, headers=header, json=body)
    if res.status_code in (200, 201):
        return res.json()
    if 'name' in body[endpointName]:
        name = body[endpointName]['name']
    elif 'title' in body[endpointName]:
        name = body[endpointName]['title']
    else:
        name = 'noName'
    logging.error('{}Failed creating {} (Name: {}) - {}{}'.format(config.RED, endpointName, name, str(res.text), config.END))
    return None

def typicalUpdate(apiKey, authToken, body, url, endpointName=''):
    '''
    Combining identical PUT methods into one
    '''
    logUrl(url)
    header = constructAuthTokenHeader(authToken, apiKey)
    res = requests.put(url, headers=header, json=body)
    if res.status_code == 200:
        return res.json()
    logging.error('{}Failed updating {} - {}{}'.format(config.RED, endpointName, str(res.text), config.END))
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
