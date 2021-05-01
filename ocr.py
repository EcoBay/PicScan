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
    return name


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
