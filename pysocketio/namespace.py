from pysocketio.socket import Socket
import pysocketio_parser as parser

from pyemitter import Emitter
import logging

log = logging.getLogger(__name__)


class Namespace(Emitter):
    _emit = Emitter.emit

    def __init__(self, engine, name):
        """Namespace constructor.

        :param engine: Engine
        :type engine: pysocketio.engine.Engine

        :param name: Namespace name
        :type name: str
        """
        self.engine = engine
        self.name = name

        self.sockets = []
        self.connected = {}

        self.middleware = []
        self.adapter = self.engine.adapter()(self)

        self.rooms = []
        self.flags = {}

    @property
    def json(self):
        self.flags['json'] = True
        return self

    def use(self, func):
        """Sets up namespace middleware."""
        self.middleware.append(func)
        return self

    def run(self, socket):
        """Executes the middleware for an incoming client."""
        for func in self.middleware:
            error = func(socket)

            if error:
                return error

        return None

    def to(self, name):
        """Targets a room when emitting.

        :param name: Room name
        :type name: str
        """
        if name not in self.rooms:
            self.rooms.append(name)

        return self

    def add(self, client, on_connected=None):
        """Adds a new client.

        :param client: Client
        :type client: pysocketio.client.Client

        :param on_connected: Connected callback
        :type on_connected: function
        """
        log.debug('adding socket to nsp "%s"', self.name)

        socket = Socket(self, client)

        # Execute middleware
        error = self.run(socket)

        if client.conn.ready_state != 'open':
            log.debug('next called after client was closed - ignoring socket')
            return None

        if error:
            socket.error(error)
            return None

        # track socket
        self.sockets.append(socket)

        # it's paramount that the internal `onconnect` logic
        # fires before user-set events to prevent state order
        # violations (such as a disconnection before the connection
        # logic is complete)
        socket.on_connect()

        if on_connected:
            on_connected(socket)

        # fire user-set events
        self._emit('connect', socket)
        self._emit('connection', socket)

        return socket

    def remove(self, socket):
        """Removes a client. Called by each `Socket`.

        :param socket: Socket
        :type socket: pysocketio.socket.Socket
        """
        if socket not in self.sockets:
            log.debug('ignoring remove for %s', socket.sid)
            return

        self.sockets.remove(socket)

    def emit(self, *args):
        """Emits to all clients."""
        packet = {
            'type': parser.EVENT,  # TODO BINARY_EVENT
            'data': args
        }

        # TODO ACK callback check

        self.adapter.broadcast(packet, {
            'rooms': self.rooms,
            'flags': self.flags
        })

        # Reset options
        self.rooms = []
        self.flags = {}

        return self

    def send(self, *args):
        """Sends a `message` event to all clients."""
        return self.emit('message', *args)
