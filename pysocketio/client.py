import logging

log = logging.getLogger(__name__)


class Client(object):
    def __init__(self, engine, socket):
        self.engine = engine
        self.socket = socket
        #
        #  TODO encoder, decoder

        self.sid = socket.sid
        # TODO request

        self.setup()

        self.sockets = []
        self.nsps = {}
        self.connect_buffer = []

    def setup(self):
        self.socket.on('data', self.on_data)\
                   .on('close', self.on_close)

        # TODO decoder.on('decoded',...)

    def connect(self, name):
        log.debug('connecting to namespace "%s"', name)

        nsp = self.engine.of(name)

        if name != '/' and not self.nsps.get('/'):
            self.connect_buffer.append(name)
            return

        @nsp.add(self)
        def on_connected(socket):
            self.sockets.append(socket)
            self.nsps[nsp.name] = socket

            if nsp.name == '/' and self.connect_buffer:
                # Connect to buffered namespaces
                for sub_name in self.connect_buffer:
                    self.connect(sub_name)

                self.connect_buffer = None

    def disconnect(self):
        pass

    def remove(self):
        pass

    def close(self):
        pass

    def send(self, packet, encoded=False, volatile=False):
        pass

    def on_data(self, data):
        pass

    def on_decoded(self, packet):
        pass

    def on_close(self, reason, description=None):
        pass

    def destroy(self):
        self.socket.off('data')\
                   .off('close')

        # TODO self.decoder.off('decoded')
