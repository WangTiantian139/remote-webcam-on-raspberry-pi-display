# On remote device such as Raspberry Pi
from flask import Flask
from flask_sockets import Sockets
import numpy as np
import cv2 as cv

app = Flask(__name__)
sockets = Sockets(app)
cap = cv.VideoCapture(0)


@sockets.route('/send-frame')
def send_frame(ws):
    while not ws.closed:
        message = ws.receive()
        if message == "":
            continue
        elif message == "update":
            # Capture frame-by-frame
            ret, frame = cap.read()
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            ret, png = cv.imencode('.png', gray)
            ws.send(png.tostring())
        elif message == "pause":
            continue
        elif message == "stop":
            cap.release()
        else:
            continue


@app.route('/')
def hello():
    return 'Hello World!'


if __name__ == "__main__":
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(
        ('0.0.0.0', 4242), app, handler_class=WebSocketHandler)
    server.serve_forever()
