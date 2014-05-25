import pysocketio_client as io
import logging

logging.basicConfig(level=logging.DEBUG)

username = raw_input('Username: ')

socket = io.connect('http://localhost:5000')

@socket.on('connect')
def connected():
    print "connected"

    socket.emit('login', username)


while True:
    raw_input()
