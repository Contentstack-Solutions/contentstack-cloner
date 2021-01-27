'''
oskar.eiriksson@contentstack.com
2020-09-28

Various config functions and variables user in both export and import scripts
'''
import os
from time import sleep
from datetime import datetime
import json
import logging
import inquirer
import requests
import cma

def readDirIfExists(folder):
    '''
    Checks if folder exists, Returns empty array if not
    '''
    if os.path.isdir(folder):
        return os.listdir(folder)
    return []

def checkDir(folder):
    '''
    Checks if folder exists - Creates one if not
    '''
    if not os.path.exists(folder):
        logging.info('Creating folder: ' + folder)
        os.makedirs(folder)
        return True
    return False

def getTime():
    now = datetime.now()
    return now.strftime("%d-%m-%Y-%H-%M-%S")

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

disableWebhooks = True # All enabled webhooks are disabled on import if TRUE. Minimizing the risk of triggering webhooks and messing with live environments.
dataRootFolder = 'data/' # Relative path to the export root folder - Remember the slash at the end if you change this.
stackRootFolder = 'stacks/' # Relative path under the dataRootFolder for stack exports
mapperFolder = 'importJobs_UidMappers/' # The folder where mappers-jobs folders are stored - under the stackRootFolder
# exportLoginFile = 'exportLogin.json' # Placed in the project root folder
authTokenFile = 'authtoken.json'
exportReportFile = 'report.json' # Placed in the stack export root folder
logLevel = logging.INFO # Possible levels e.g.: DEBUG, ERROR, INFO
logFolder = 'log/'
logFile = getTime()
checkDir(logFolder)
# logging.basicConfig(filename=logFile, filemode='a', format='%(asctime)s:%(levelname)s:%(message)s', level=logLevel)

logFormatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
logging.basicConfig(level=logLevel)
rootLogger = logging.getLogger()

fileHandler = logging.FileHandler("{0}/{1}.log".format(logFolder, logFile))
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

'''
Possibly replacing the regionMap variables with this one
'''
# regionMap = {
#     'delivery': {
#         'US': '',
#         'us': '',
#         'EU': '',
#         'eu': ''
#     },
#     'management': {
#         'US': '',
#         'us': '',
#         'EU': '',
#         'eu': ''
#     }
# }

# Folder/Directory definitions for all exports. Used to decide a folder and to validate that everything was exported correctly.
folderNames = {
    'contentTypes': 'contentTypes/',
    'deliveryTokens': 'deliveryTokens/',
    'environments': 'environments/',
    'extensions': 'extensions/',
    'globalFields': 'globalFields/',
    'labels': 'labels/',
    'languages': 'languages/',
    'publishingRules': 'publishingRules/',
    'roles': 'roles/',
    'webhooks': 'webhooks/',
    'workflows': 'workflows/',
    'entries': 'entries/',
    'assets': 'assets/',
    'folders': 'assets/'
}
# Filename definitions for all exports. Used to decide filename and to validate that everything was exported correctly.
fileNames = {
    'contentTypes': 'content_types.json',
    'deliveryTokens': 'delivery_tokens.json',
    'environments': 'environments.json',
    'extensions': 'extensions.json',
    'globalFields': 'global_fields.json',
    'labels': 'labels.json',
    'languages': 'languages.json',
    'publishingRules': 'publishing_rules.json',
    'roles': 'roles.json',
    'webhooks': 'webhooks.json',
    'workflows': 'workflows.json',
    'entries': 'entries.json',
    'assets': 'assets.json',
    'folders': 'folders.json'
}

# Text formatting for terminal logs.
PURPLE = '\033[95m'
CYAN = '\033[96m'
DARKCYAN = '\033[36m'
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
WHITE = '\033[0;37m'
REDBG = '\033[0;41m'
GREENBG = '\033[0;42m'
END = '\033[0m'

def createFolder(name):
    '''
    Creates an export folder with name
    '''
    cont = [inquirer.Text('folderName', message="{}Give the export folder a name:{}".format(BOLD, END), default=name + ' - ' + getTime())]
    folderName = inquirer.prompt(cont)['folderName'] + '/'
    return folderName

def defineFullFolderPath(folder, key):
    '''
    Reusable function getting the full path of export folders
    '''
    fullPath = folder['fullPath'] + folderNames[key]
    checkDir(fullPath)
    logging.debug('{}Full Folder Path Defined: {}{}'.format(YELLOW, fullPath, END))
    return fullPath

def defineFullFilePath(folder, key):
    '''
    Reusable function getting the full path of export files for everything
    '''
    fullPath = defineFullFolderPath(folder, key)
    filePath = fullPath + fileNames[key]
    logging.info('{}Full File Path Defined: {}{}'.format(YELLOW, filePath, END))
    return filePath

def writeToJsonFile(payload, filePath, overwrite=False):
    '''
    Takes dictionary and writes to .json file in the relevant folder
    '''
    if os.path.isfile(filePath) and not overwrite: # Not writing over file
        logging.info('File exists. Not overwriting ({})'.format(filePath))
        return False
    try:
        with open(filePath, 'w') as fp:
            json.dump(payload, fp)
        return True
    except Exception as e:
        logging.critical('{}Failed writing dictionary to file: {} - Error Message: {}{}'.format(RED, filePath, e, END))
        return False

def addToJsonFile(payload, filePath):
    '''
    Adding to JSON file
    Various export functions add to reporting file information about the export.
    Could be used for other files later when needed.
    '''
    if not os.path.isfile(filePath): # If file does not exist, we just create it.
        return writeToJsonFile(payload, filePath)
    try: # If it exists, we update it
        with open(filePath, "r+") as file:
            data = json.load(file)
            data.update(payload)
            file.seek(0)
            json.dump(data, file)
        return True
    except Exception as e:
        logging.error('{}Unable to update {}{}'.format(RED, filePath, END))
        logging.error('{}Error: {}{}'.format(RED, e, END))
        return False

def addToExportReport(key, value, folder):
    '''
    Used in many places to enrich the export report
    '''
    addToJsonFile({key:value}, folder + exportReportFile)

def readFromJsonFile(filePath):
    try:
        with open(filePath) as json_file:
            return json.load(json_file)
    except Exception as e:
        logging.critical('Failed reading from json file: '  + filePath + ' - ' + str(e))
        return False

def downloadFileToDisk(url, folder, fileName):
    '''
    Downloading asset file to local disk
    '''
    if os.path.isfile(folder + fileName): # Not writing over file
        logging.info('File exists. Not overwriting ({})'.format(folder + fileName))
        return True
    try:
        res = requests.get(url, allow_redirects=True)
        if res.status_code not in (200, 201):
            logging.error('{}Unable to download asset: {} from URL: {}{}'.format(RED, fileName, url, END))
            logging.error('{}Error Message: {} {}'.format(RED, res.text, END))
            return False
        write = open(folder + fileName, 'wb').write(res.content)
        if not write:
            logging.error('{}Unable write asset to disk: {}/{}{}'.format(RED, folder, fileName, END))
            return False
        logging.info('Asset downloaded: {}'.format(fileName))
        return True
    except Exception as e:
        logging.error('{}Unable to download asset: {} from URL: {}{}'.format(RED, fileName, url, END))
        logging.error('{}Error Message: {} {}'.format(RED, e, END))
        return False

def countFilesInFolder(folder):
    count = 0
    for path in readDirIfExists(folder):
        if os.path.isfile(os.path.join(folder, path)):
            count += 1
    return count

def countFoldersInFolder(folder):
    count = 0
    for path in readDirIfExists(folder):
        if os.path.isdir(os.path.join(folder, path)):
            count += 1
    return count

def structureReport(folder):
    '''
    Iterates all folders and generates 'crude' analytics to be pumped in report
    '''
    d = {}
    for key, _ in folderNames.items():
        if key not in ['assets', 'entries', 'folders']: # Those types are exported to more folders and/or files
            label = 'Number of {} Exported'.format(key)
            value = folder + folderNames[key]
            d[label] = countFilesInFolder(value)
    try:
        d['Number of Assets Exported'] = countFoldersInFolder(folder + folderNames['assets'])
        if os.path.isfile(folder + folderNames['folders'] + fileNames['folders']):
            d['Number of Asset Folders Exported'] = len(readFromJsonFile(folder + folderNames['folders'] + fileNames['folders'])['assets'])
        else:
            d['Number of Asset Folders Exported'] = 0
    except Exception:
        d['Number of Assets Exported'] = None
        d['Number of Asset Folders Exported'] = None
    d['Number of Content types with Exported Entries'] = countFoldersInFolder(folder + folderNames['entries'])
    d['Number of Entries Per Content Type and Language'] = {}
    for contentType in readDirIfExists(folder + folderNames['entries']):
        d['Number of Entries Per Content Type and Language'][contentType] = {}
        ctFolder = folder + folderNames['entries'] + contentType + '/'
        for f in readDirIfExists(ctFolder):
            lang = f.replace('.json', '')
            r = readFromJsonFile(ctFolder + f)
            d['Number of Entries Per Content Type and Language'][contentType][lang] = len(r['entries'])
    addToJsonFile({'Numbers':d}, folder + exportReportFile) # Adding our findings to the report
