
import os
import paramiko
import time
import pycurl
from selenium import webdriver
import certifi
from io import BytesIO
import urllib3
import pyautogui
import time
from datetime import datetime
import subprocess
import json
confs = open("./config.json")
confs = json.load(confs)

api_port = confs["api_port"]
api = confs["api"]
server = confs["server"]
port = confs["port"]
username = confs["username"]
password = confs["password"]
DeployBranch = confs["DeployBranch"]
githubKey = confs["githubKey"]
RepoLink = confs["RepoLink"]
domain = confs["domain"]
RootUrl = confs["RootUrl"]
sudomains = confs["sudomains"]
folderName = RepoLink.split("/")[4].replace(".git", "")
repoServerpath = ''
clientPath = "" if confs["clientPath"] == "/" else confs["clientPath"]


def CreateJointCer():
    path = os.getcwd()
    print(path)


def CreateJointSSL():
    '''This is to Join two certificates "domain.cer" and "intermediate.cer" localted in the ./SSL folder. !!! This JointCer.cer needs to stay there because it is needed !!!!'''
    cer = ''.join(open('./SSL/domain.cer', 'r'))

    intermediate = ''.join(open('./SSL/intermediate.cer', 'r'))

    file = open('./SSL/JointCer.cer', 'w')
    file.write(cer + intermediate)
    print(file)


def ConfigureGit(conn):
    '''Configuring git: 
    1.Manipulate gitignore to track builds 
    2.Enabling line ending conversions on Windows 
    3.Enabling line ending conversions on Linux
    '''
    file = open("../.gitignore", 'r')
    f = ''.join(file.readlines())

    f = f.replace("/build", '')
    file.close()

    out = open("../.gitignore", "w")
    out.write(f)
    out.close()
    subprocess.run(["git", "config", "--global",
                   "core.autocrlf", "true"], shell=True, check=True)
    execCommand(conn, command="git config --global core.autocrlf input")


def buildCommitPush():
    try:
        subprocess.run(["npm", "run", "build"], shell=True, check=True)
    except Exception as e:
        print("building went wrong")
    subprocess.run(["git", "add", "--all"], shell=True, check=True)
    subprocess.run(["git", "commit", "-m",
                   '"commitBeforeSendingToServer"'], shell=True, check=True)
    subprocess.run(["git", "push"], shell=True, check=True)


def login():
    process = subprocess.Popen(['start', 'cmd'], shell=True,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    time.sleep(5)
    # NOTE this has changed
    pyautogui.write(f'ssh {username}@{confs["server"]} -p{port}')
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(2.5)
    pyautogui.write(confs["password"])
    time.sleep(1)
    pyautogui.press('enter')


def installVim():
    login()
    pyautogui.write(f'sudo apt install vim')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(2)
    pyautogui.write(f'yes')
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(2)
    w = pyautogui.getActiveWindow()
    w.close()


def connect_to_server():
    conn = paramiko.SSHClient()
    # This script doesn't work for me unless this line is added!
    conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(server + port + username + password)
    conn.connect(server, port=port, username=username, password=password)
    return conn


def execCommand(p, command):
    '''this is a docstring'''
    print('\n==================================================================================================')
    print('COMMAND: '+command)
    stdin, stdout, stderr = p.exec_command(command)
    opt = stdout.readlines()
    opt = "".join(opt)
    err = stderr.readlines()
    err = "".join(err)
    print(f'OUTPUT: {opt}')
    print(f'ERROR: {err}')
    return opt, err


def execCommands(p, commands):
    '''this is a docstring'''
    for com in commands:
        execCommand(p, com)


def InitClient():
    '''return paramiko client and the connection 
    takes in configurations from config.json'''

    conn = connect_to_server()
    p = paramiko.SSHClient()
    # This script doesn't work for me unless this line is added!
    p.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    p.connect(server, port,
              username=username, password=password)
    commands = ["uname -a", 'ls -l', 'git --version',
                'echo $SHELL | bash -', 'echo $SHELL']
    execCommands(conn, commands)
    return p, conn


def nginx_subdomain(subdomains):
    '''take list of subdomains and create nginx configuration file for each one localy before copying to the server under /etc/nginx/enabled-sites '''
    default_server = 0
    for subdomain in subdomains:
        if os.path.exists("./Nginx/"+subdomain+".txt"):
            os.remove("./Nginx/"+subdomain+".txt")
        output = open("./Nginx/"+subdomain+".txt", "a")
        with open("./Nginx/"+'HTTPSNginxConfig.txt') as template:
            for line in template:
                if "root" in line:
                    line = "root /var/www/"+subdomain+"/html;"
                if "server_name" in line:
                    line = "server_name "+subdomain+";"
                if "return 301" in line:
                    line = "return 301 https://"+subdomain+"$request_uri;"
                if "default_server" in line:
                    if default_server < 2:
                        line = line.replace("default_server", "")
                        default_server += 1
                output.write(line+"\n")
            output.close()
            template.close()


def setup_https(conn):
   # sudomains=['aottest.Kaiserfranz-engineering.de','lgtest.Kaiserfranz-engineering.de']
    nginxPath = f'/root/{folderName}/Deploy/Nginx'
    SSLPath = f'/root/{folderName}/Deploy/SSL/'
    # buildPath = f'/root/{folderName}/{}'
    print(sudomains)
    for sudomain in sudomains:
        buildPath = f'/root/{folderName}/Deploy/{sudomain}'
        commands = [f'mkdir -p /var/www/{sudomain}/html/',
                    "export DEBIAN_FRONTEND=noninteractive",
                    '[ -d "/etc/ssl" ] &&  echo " /etc/ssl directoty  exsist" ||  ( echo \'directory not exsist .. creating /etc/ssl directory\' && mkdir -p /etc/ssl)',
                    f'cp -r {SSLPath}*.pem /etc/ssl',
                    f'cp -r {SSLPath}*.key /etc/ssl',
                    f'cp -r {SSLPath}*.crt /etc/ssl',
                    f'cp -r {SSLPath}*.cer /etc/ssl',
                    f'echo 127.0.0.1 {sudomain} >> /etc/hosts ',
                    f'cat /etc/ssl/domain.cer /etc/ssl/intermediate.cer > /etc/ssl/jointCert.cer',
                    'mv /etc/nginx/sites-enabled/default /default',
                    f'cp -r {buildPath}/* /var/www/{sudomain}/html/',
                    f'[ -f "/etc/nginx/sites-enabled/{sudomain}" ] &&  echo " /etc/nginx/sites-enabled/{sudomain} file  exsist" ||  ( echo \'file not exsist .. creating /etc/nginx/sites-enabled/{sudomain}\' && touch /etc/nginx/sites-enabled/{sudomain})',
                    f"cat {nginxPath}/{sudomain}.txt  >  /etc/nginx/sites-enabled/{sudomain}",
                    'nginx -t',
                    'systemctl restart nginx']
        execCommands(conn, commands)


def setup_http(conn):  # NOTE this might not work when using 'npm server'
    nginxPath = f'root/{folderName}/Deploy/Nginx/NGINXConfig.txt'
    buildPath = f'/root/{folderName}/{clientPath}/build/*'
    print('nginx config path' + nginxPath + '\nbuildPath:' + buildPath)
    commands = ['mkdir -p /var/www/localhost/html/',
                '[ -d "/etc/ssl" ] &&  echo " /etc/ssl directoty  exsist" ||  ( echo \'directory not exsist .. creating /etc/ssl directory\' && mkdir -p /etc/ssl)',
                'mv /etc/nginx/sites-enabled/default /default',
                f'cp -r {buildPath} /var/www/localhost/html/',
                'touch /etc/nginx/sites-enabled/localhost',
                f'cd / ; cat  {nginxPath} > /etc/nginx/sites-enabled/localhost',
                'nginx -t',
                'systemctl restart nginx']
    execCommands(conn, commands)


def fire_up_server(conn):
    commands = [f'cd /root/{folderName}', 'pm2 start server.js',
                'curl http://localhost:4000/api/user']
    execCommands(conn, commands)


def install_nginx(conn):
    commands = ['apt-get install -y nginx', 'ufw allow OpenSSH',
                'ufw allow \'Nginx Full\' ', 'ufw --force enable']
    execCommands(conn, commands)


def install_js_pm2_npm(conn):
    commands = ['apt-get install -y ufw',
                'export DEBIAN_FRONTEND=noninteractive', 'apt-get install -y libterm-readline-gnu-perl', 'curl -sL https://deb.nodesource.com/setup_10.x', 'apt-get install -y nodejs', 'apt-get install -y npm', 'export NODE_OPTIONS="--max-old-space-size=8192"', 'npm install -g pm2', 'pm2 startup systemd']
    execCommands(conn, commands)


def install_mongo_db(conn):
    commands = ['apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 9DA31620334BD75D9DCB49F368818C72E52529D4',
                'echo "deb [ arch=amd64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/4.0 multiverse" |  tee /etc/apt/sources.list.d/mongodb-org-4.0.list',
                'apt-get update',
                'apt-get install -y mongodb-org', 'systemctl enable mongod',
                'systemctl start mongod',
                'systemctl enable mongod']

    for i in commands:
        opt = execCommand(conn, i)[1]
        if opt:
            print('error!!')
            opt = "".join(opt)
            print(opt)
            commands = ['echo "deb http://security.ubuntu.com/ubuntu impish-security main" | sudo tee /etc/apt/sources.list.d/impish-security.list',
                        'apt-get update', 'apt-get install libssl1.1']
            for i in commands:
                execCommand(conn, i)


def ClonePull(conn):
    '''TODO @Mohamed please use docstrings like this to describe the functionality of each function'''
    folderName = RepoLink.split("/")[4].replace(".git", "")
    commands = [
        f'rm -r {folderName}',
        f'ls',
        f'git clone https://ghp_{githubKey}@{RepoLink.replace("https://","")}.git',
        f'cd {folderName}; ls;',
        f'cd {folderName}; git pull  ',
    ]

    execCommand(conn, commands[0])
    res1 = ''.join(execCommand(conn, commands[1])[0])
    if folderName in res1:
        print('folder for repo is present at root')
        execCommand(conn, commands[3])
        execCommand(conn, commands[4])
    else:
        print('need to clone')
        execCommand(conn, commands[2])
        execCommand(conn, commands[3])
        execCommand(conn, commands[4])


def NPMInstall(conn):
    '''instals depencdencies in default branch and builds with node options Brute force'''
    for mem in [5120, 6144, 7168, 8192, 10000]:
        execCommand(conn, f'export NODE_OPTIONS="--max-old-space-size={mem}"')
        out, err = execCommand(conn, f'cd {folderName} ; npm run build')
        if not 'FATAL ERROR' in err:
            return

    if 'index.html' in ''.join(execCommand(conn, f'cd /root/{folderName}/{clientPath}/build ; ls -la')):
        print('SUCCESS: we have a build/index.html')
    else:
        raise ("Building went wrong")


def build(conn):
    '''instals depencdencies in default branch and builds with node options Brute force'''
    execCommand(conn, f'cd {folderName} ; npm install')

def api_nginx(conn):
    ''' this function will take api subdomain and port to hit backend server then create nginx config file and '''
    if os.path.exists("./Nginx/"+api+".txt"):
        os.remove("./Nginx/"+api+".txt")
    output = open("./Nginx/"+api+".txt", "a")
    with open('./Nginx/api-NginxConfig-template.txt') as template:
        for line in template:
            if "proxy_pass" in line:
                line = "proxy_pass https://"+api+":"+api_port+";"
            output.write(line+"\n")
        output.close()
        template.close()
    nginxPath = f'/root/{folderName}/Deploy/Nginx'
    SSLPath = f'/root/{folderName}/Deploy/SSL/'
    commands = ['[ -d "/etc/ssl" ] &&  echo " /etc/ssl directoty  exsist" ||  ( echo \'directory not exsist .. creating /etc/ssl directory\' && mkdir -p /etc/ssl)',
                    f'cp -r {SSLPath}*.pem /etc/ssl',
                    f'cp -r {SSLPath}*.key /etc/ssl',
                    f'cp -r {SSLPath}*.crt /etc/ssl',
                    f'cp -r {SSLPath}*.cer /etc/ssl',
                    f'echo 127.0.0.1 {api} >> /etc/hosts ',
                    f'cat /etc/ssl/domain.cer /etc/ssl/intermediate.cer > /etc/ssl/jointCert.cer',
                    'mv /etc/nginx/sites-enabled/default /default',
                    f'[ -f "/etc/nginx/sites-enabled/{api}" ] &&  echo " /etc/nginx/sites-enabled/{api} file  exsist" ||  ( echo \'file not exsist .. creating /etc/nginx/sites-enabled/{api}\' && touch /etc/nginx/sites-enabled/{api})',
                    f"cat {nginxPath}/{api}.txt  >  /etc/nginx/sites-enabled/{api}",
                    'nginx -t',
                    'systemctl restart nginx']
    execCommands(conn, commands)
    