class TKeyError(Exception):
    pass

class TKeyConnectionError(TKeyError):
    pass

class TKeyWriteError(TKeyError):
    pass

class TKeyReadError(TKeyError):
    pass

class TKeyStatusError(TKeyError):
    pass

class TKeyProtocolError(TKeyError):
    pass
