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

img, status, dat, nam = 0, 0, None, ""

@app.route('/')
def root():
    return redirect(url_for('index'))

@app.route('/index')
def index():
    global status, dat, nam

    if status == 2:
        dat = getDat(nam)
        with sqlite3.connect('picscan.db') as conn:
            cur = conn.cursor()
            sql = '''
                SELECT Logout.ID, type, destination, timeout, IFNULL(timein, ""), IFNULL(CASE remarks
                    WHEN 0 THEN "No Issues"
                    WHEN 110 THEN "WARNING: Exceeded Time"
                    WHEN 210 THEN "VIOLATION: Exceeded Time"
                    WHEN 211 THEN "VIOLATION: Expired Pass"
                    WHEN 221 THEN "VIOLATION: Broke Curfew"
                    WHEN 222 THEN "VIOLATION: Inappropriate Behaviour"
                END, "")
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
    page = request.args.get('page', default = 1, type = int)
    sort = request.args.get('sort', default = 0, type = int)
    with sqlite3.connect("picscan.db") as conn:
        conn.enable_load_extension(True)
        conn.load_extension("./spellfix.so")

        cur = conn.cursor()
        sql = '''
            SELECT Logout.id, word, type, destination, timeout, IFNULL(timein, ""), IFNULL(CASE remarks
                    WHEN 0 THEN "No Issues"
                    WHEN 110 THEN "WARNING: Exceeded Time"
                    WHEN 210 THEN "VIOLATION: Exceeded Time"
                    WHEN 211 THEN "VIOLATION: Expired Pass"
                    WHEN 221 THEN "VIOLATION: Broke Curfew"
                    WHEN 222 THEN "VIOLATION: Inappropriate Behaviour"
                END, "")
            FROM Students
            INNER JOIN Names ON Students.id=Names.rowid
            INNER JOIN LeavePass ON LeavePass.studentID=Students.id
            INNER JOIN Logout ON Logout.leavePassID=LeavePass.id
            LEFT JOIN Login ON Login.logID=Logout.ID
            {}
            LIMIT ?, 20
        '''
        order = "ORDER BY Logout.id DESC"
        if sort == 1:
            order = '''
                ORDER BY CASE WHEN timein IS NULL THEN 1 ELSE 0 END DESC,
                timein DESC,
                Logout.id DESC
            '''
        elif sort == 2:
            order = '''
                ORDER BY remarks DESC, Logout.id DESC
            '''
        cur.execute(sql.format(order), (page * 20 - 20, ))
        logs = cur.fetchall()
    return render_template('log.html',
            logs=logs,
            page=page,
            sort=sort
    )

@app.route('/leavePass')
def leavePass():
    return render_template('leavePass.html')

@app.route('/addLeavePass', methods=['POST'])
def addLeavePass():
    name = request.form['name']
    tp = request.form['type']
    add = request.form['destination']
    with sqlite3.connect("picscan.db") as conn:
        conn.enable_load_extension(True)
        conn.load_extension("./spellfix.so")

        cur = conn.cursor()
        cur.execute('''
            SELECT word, Students.id FROM Names
            INNER JOIN Students
            ON Students.id=Names.rowid
            WHERE word MATCH "*{}*" AND top=1;
        '''.format(name))
        if a:=cur.fetchone():
            name = a[0]
            msg = "Added Leavepass for {}".format(name)
            conn.execute('''
                INSERT INTO LeavePass(studentID, type, destination)
                VALUES (?, ?, ?)
            ''', (a[1], tp, add))
            conn.commit()

        else:
            msg = 'Cannot match "{}"'.format(name)

        return redirect(url_for('index')+"?u="+msg)


def getDat(nam):
    name = nam
    with sqlite3.connect('picscan.db') as conn:
        conn.enable_load_extension(True)
        conn.load_extension("./spellfix.so")
        cur = conn.cursor()
        sql = '''
            SELECT word, gradeAndSection, idNumber, address, CASE isIntern
                WHEN 0 THEN "Extern"
                WHEN 1 THEN "Intern"
            END, CASE inCampus
                WHEN 0 THEN "Out of Campus"
                WHEN 1 THEN "In Campus"
            END
            FROM Students
            INNER JOIN Names ON Students.id=Names.rowid
            WHERE word MATCH ? AND top=1 AND scope=1
        '''
        cur.execute(sql, (name,))
        data = cur.fetchall()
        if len(data):
            data = data[0]
        else:
            return False
    
    keys=['name', 'gradeAndSection', 'idNumber', 'address', 'residence', 'status']
    dat = dict()
    for a, b in zip(keys, data):
        dat[a] = b
    return dat

@app.route('/post', methods=['POST'])
def post():
    global img, status, dat, nam
    image = request.json['image']

    arr = np.frombuffer(base64.b64decode(image), np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    val, img1 = ocr.checkValidity(img)

    if val:
        nam = ocr.getUser(img1)
        dat = getDat(nam)
        if dat['status'] == "In Campus":
            with sqlite3.connect('picscan.db') as conn:
                cur = conn.cursor()
                sql = '''
                    SELECT LeavePass.id FROM LeavePass
                    INNER JOIN Students
                    ON Students.id=LeavePass.studentID
                    LEFT JOIN Logout
                    ON Logout.leavePassID=LeavePass.id
                    WHERE Logout.id IS NULL AND Students.idNumber=?
                '''
                cur.execute(sql, (dat['idNumber'],))
                if row := cur.fetchone():
                    conn.execute("INSERT INTO Logout(leavePassID) VALUES(?)", (row[0],))
                    conn.execute("UPDATE Students SET inCampus=0 WHERE idNumber=?", (dat['idNumber'],))
                    conn.commit()
        else:
            with sqlite3.connect('picscan.db') as conn:
                cur = conn.cursor()
                sql = '''
                    SELECT Logout.id FROM Logout
                    INNER JOIN LeavePass
                    ON Logout.leavePassID=LeavePass.id
                    INNER JOIN Students
                    ON Students.id=LeavePass.studentID
                    LEFT JOIN Login
                    ON Login.logID=Logout.id
                    WHERE Login.logID IS NULL AND Students.idNumber=?
                '''
                cur.execute(sql, (dat['idNumber'],))
                if row := cur.fetchone():
                    conn.execute("INSERT INTO Login(logID) VALUES(?)", (row[0],))
                    conn.execute("UPDATE Students SET inCampus=1 WHERE idNumber=?", (dat['idNumber'],))
                    conn.commit()


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
