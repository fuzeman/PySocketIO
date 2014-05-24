from pysocketio import Engine, Server

from flask import Flask, render_template
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
io = Engine()


@app.route('/')
def index():
    return render_template('index.html')


@io.on('connection')
def on_connection(socket):
    print 'on_connection', socket


if __name__ == '__main__':
    server = Server(('', 5000), app, io)
    server.serve_forever()
