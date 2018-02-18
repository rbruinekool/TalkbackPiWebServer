from flask import Flask, render_template
import socket
import subprocess

app = Flask(__name__)

def restart():
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
    return restart()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')