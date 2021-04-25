#!/bin/python

from flask import Flask, request, redirect, url_for, render_template, send_file
app = Flask(__name__)

from PIL import Image
import base64
import numpy as np
import cv2
import io

import os

img, no_img = 0, 1

@app.route('/')
def root():
    return redirect(url_for('index'))

i = 0
@app.route('/index')
def index():
    global i, no_img
    i += 1
    return render_template('index.html',
        counter = i,
        autoupdate = request.args.get('autoupdate', default = 0, type = int),
        no_img = no_img
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
    global img, no_img
    image = request.json['image']

    arr = np.frombuffer(base64.b64decode(image), np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    no_img = 0


    return '', 204

@app.route('/image.jpg')
def image():
    global img
    image = Image.fromarray(img.astype('uint8'))
    file = io.BytesIO()
    image.save(file, 'JPEG')
    
    file.seek(0)
    return send_file(file, mimetype='image/jpeg')

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
