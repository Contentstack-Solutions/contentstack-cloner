'''

'''
import os
import re
import config
import inquirer
import cma
from app import exitProgram


def chooseRegion():
    '''
    Choosing between available Contentstack regions
    '''
    regionMap = {
        'North America': 'US',
        'Europe': 'EU'
    }
    chooseRegion = [
        inquirer.List('chosenRegion',
                      message="{}Choose Region{}".format(config.BOLD, config.END),
                      choices=['North America', 'Europe'],
                      ),
    ]
    region = inquirer.prompt(chooseRegion)['chosenRegion']
    return regionMap[region]

def executeLogin(loginInfo, maxTries, count=1):
    '''
    Executes the login versus Contentstack with the login information fetches in the initiateLogin function
    '''
    loginInfo['region'] = cma.regionMap[loginInfo['region']]
    while count < maxTries: # Maximum Attempts
        statusCode, loginAttempt = cma.login(loginInfo['username'], loginInfo['password'], loginInfo['region'])
        if statusCode == 200:
            return loginAttempt, loginInfo['region']
        elif 'error_message' in loginAttempt:
            config.logging.error(str(config.RED) + str(loginAttempt['error_message']) + str(config.END))
        else:
            config.logging.error(str(config.RED) + str(loginAttempt) + str(config.END))
        count += 1
    config.logging.error('{}Login failed{}'.format(config.RED, config.END))
    return None, None

def getLoginInfo(region):
    '''
    Getting the username and password
    '''
    loginList = [
        inquirer.Text('username', message="{}Type in your username (email address){}".format(config.BOLD, config.END), validate=lambda _, x: re.match('[^@]+@[^@]+\.[^@]+', x)),
        inquirer.Password('password', message="{}Type in your password{}".format(config.BOLD, config.END)),
        inquirer.Confirm('store', message='{}Do you want to store the authentication token on the local drive?{}'.format(config.BOLD, config.END), default=True)
    ]
    loginInfo = inquirer.prompt(loginList)
    loginInfo['region'] = region
    return loginInfo

def shouldDeleteFile():
    deleteFile = [inquirer.Confirm('deleteFile', message="{}Want to delete authtoken file?{}".format(config.BOLD, config.END), default=True)]
    if inquirer.prompt(deleteFile)['deleteFile']:
        os.remove(config.authTokenFile)



def initiateLogin(region, retrying=False):
    '''
    Initiating a Login sequence
    '''
    loginToNewRegion = False
    if retrying:
        shouldDeleteFile()
    loginInfo = None
    if os.path.isfile(config.authTokenFile):
        authTokenDict = config.readFromJsonFile(config.authTokenFile)
        if authTokenDict:
            if region in authTokenDict:
                config.logging.info('Authtoken found for user {}{}{} in {} region.'.format(config.UNDERLINE, authTokenDict[region]['username'], config.END, region))
                use = [inquirer.Confirm('useFile', message="{}AuthToken found on local storage. Try to use that?{}".format(config.BOLD, config.END), default=True)]
                if inquirer.prompt(use)['useFile']:
                    return {'region': region, 'username': authTokenDict[region]['username'], 'authtoken': authTokenDict[region]['authtoken']}
                else:
                    shouldDeleteFile()
                loginInfo = getLoginInfo(region)
            else:
                loginToNewRegion = True
                loginInfo = getLoginInfo(region)
    else:
        loginInfo = getLoginInfo(region)
    if loginInfo or loginToNewRegion:
        statusCode, userSession = cma.login(loginInfo['username'], loginInfo['password'], cma.regionMap[loginInfo['region']])
        if statusCode == 200:
            config.logging.info('{}Login Successful - Username: {} - Region: {}{}'.format(config.GREEN, loginInfo['username'], loginInfo['region'], config.END))
        else:
            config.logging.critical('{}Login ERROR! - Username: {} - Region: {} Status Code: {}{}'.format(config.GREEN, loginInfo['username'], loginInfo['region'], statusCode, config.END))
            return None
        sessionToFile = {loginInfo['region']: {'username': loginInfo['username'], 'authtoken': userSession['user']['authtoken']}}
        session = {'username': loginInfo['username'], 'authtoken': userSession['user']['authtoken'], 'region': loginInfo['region']}
        if statusCode == 200 and loginInfo['store']:
            config.addToJsonFile(sessionToFile, config.authTokenFile)
        return session

def startup(count=1):
    '''
    Starting up the application - authenticating the user
    '''
    region = chooseRegion()

    userInfo = initiateLogin(region)
    if not userInfo:
        config.logging.critical('Not able to login. Try again')
        exitProgram()
    liveUserInfo = cma.getUserInfo(userInfo['authtoken'], cma.regionMap[region])
    print('here')
    if not liveUserInfo:
        userInfo = initiateLogin(region, count)
    while not liveUserInfo and count < 3:
        liveUserInfo = cma.getUserInfo(userInfo['authtoken'], cma.regionMap[region])
        count += 1
    return cma.regionMap[region], userInfo, liveUserInfo, userInfo['authtoken']
