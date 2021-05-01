#!/bin/python

from flask import Flask, request, redirect, url_for, render_template, send_file, current_app
app = Flask(__name__)

from PIL import Image
import base64
import numpy as np
import cv2
import io

import os

img, status = 0, 0

@app.route('/')
def root():
    return redirect(url_for('index'))

@app.route('/index')
def index():
    global status
    dat = dict()
    if status == 1:
        dat['error'] = "ID not recognized"
    elif status == 2:
        dat['name'] = "BAYOD, Jerico Wayne Y."
        dat['gradeAndSection'] = "12 - Eridani"
        dat['idNumber'] = "15-01297"
        dat['address'] = "Centro East, Allacapan, Cagayan"
        dat['residence'] = "Intern"
        dat['status'] = "In Campus"
    return render_template('index.html',
        autoupdate = request.args.get('autoupdate', default = 0, type = int),
        status = status,
        stamp = np.random.randint(1,0xFFFF),
        data=dat
    )

@app.route('/log')
def log():
    return render_template('log.html')

@app.route('/leavePass')
def leavePass():
    return render_template('leavePass.html')

@app.route('/students')
def students():
    return render_template('students.html')

@app.route('/post', methods=['POST'])
def post():
    global img, status
    image = request.json['image']

    arr = np.frombuffer(base64.b64decode(image), np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    status += 1


    return '', 204

@app.route('/image.jpg')
def image():
    global img
    if status > 0:
        image = Image.fromarray(img.astype('uint8'))
        file = io.BytesIO()
        image.save(file, 'JPEG')
        file.seek(0)
        return send_file(file, mimetype='image/jpeg')
    else:
        return send_file('static/images/noimg.jpg', mimetype='image/jpeg')

@app.route('/idpic/<idnumber>')
def idpic(idnumber):
    if os.path.exists("static/images/{}.jpg".format(idnumber)):
        return send_file('static/images/{}.jpg'.format(idnumber), mimetype='image/jpeg')
    else:
        return send_file('static/images/noid.jpg', mimetype='image/jpg')


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path, endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)

if __name__ == '__main__':
    app.run('192.168.1.115', 5000)
