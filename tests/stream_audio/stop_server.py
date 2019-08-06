"""
Send a command to the stream_server to stop streaming audio data.
"""
import time
import ipc_mngr


if __name__ == '__main__':
    with ipc_mngr.Client(('127.0.0.1', 8222), authkey='12345') as client:
        client.send('stop')
        time.sleep(1)
