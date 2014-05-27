import pysocketio_client as io
import logging

logging.basicConfig(level=logging.DEBUG)

username = raw_input('Username: ')

socket = io.connect('http://localhost:5000')

@socket.on('connect')
def connected():
    print "connected"

    socket.emit('login', username)

@socket.on('message')
def on_message(data):
    print '[%s] %s' % (data.get('username'), data.get('message'))


while True:
    message = raw_input('>>> ')

    print '[%s] %s' % (username, message)
    socket.emit('message', message)
