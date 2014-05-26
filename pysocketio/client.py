import pysocketio_parser as parser

import logging

log = logging.getLogger(__name__)


class Client(object):
    def __init__(self, engine, socket):
        """Client constructor.

        :param engine: Engine
        :type engine: pysocketio.engine.Engine

        :param socket: EIO Socket
        :type socket: pyengineio.socket.Socket
        """
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
        """Sets up event listeners."""
        self.socket.on('data', self.on_data)\
                   .on('close', self.on_close)

        self.decoder.on('decoded', self.on_decoded)

    def connect(self, name):
        """Connects a client to a namespace.

        :param name: Namespace name
        :type name: str
        """
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
        """Disconnects from all namespaces and closes transport."""
        while self.sockets:
            self.sockets.pop(0).disconnect()

        self.close()

    def remove(self, socket):
        """Removes a socket. Called by each `Socket`."""
        if socket not in self.sockets:
            log.debug('ignoring remove for %s', socket.sid)
            return

        self.sockets.remove(socket)
        del self.nsps[socket.nsp.name]

    def close(self):
        """Closes the underlying connection."""
        if self.socket.ready_state != 'open':
            return

        log.debug('forcing transport close')

        self.socket.close()
        self.on_close('forced server close')

    def packet(self, packet, encoded=False, volatile=False):
        """Writes a packet to the transport.

        :param packet: Packet
        :type packet: dict

        :param encoded: Flag indicating the packet has already been encoded
        :type encoded: bool

        :param volatile: Flag indicating the packet is volatile
        :type volatile: bool
        """
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
        """Called with incoming transport data.

        :param data: Data
        :type data: str
        """
        self.decoder.add(data)

    def on_decoded(self, packet):
        """Called when the parser fully decodes a packet.

        :param packet: Decoded packet
        :type packet: dict
        """
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
        """Called upon transport close.

        :param reason: Close reason
        :type reason: str

        :param description: Close description
        :type description: str
        """
        log.debug('client close with reason %s', reason)

        # ignore a potential subsequent `close` event
        self.destroy()

        # `nsps` and `sockets` are cleaned up seamlessly
        for socket in self.sockets:
            socket.on_close(reason)

        # clean up decoder
        self.decoder.destroy()

    def destroy(self):
        self.socket.off('data')\
                   .off('close')

        self.decoder.off('decoded')
