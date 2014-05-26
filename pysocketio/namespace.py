from pysocketio.socket import Socket

from pyemitter import Emitter
import logging

log = logging.getLogger(__name__)


class Namespace(Emitter):
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

        self.adapter = self.engine.adapter()(self)

    def run(self, socket):
        """Executes the middleware for an incoming client."""
        return None

    def to(self, name):
        raise NotImplementedError()

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

        if client.socket.ready_state != 'open':
            log.debug('next called after client was closed - ignoring socket')
            return None

        if error is not None:
            log.error(error)
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
        self.emit('connect', socket)
        self.emit('connection', socket)

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

