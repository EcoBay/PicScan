#!/bin/python

from flask import Flask, request, redirect, url_for, render_template, send_file, current_app
app = Flask(__name__)

import sqlite3
import ocr

from PIL import Image
import base64
import numpy as np
import cv2
import io

import os

img, status, dat = 0, 0, None

@app.route('/')
def root():
    return redirect(url_for('index'))

@app.route('/index')
def index():
    global status, dat

    if status == 2:
        with sqlite3.connect('picscan.db') as conn:
            cur = conn.cursor()
            sql = '''
                SELECT Logout.ID, type, timeout, timein, CASE remarks
                    WHEN 0 THEN "No Issues"
                    WHEN 110 THEN "WARNING: Exceeded Time"
                    WHEN 210 THEN "VIOLATION: Exceeded Time"
                    WHEN 211 THEN "VIOLATION: Expired Pass"
                    WHEN 221 THEN "VIOLATION: Broke Curfew"
                    WHEN 222 THEN "VIOLATION: Inappropriate Behaviour"
                END
                FROM Students
                INNER JOIN LeavePass ON LeavePass.studentID=Students.id
                INNER JOIN Logout ON Logout.leavePassID=LeavePass.id
                LEFT JOIN Login ON Login.logID=Logout.id
                WHERE idNumber=? ORDER BY Logout.ID DESC LIMIT 10
            '''
            cur.execute(sql, (dat['idNumber'],))
            dat['logs'] = cur.fetchall()
    
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
    global img, status, dat
    image = request.json['image']

    arr = np.frombuffer(base64.b64decode(image), np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    val, img1 = ocr.checkValidity(img)

    if val:
        dat = ocr.getUser(img1)
        if not dat:
            dat = {'error': 'Student not in the Database'}
            val -= 1
    else:
        dat = {'error': 'Cannot recognize ID'}

    status = val + 1

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
