import pyengineio


class Server(pyengineio.Server):
    def __init__(self, listener, application, engine, *args, **kwargs):
        super(Server, self).__init__(
            listener, application, engine.eio,
            *args, **kwargs
        )
