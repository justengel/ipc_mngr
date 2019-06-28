"""
NOTE: Cannot communicate if object class is not known in both services
"""
import socket
import threading
from multiprocessing.connection import Listener, Client

MY_IP = socket.gethostbyname(socket.gethostname())
MY_PORT = 54212
AUTHKEY = b'hello I"ts bob'


alive_event = threading.Event()
alive_event.set()


def listener_handler(alive, client):
    while alive.is_set():
        try:
            obj = client.recv()
            client.send('ACK')
            print('ACK:', obj)
        except EOFError:
            break  # Client disconnected
        except Exception as err:
            client.send('NACK')
            print('NACK:', err)

    print('Client closed {}!'.format(client))


if __name__ == '__main__':
    with Listener((MY_IP, MY_PORT), authkey=AUTHKEY) as listener:
        print('listening . . .')
        while alive_event.is_set():
            sock = listener.accept()
            print('Client connected {}!'.format(sock))
            th = threading.Thread(target=listener_handler, args=(alive_event, sock))
            th.daemon = True  # Python keeps track and a reference of all daemon threads
            th.start()

    alive_event.clear()
    print('listener closed')
