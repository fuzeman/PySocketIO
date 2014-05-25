import pysocketio_parser as parser

import logging

log = logging.getLogger(__name__)


class Client(object):
    def __init__(self, engine, socket):
        self.engine = engine
        self.socket = socket

        self.encoder = parser.Encoder()
        self.decoder = parser.Decoder()

        self.sid = socket.sid
        # TODO request

        self.setup()

        self.sockets = []
        self.nsps = {}
        self.connect_buffer = []

    def setup(self):
        self.socket.on('data', self.on_data)\
                   .on('close', self.on_close)

        self.decoder.on('decoded', self.on_decoded)

    def connect(self, name):
        log.debug('connecting to namespace "%s"', name)

        nsp = self.engine.of(name)

        if name != '/' and not self.nsps.get('/'):
            self.connect_buffer.append(name)
            return

        def on_connected(socket):
            self.sockets.append(socket)
            self.nsps[nsp.name] = socket

            if nsp.name == '/' and self.connect_buffer:
                # Connect to buffered namespaces
                for sub_name in self.connect_buffer:
                    self.connect(sub_name)

                self.connect_buffer = None

        nsp.add(self, on_connected)

    def disconnect(self):
        pass

    def remove(self):
        pass

    def close(self):
        pass

    def packet(self, packet, encoded=False, volatile=False):
        if self.socket.ready_state != 'open':
            log.debug('ignoring packet write %s, transport not ready', packet)
            return

        def write(encoded_packets):
            if volatile and not self.socket.transport.writable:
                return

            # Write each packet to socket
            for ep in encoded_packets:
                self.socket.write(ep)

        log.debug('writing packet %s', packet)

        # Packet(s) already encoded, write them to socket
        if encoded:
            return write(packet)

        # Encode packets, write them to socket
        self.encoder.encode(packet, write)

    def on_data(self, data):
        self.decoder.add(data)

    def on_decoded(self, packet):
        p_type = packet.get('type')
        p_nsp = packet.get('nsp')

        if p_type == parser.CONNECT:
            return self.connect(p_nsp)

        socket = self.nsps.get(p_nsp)

        if not socket:
            log.debug('no socket for namespace %s', p_nsp)
            return

        return socket.on_packet(packet)

    def on_close(self, reason, description=None):
        pass

    def destroy(self):
        self.socket.off('data')\
                   .off('close')

        # TODO self.decoder.off('decoded')
