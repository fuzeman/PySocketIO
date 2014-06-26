import pysocketio_parser as parser

from pyemitter import Emitter
import logging

log = logging.getLogger(__name__)


class Socket(Emitter):
    _emit = Emitter.emit

    def __init__(self, nsp, client):
        """Interface to a `Client` for a given `Namespace`.

        :param nsp: Namespace
        :type nsp: pysocketio.namespace.Namespace

        :param client: Client
        :type client: pysocketio.client.Client
        """
        self.nsp = nsp
        self.client = client
        self.request = self.client.request
        self.adapter = nsp.adapter

        self.sid = client.sid

        self.rooms = []
        self.acks = {}

        self.connected = True
        self.disconnected = False

        self._rooms = []
        self.flags = {}

    @property
    def json(self):
        self.flags['json'] = True
        return self

    @property
    def volatile(self):
        self.flags['volatile'] = True
        return self

    @property
    def broadcast(self):
        self.flags['broadcast'] = True
        return self

    def emit(self, *args):
        """Emits to this client."""
        packet = {
            'type': parser.EVENT,  # TODO BINARY_EVENT
            'data': args
        }

        # TODO ACK

        if self._rooms or self.flags.get('broadcast'):
            self.adapter.broadcast(packet, {
                'except': [self.sid],
                'rooms': self._rooms,
                'flags': self.flags
            })
        else:
            # Dispatch packet
            self.packet(packet)

        # Reset options
        self._rooms = []
        self.flags = {}

        return self

    def to(self, name):
        """Targets a room when broadcasting.

        :param name: Room name
        :type name: str
        """
        if name not in self._rooms:
            self._rooms.append(name)

        return self

    def send(self, *args):
        """Sends a `message` event."""
        return self.emit('message', *args)

    def packet(self, packet, encoded=False, volatile=False):
        """Writes a packet.

        :param packet: Packet
        :type packet: dict

        :param encoded: Flag indicating the packet has already been encoded
        :type encoded: bool

        :param volatile: Flag indicating the packet is volatile
        :type volatile: bool
        """
        if not encoded:
            packet['nsp'] = self.nsp.name

        # Volatile namespace?
        volatile = volatile or (self.flags and self.flags.get('volatile'))

        # Send packet to client
        self.client.packet(packet, encoded, volatile)

    def join(self, room, callback=None):
        """Joins a room.

        :param room: room name
        :type room: str

        :param callback: Callback function
        :type callback: function
        """
        log.debug('joining room %s', room)

        if room in self.rooms:
            return self

        def on_added(error=None):
            if error and callback:
                return callback(error)

            log.debug('joined room %s', room)
            self.rooms.append(room)

            if callback:
                callback()

        self.adapter.add(self.sid, room, on_added)
        return self

    def leave(self, room, callback):
        """Leaves a room.

        :param room: room name
        :type room: str

        :param callback: Callback function
        :type callback: function
        """
        log.debug('leave room %s', room)

        def on_removed(error=None):
            if error and callback:
                callback(error)

            log.debug('left room %s', room)
            self.rooms.remove(room)

            if callback:
                callback()

        self.adapter.remove(self.sid, room, on_removed)
        return self

    def leave_all(self):
        """Leave all rooms."""
        self.adapter.remove_all(self.sid)

    def on_connect(self):
        """Called by `Namespace` upon successful middleware
           execution (ie: authorization)."""
        log.debug('socket connected - writing packet')

        self.join(self.sid)
        self.packet({'type': parser.CONNECT})

        self.nsp.connected[self.sid] = self

    def on_packet(self, packet):
        """Called with each packet. Called by `Client`.

        :param packet: Packet
        :type packet: dict
        """
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
        """Called upon event packet.

        :param packet: Packet
        :type packet: dict
        """
        args = packet.get('data') or []
        log.debug('emitting event %s', args)

        if packet.get('id'):
            log.debug('attaching ack callback to event')
            args.append(self.ack(packet['id']))

        self._emit(*args)

    def ack(self, id):
        """Produces an ack callback to emit with an event.

        :param id: Packet ID
        :type id: str
        """
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
        """Called upon ack packet.

        :param packet: Packet
        :type packet: dict
        """
        p_id = packet.get('id')
        p_data = packet.get('data')

        ack_func = self.acks.get(p_id)

        if ack_func is None:
            log.debug('bad ack %s', p_id)
            return

        log.debug('calling ack %s with %s', p_id, p_data)

        try:
            ack_func(*p_data)
        except Exception, ex:
            log.warn('error while calling ack callback: %s', ex)

        del self.acks[p_id]

    def on_disconnect(self):
        """Called upon client disconnect packet."""
        log.debug('got disconnect packet')
        self.on_close('client namespace disconnect')

    def on_close(self, reason=None):
        """Called upon closing. Called by `Client`.

        :param reason: Close reason
        :type reason: str
        """
        if not self.connected:
            return

        log.debug('closing socket - reason %s', reason)

        self.leave_all()

        self.nsp.remove(self)
        self.client.remove(self)

        self.connected = False
        self.disconnected = True

        del self.nsp.connected[self.sid]
        self.emit('disconnect', reason)

    def error(self, data):
        """Produces an `error` packet.

        :param data: Error detail
        :type data: object
        """
        self.packet({
            'type': parser.ERROR,
            'data': data
        })

    def disconnect(self, close=False):
        """Disconnects this client.

        :param close: if `true`, closes the underlying connnection
        :type close: bool
        """
        if not self.connected:
            return

        if close:
            self.client.disconnect()
        else:
            self.packet({'type': parser.DISCONNECT})
            self.on_close('server namespace disconnect')

        return self
