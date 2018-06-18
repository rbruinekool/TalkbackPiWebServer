from flask import Flask, render_template, url_for, redirect
import socket
import subprocess
import time
from multiprocessing import Process
import os
import signal
import requests
import threading
import pickle

app = Flask(__name__)

@app.before_first_request
def beforeRequest():
    thisDevice = socket.gethostname()

    # Stupid statement to allow running on pycharm on mac
    if socket.gethostname() == "Robrechts-MacBook-Pro-4.local":
        thisDevice = "talkback-test"

    if "mutebox" in thisDevice:
        print ("mutebox detected")
        checkIn()
    elif "talkback" in thisDevice:
        startTalkbackPi()
        print ("talkback box detected")
    else:
        print ("other device detected")

@app.route('/')
def index():
    thisDevice = socket.gethostname()
    return render_template('index.html', thisDevice=thisDevice)

@app.route('/reboot')
def rebootPage():
    p1 = Process(target=reboot)
    p1.start()
    return redirect(url_for('.index'))

@app.route('/restartmutebox')
def restartMuteBox():
    thisDevice = socket.gethostname()

    #Stupid statement to allow running on pycharm on mac
    if socket.gethostname() == "Robrechts-MacBook-Pro-4.local":
        thisDevice = "talkback-test"

    if "mutebox" in thisDevice:
        fileHandler = open("muteBoxPid.obj", 'rb')
        muteBoxPid = pickle.load(fileHandler)
        os.kill(muteBoxPid, signal.SIGKILL)
        time.sleep(1)
        startMuteBox()
        return redirect(url_for('.index'))
    elif "talkback" in thisDevice:
        fileHandler = open("talkbackPid.obj", 'rb')
        talkbackPid = pickle.load(fileHandler)
        os.kill(talkbackPid, signal.SIGKILL)
        time.sleep(1)
        startTalkbackPi()
        return redirect(url_for('.index'))
    else:
        print("other device detected")


def reboot():
    time.sleep(3)
    command = "/usr/bin/sudo /sbin/shutdown -r now"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    return output

# This function forces the before_first_request function to run by starting a temporary thread
# that polls the server locally (otherwise it only starts when someone opens the server for the first time)
def start_runner():
    def start_loop():
        not_started = True
        while not_started:
            print('In start loop')
            try:
                r = requests.get('http://127.0.0.1:5000/', timeout=5)
                if r.status_code == 200:
                    print('Server started, quiting start_loop')
                    not_started = False
            except:
                print('Server not yet started')
            time.sleep(2)

    print('Started runner')
    thread = threading.Thread(target=start_loop)
    thread.start()

def startMuteBox():
    if socket.gethostname() == "Robrechts-MacBook-Pro-4.local":
        path = "/Users/rbruinekool/PycharmProjects/x32-broadcast/MuteBoxServer.py"
    else:
        path = "/home/pi/x32-broadcast/MuteBoxServer.py"
    muteBoxPid = subprocess.Popen(['python2', path]).pid
    fileHandler = open("muteBoxPid.obj", 'wb')
    pickle.dump(muteBoxPid, fileHandler)
    return "muteBoxPid = " + str(muteBoxPid)

def startTalkbackPi():
    deviceName = socket.gethostname();
    if deviceName == "Robrechts-MacBook-Pro-4.local":
        path = "/Users/rbruinekool/PycharmProjects/x32-broadcast/ProducerServer.py"
        deviceName = "talkback-a"
    else:
        path = "/home/pi/x32-broadcast/ProducerServer.py"

    person = getTalkbackData(deviceName);
    talkbackPid = subprocess.Popen(['python2', path, 'o', person]).pid
    fileHandler = open("talkbackPid.obj", 'wb')
    pickle.dump(talkbackPid, fileHandler)

    checkIn()

    return "muteBoxPid = " + str(talkbackPid)

def checkIn():
    # Checking for an internet connection
    internetActive = False
    while not (internetActive):
        try:
            #urllib3.urlopen('http://google.com', timeout=1)
            requests.get('http://google.com', timeout=1)
            internetActive = True
        except:
            print("No connection to internet, trying again in 5 seconds")
            time.sleep(5)

    # Getting current Ip
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    myIp = s.getsockname()[0]
    s.close()

    thisDevice = socket.gethostname()

    # Stupid statement to allow running on pycharm on mac
    if socket.gethostname() == "Robrechts-MacBook-Pro-4.local":
        thisDevice = "talkback-test"

    if "mutebox" in thisDevice:
        r = requests.post(
            "https://script.google.com/macros/s/AKfycbzB3Tig-5MJp3eLhVInG-IGOx7cwVqvfDBjdByuVfHBKkxMvpw/exec",
            data={"deviceType": "mutebox", "deviceName": thisDevice, "muteboxIp": myIp})
        startMuteBox()
    elif "talkback" in thisDevice:
        r = requests.post(
            "https://script.google.com/macros/s/AKfycbzB3Tig-5MJp3eLhVInG-IGOx7cwVqvfDBjdByuVfHBKkxMvpw/exec",
            data={"deviceType": "talkback", "deviceName": thisDevice, "muteboxIp": myIp})
            #Moved checkin function to starting of the talkback script to make sure it checks in during a restart
    else:
        print("It appears this Pi is not a mutebox or a talkbackPi")

def callbackdata(data):
    return data

def getTalkbackData(deviceName):
    sheetId = "1xCvYdmH13sQg41dOZfgAiYZLI1JzmML7IhTW7QzNktg"
    url = "http://spreadsheets.google.com/tq?tqx=responseHandler:callbackdata&key=" + sheetId + "&sheet=talkback pis"

    rawResponse = requests.get(url).text
    response = rawResponse.splitlines()[1].replace(';', '').replace('null', '{}')
    response = response.replace('"v":{}', '')  # This one is put on a separate row because it might be a bit risky
    responseDict = eval(response)
    allRows = responseDict["table"]['rows'];

    deviceFound = False
    for i in range(0, len(allRows)):
        if allRows[i]['c'][0]['v'] == deviceName:
            deviceFound = True
            deviceRow = i

    if deviceFound:
        return allRows[deviceRow]['c'][1]['v']
    else:
        print ("Cant find who this device ("+ deviceName + ") belongs to")
        return


app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

if __name__ == '__main__':
    start_runner()
    app.run(debug=True, host='0.0.0.0')
