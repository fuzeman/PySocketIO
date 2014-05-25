from pysocketio.client import Client
from pysocketio.namespace import Namespace
from pysocketio_adapter import Adapter
import pyengineio

from pyemitter import Emitter
import logging

log = logging.getLogger(__name__)


class Engine(Emitter):
    def __init__(self, options=None):
        """Engine constructor.

        :param options: Engine configuration options
        :type options: dict
        """
        if options is None:
            options = {}

        options['path'] = options.get('path') or '/socket.io'

        # Setup
        self._adapter = None

        self.nsps = {}
        self.adapter(options.get('adapter') or Adapter)
        self.sockets = self.of('/')

        # Set proxy methods to '/' namespace
        for name in ['on']:
            func = getattr(self.sockets, name)
            setattr(self, name, func)

        # Initialize engine.io
        log.debug('creating engine.io instance with options %s', options)

        self.eio = pyengineio.Engine(options) \
            .on('connection', self.on_connection)

    def adapter(self, adapter=None):
        if not adapter:
            return self._adapter

        self._adapter = adapter

        for nsp in self.nsps:
            nsp.adapter = self._adapter(nsp)

        return self

    def on_connection(self, socket):
        log.debug('incoming connection with sid "%s"', socket.sid)

        client = Client(self, socket)
        client.connect('/')

    def of(self, name):
        if not self.nsps.get(name):
            log.debug('initializing namespace "%s"', name)
            self.nsps[name] = Namespace(self, name)

        return self.nsps[name]
