import pysocketio_parser as parser

from pyemitter import Emitter
import logging

log = logging.getLogger(__name__)


class Socket(Emitter):
    _emit = Emitter.emit

    def __init__(self, nsp, client):
        self.nsp = nsp
        self.client = client
        self.adapter = nsp.adapter

        self.sid = client.sid

        self.rooms = []
        self.flags = {}

    def emit(self, *args):
        packet = {
            'type': parser.EVENT,  # TODO BINARY_EVENT
            'data': args
        }

        # TODO ACK

        if self.rooms or self.flags.get('broadcast'):
            self.adapter.broadcast(packet, {
                'except': [self.sid],
                'rooms': self.rooms,
                'flags': self.flags
            })
        else:
            # dispatch packet
            self.packet(packet)

        # reset flags
        self.rooms = []
        self.flags = {}

        return self

    @property
    def broadcast(self):
        self.flags['broadcast'] = True
        return self

    @property
    def volatile(self):
        self.flags['volatile'] = True
        return self

    def to(self, name):
        if name not in self.rooms:
            self.rooms.append(name)

        return self

    def send(self, *args):
        return self.emit('message', *args)

    def packet(self, packet, encoded=False, volatile=False):
        if not encoded:
            packet['nsp'] = self.nsp.name

        # Volatile namespace?
        volatile = volatile or (self.flags and self.flags.get('volatile'))

        # Send packet to client
        self.client.packet(packet, encoded, volatile)

    def join(self, room, callback=None):
        log.debug('joining room %s', room)

        def on_added(error=None):
            if error and callback:
                return callback(error)

            log.debug('joined room %s', room)
            self.rooms.append(room)

            if callback:
                callback()


        self.adapter.add(self.sid, room, on_added)

    def leave(self, room):
        pass

    def leave_all(self):
        pass

    def on_connect(self):
        log.debug('socket connected - writing packet')

        self.join(self.sid)
        self.packet({'type': parser.CONNECT})

        self.nsp.connected[self.sid] = self

    def on_packet(self, packet):
        p_type = packet.get('type')

        if p_type == parser.EVENT:
            return self.on_event(packet)

        if p_type == parser.BINARY_EVENT:
            return self.on_event(packet)

        if p_type == parser.ACK:
            return self.on_ack(packet)

        if p_type == parser.DISCONNECT:
            return self.on_disconnect()

        if p_type == parser.ERROR:
            return self._emit('error', packet.get('data'))

    def on_event(self, packet):
        args = packet.get('data') or []
        log.debug('emitting event %s', args)

        if packet.get('id'):
            log.debug('attaching ack callback to event')
            args.append(self.ack(packet['id']))

        self._emit(*args)

    def ack(self, id):
        sent = False

        def ack_callback(*args):
            # Prevent double callbacks
            if sent:
                return

            log.debug('sending ack %s', args)

            self.packet({
                'id': id,
                'type': parser.ACK,
                'data': args
            })

        return ack_callback


    def on_ack(self, packet):
        pass

    def on_disconnect(self):
        pass

    def on_close(self):
        pass

    def error(self, data):
        pass

    def disconnect(self, close=False):
        pass
