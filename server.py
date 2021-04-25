#!/bin/python

from flask import Flask, request
app = Flask(__name__)

@app.route('/post', methods=['POST'])
def upload_pic():
    image = request.json['image']
    print(image[:20])
    return '', 204

if __name__ == '__main__':
    app.run('192.168.1.115', 5000)
