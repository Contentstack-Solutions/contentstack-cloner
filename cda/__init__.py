'''
Contentstack's Content Delivery API Python wrapper
https://www.contentstack.com/docs/developers/apis/content-delivery-api/
oskar.eiriksson@contentstack.com
2020-09-28

Prerequisites:

- You'll need to have Python 3
- You need to install the requests library:
        -- Run: `pip install requests`
'''
import os
import requests
import config
import cma

regionMap = {
    'US': 'https://cdn.contentstack.io/',
    'us': 'https://cdn.contentstack.io/',
    'EU': 'https://eu-cdn.contentstack.com/',
    'eu': 'https://eu-cdn.contentstack.com/'
}

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
    cma.logging.error('Error: ' + str(httpStatus) + ' - Response Text: ' + resText + ' - Function Name: ' + fName + ' - Message: ' + str(msg))
    return {
        'http_status': httpStatus,
        'response_text': resText,
        'function_name': fName,
        'message': msg
    }

def logUrl(url):
    cma.logging.debug('-------')
    cma.logging.debug('The CDA URL:')
    cma.logging.debug(url)
    cma.logging.debug('-------')

def getAllEntries(stackInfo, contentType, language, environment, token):
    '''
    Get all published entries on environment in a specific language
    sample url: https://cdn.contentstack.io/v3/content_types/{content_type_uid}/entries?skip=0&environment={environment_name}&locale={locale_code}&include_count=true
    '''
    header = {
        'api_key': stackInfo['apiKey'],
        'access_token': token
    }
    result = []
    skip = 0
    count = 1 # Just making sure we check at least once. Setting the real count value in while loop
    while skip <= count:
        url = '{region}v3/content_types/{contentType}/entries?skip={skip}&environment={environment}&locale={language}&include_count=true'.format(region=stackInfo['region'], contentType=contentType, skip=skip, environment=environment, language=language)
        logUrl(url)
        res = requests.get(url, headers=header)
        if res.status_code == 200:
            count = res.json()['count'] # Setting the real value of count here
            result = result + res.json()['entries']
            skip += 100
            cma.logging.debug('Result as of now: {}'.format(result))
        else:
            cma.logging.error('{}Failed getting entries for Content Type {} in language {} on environment {}{}'.format(config.RED, contentType, language, environment, config.END))
            cma.logging.error('{}Error Message: {}{}'.format(config.RED, res.text, config.END))
            return None
    if result:
        return {'entries': result}
    cma.logging.info('No Entries in content type and language {} - {}'.format(contentType, language))
    return None
