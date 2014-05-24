from pysocketio.client import Client
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

        # initialize engine
        log.debug('creating engine.io instance with options %s', options)

        self.eio = pyengineio.Engine(options)\
            .on('connection', self.on_connection)

    def on_connection(self, socket):
        log.debug('incoming connection with sid "%s"', socket.sid)

        client = Client(self, socket)
        client.connect('/')
