import configparser, os, re, ast, subprocess, datetime
scriptDir = os.path.dirname(os.path.realpath('__file__'))

masterconfig = configparser.ConfigParser()
masterconfig.read('masterconfig.ini')

relitiveScriptDir = os.path.join(scriptDir, os.path.normpath(masterconfig['Scripts']['restart'][:-8]))

config = configparser.ConfigParser()
config.read(os.path.join(relitiveScriptDir,'localConfig.ini'))
rawlogPath = os.path.join(relitiveScriptDir, os.path.normpath(config['Paths']['rawlog']))
logPath = os.path.join(relitiveScriptDir, os.path.normpath(config['Paths']['log']))

def generateCode(date,player,server,fromServer):
    dateCode = int(date[:4])*int(date[5:7])/int((oct(int(date[-2:]))[2:]))
    playerCode = ord(player[1])+ord(player[-1])/ord(player[int(len(player)/2)])*ord(player[2])+ord(player[-2])
    serverCode = float(config['Server Codes'][server])
    fromserverCode = float(config['More Server Codes'][fromServer])
    codewordCode = 0
    for char in config['Other']['codeword']:
        codewordCode = codewordCode + ord(char)*len(player)
    return hex(int(dateCode*playerCode/serverCode+fromserverCode-codewordCode*serverCode))[3:]
    
def findNextRestart(server):
    if config['Next Restart'][server] == 'N/A':
        now = datetime.datetime.now()
        date = '{:%Y-%m-%d}'.format(datetime.datetime(now.year, now.month, now.day))
        date = datetime.datetime.strptime(date, '%Y-%m-%d')
    else:
        date = datetime.datetime.strptime(config['Next Restart'][server], '%Y-%m-%d')
    new = date + datetime.timedelta(hours=int(config['Auto Restart'][server]))
    config['Next Restart'][server] = '{:%Y-%m-%d}'.format(datetime.datetime(new.year, new.month, new.day))
    print('Next Restart for %s is %s' %(masterconfig['Server Names'][server],config['Next Restart'][server]))

def getNewLines():
    log = open(os.path.join(relitiveScriptDir, rawlogPath),'r').readlines()
    if int(config['Other']['logprogress']) <= log.index(log[-1])+1:
        toReturn = log[int(config['Other']['logprogress']):]
    else:
        toReturn = log[0:]
    config['Other']['logprogress'] = str(log.index(log[-1])+1)
    return toReturn

def log(line):
    with open(logPath,'a') as log:
        log.write(line+'\n')

def restart(server):
    #service factorio1 new-map mapname.zip data/map-gen-settings.example.json
    #service <_______> new-game map<__>.zip data/map-gen-settings.example.json
    subprocess.call(['service',masterconfig['Map Names'][server],'new-game','map'+str(int(masterconfig['Current Map'][server])+1)+'.zip','data/map-gen-settings.example.json'])
    masterconfig['Current Map'][server] = str(int(masterconfig['Current Map'][server])+1)
    
def manualRestart():
    lines = getNewLines()
    for line in lines:
        line = ast.literal_eval(re.search('{(.+?)}',line).group(0))
        if line['type'] == 'shout' and 'RESTART' in line['message']:
            message = line['message']
            #message = 'RESTART S1 >>>1248a'
            if re.search('S\d',message):
                server = re.search('S\d',message).group(0)
                if re.search('>>>(.+?)$',message):
                    code = re.search('>>>(.+?)$',message).group(0)[3:]
                    now = datetime.datetime.now()
                    date = '{:%Y-%m-%d}'.format(datetime.datetime(now.year, now.month, now.day))
                    if code == generateCode(date,line['byplayer'],server,line['server']):
                        log(server+' was restart by '+line['byplayer'])
                        findNextRestart(server)
                        restart(server)
                    else:
                        log(line['byplayer']+' Failed to restart server')

def autoRestart():
    for server in config['Auto Restart']:
        if config['Auto Restart'][server] != '0' and config['Next Restart'][server] != 'N/A':
            restartDate = datetime.datetime.strptime(config['Next Restart'][server], '%Y-%m-%d')
            if restartDate < datetime.datetime.now():
                restart(server)
    with open(os.path.join(relitiveScriptDir,'localConfig.ini'), 'w') as configfile:
        config.write(configfile)
