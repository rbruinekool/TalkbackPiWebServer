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
    startMuteBox()

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
    fileHandler = open("muteBoxPid.obj", 'rb')
    muteBoxPid = pickle.load(fileHandler)
    os.kill(muteBoxPid, signal.SIGKILL)
    time.sleep(1)
    startMuteBox()
    return redirect(url_for('.index'))

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
                r = requests.get('http://127.0.0.1:5000/')
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
    muteBoxPid = subprocess.Popen(['python2', '/Users/rbruinekool/PycharmProjects/x32-broadcast/MuteBoxServer.py']).pid
    fileHandler = open("muteBoxPid.obj", 'wb')
    pickle.dump(muteBoxPid, fileHandler)
    return "muteBoxPid = " + str(muteBoxPid)

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

if __name__ == '__main__':
    start_runner()
    app.run(debug=True, host='0.0.0.0')