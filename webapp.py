from flask import Flask, render_template, url_for, redirect
import socket
import subprocess
import time
from multiprocessing import Process

app = Flask(__name__)

def restart():
    time.sleep(1)
    command = "/usr/bin/sudo /sbin/shutdown -r now"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    return output

@app.route('/')
def index():
    thisDevice = socket.gethostname()
    return render_template('index.html', thisDevice=thisDevice)

@app.route('/reboot')
def rebootPage():
    p1 = Process(target=restart)
    p1.start()
    return redirect(url_for('.index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')