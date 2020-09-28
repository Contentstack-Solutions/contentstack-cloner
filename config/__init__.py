'''
oskar.eiriksson@contentstack.com
2020-09-28

Various config functions and variables user in both export and import scripts
'''
import os
from time import sleep
from datetime import datetime
import json
import inquirer
import cma

localFolder = 'content' # Relative path to the export folder
mapperFolder = 'uidMappers' # The folder where mappers folders are stored - under the localFolder
exportLoginFile = 'exportLogin.json'
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
    'assets': 'assets.json'
}

'''
Text formating available
'''
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

def checkDir(folder):
    '''
    Checks if folder exists
    '''
    if not os.path.exists(localFolder + '/' + folder):
        cma.logging.info('Creating folder: ' + localFolder + '/' + folder)
        os.makedirs(localFolder + '/' + folder)
        return True
    return False

def createFolder(name):
    '''
    Creates an export folder with name
    '''
    cont = [inquirer.Text('folderName', message="{}Give the export folder a name:{}".format(BOLD, END), default=name + ' - ' + str(datetime.now()))]
    folderName = inquirer.prompt(cont)['folderName']
    return folderName

def chooseFolder(ignoreFolder=None):
    '''
    Lists up folders in export folder.
    Optionally, there's a folder to be ignored from the list.
    The user just picks one.
    '''
    if ignoreFolder:
        allFolders = []
        for f in os.listdir(localFolder):
            if f != ignoreFolder:
                allFolders.append(f)
    else:
        allFolders = os.listdir(localFolder)
    folder = [
        inquirer.List('chosenFolder',
                      message="{}Choose export folder to import from{}".format(BOLD, END),
                      choices=allFolders,
                      ),
    ]
    folder = inquirer.prompt(folder)['chosenFolder']
    return folder


def validateJSON(filename):
    '''
    Simple validation of json
    '''
    try:
        with open(localFolder + '/' + filename) as json_file:
            json.load(json_file)
    except Exception:
        return False
    return True

def validateExport():
    '''
    Validates that there is an export available for everything
    '''
    for export, filename in fileNames.items():
        if filename not in os.listdir(localFolder):
            cma.logging.warning(export + ' export is not in exports folder. (' + filename + ')')
            cont = None
            while cont not in ('Y', 'y', 'N', 'n'):
                cont = input('The ' + export + ' are missing from the stack export. Continue with import? (Y/N)')
                if cont in ('N', 'n'):
                    sleep(0.5)
                    cma.logging.info('Exiting...')
                    sleep(0.5)
                    return False
        else:
            if not validateJSON(filename):
                cma.logging.error('{}File is corrupt! ({}) - Exiting{}'.format(RED, filename, END))
                sleep(0.5)
                cma.logging.info('Exiting...')
                sleep(0.5)
                return False
    return True


def writeToJsonFile(payload, filePath):
    '''
    Takes dictionary and writes to .json file in the relevant folder
    '''
    try:
        with open(filePath, 'w') as fp:
            json.dump(payload, fp)
        return True
    except Exception as e:
        cma.logging.critical('Failed writing dictionary to file: ' + filePath + ' - ' +  str(e))
        return False

def readFromJsonFile(filePath):
    try:
        with open(filePath) as json_file:
            return json.load(json_file)
    except Exception as e:
        cma.logging.critical('Failed reading from json file: '  + filePath + ' - ' + str(e))
        return False
