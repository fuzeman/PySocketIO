from pysocketio import Engine, Server

from flask import Flask, render_template
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
io = Engine()


@app.route('/')
def index():
    return render_template('index.html')


users = {}


@io.on('connection')
def on_connection(socket):
    print 'on_connection', socket

    logged_on = False

    @socket.on('message')
    def on_message(message):
        socket.broadcast.emit('message', {
            'username': socket.username,
            'message': message
        })

    @socket.on('login')
    def on_login(username):
        print 'login "%s"' % username

        # Store username on socket
        socket.username = username

        # Update active user list
        users[username] = True

        socket.emit('login', {
            'active': len(users)
        })

        socket.broadcast.emit('user.joined', {
            'username': username,
            'active': len(users)
        })

    @socket.on('disconnect')
    def on_disconnect():
        if not hasattr(socket, 'username'):
            return

        if socket.username not in users:
            return

        del users[socket.username]

        socket.broadcast.emit('user.left', {
            'username': socket.username,
            'active': len(users)
        })



if __name__ == '__main__':
    server = Server(('', 5000), app, io)
    server.serve_forever()
