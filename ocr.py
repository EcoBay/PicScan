#!/bin/python
import sqlite3
import pytesseract
import numpy as np

def checkValidity(img):
    headers = [
        "REPUBLIC OF THE PHILIPPINES",
        "DEPARTMENT OF SCIENCE & TECHNOLOGY",
        "PHILIPPINE SCIENCE HIGH SCHOOL",
        "CAGAYAN VALLEY CAMPUS",
        "Bayombong, Nueva Viscaya"
    ]
    validity = False

    for _ in range(2):
        for i in pytesseract.image_to_string(img[:int(img.shape[1]/2)]).splitlines(): 
            for j in headers:
                if levenshteinDistance(i, j) < len(j) * 0.25:
                    validity = True
                    break
            else:
                continue
            break
        else:
            img = np.rot90(img, 2)
            continue
        break

    return validity, img

def getUser(img):
    img = img[int(img.shape[1]/2):]

    name = max(pytesseract.image_to_string(img).splitlines(), key=len)
    a = int(len(name)*0.1)
    name = name[a:-a]

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

def levenshteinDistance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2 + 1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]

if __name__ == '__main__':
    import cv2
    _, img = checkValidity(cv2.imread('/home/eco/id.jpg'))
    getUser(img)
