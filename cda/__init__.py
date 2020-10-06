'''
Contentstack's Content Delivery API Python wrapper
https://www.contentstack.com/docs/developers/apis/content-delivery-api/
oskar.eiriksson@contentstack.com
2020-09-28
'''
import os
import requests
import config
from cma import iterateURL

regionMap = {
    'US': 'https://cdn.contentstack.io/',
    'us': 'https://cdn.contentstack.io/',
    'EU': 'https://eu-cdn.contentstack.com/',
    'eu': 'https://eu-cdn.contentstack.com/'
}

def logUrl(url):
    config.logging.debug('-------')
    config.logging.debug('The CDA URL:')
    config.logging.debug(url)
    config.logging.debug('-------')

def constructDeliveryTokenHeader(deliveryToken, apiKey):
    '''
    Constructing header
    '''
    header = {
        'api_key': apiKey,
        'access_token': deliveryToken
    }
    return header


def typicalGetIterate(url, apiKey, deliveryToken, dictKey):
    '''
    Re-usable function to GET objects that might have more than 100 items in it
    '''
    header = constructDeliveryTokenHeader(deliveryToken, apiKey)
    result = []
    skip = 0
    count = 1 # Just making sure we check at least once. Setting the real count value in while loop
    originalURL = url
    while skip <= count:
        url = iterateURL(originalURL, skip)
        logUrl(url)
        res = requests.get(url, headers=header)
        if res.status_code in (200, 201):
            count = res.json()['count'] # Setting the real value of count here
            result = result + res.json()[dictKey]
            skip += 100
            config.logging.debug('Result as of now: {}'.format(result))
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

def getAllEntries(stackInfo, contentType, language, environment, token):
    '''
    Get all published entries on environment in a specific language
    sample url: https://cdn.contentstack.io/v3/content_types/{content_type_uid}/entries?skip=0&environment={environment_name}&locale={locale_code}&include_count=true
    '''
    url = '{region}v3/content_types/{contentType}/entries?locale={language}&environment={environment}&include_workflow=true&include_publish_details=true&include_count=true'.format(region=stackInfo['region'], contentType=contentType, language=language, environment=environment)
    return typicalGetIterate(url, stackInfo['apiKey'], token, 'entries')

def getAllAssets(stackInfo, deliveryToken, environment):
    '''
    Get all assets published on environment
    sample url: https://cdn.contentstack.io/v3/assets?environment={environment_name}&relative_urls={boolean_value}&include_dimension={boolean_value}
    '''
    url = '{region}v3/assets?environment={environment}&relative_urls=false&include_dimension=true&include_count=true'.format(region=stackInfo['region'], environment=environment)
    return typicalGetIterate(url, stackInfo['apiKey'], deliveryToken, 'assets')
