"""
NOTE: Cannot communicate if object class is not known in both services
"""
import time
import socket
from multiprocessing.connection import Listener, Client

MY_IP = socket.gethostbyname(socket.gethostname())
MY_PORT = 54212
AUTHKEY = b'hello I"ts bob'


class UnknownToListener(object):
    def __init__(self, *args, **kwargs):
        self.args = args,
        self.kwargs = kwargs

    def __str__(self):
        return ' '.join((self.__class__.__name__, str(self.args), str(self.kwargs)))


if __name__ == '__main__':
    cmd = UnknownToListener('abc', 0, 'blah', 2, value=1, fun=3)

    with Client((MY_IP, MY_PORT), authkey=AUTHKEY) as client:
        client.send(cmd)
        ack = client.recv()
        print('ACK?', ack)
        time.sleep(1)
