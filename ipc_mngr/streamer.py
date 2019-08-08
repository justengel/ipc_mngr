import time
import threading

from .com_mngr import Listener, Client, IPCError


__all__ = ['Streamer', 'StreamClient', 'IPCError']


class Streamer(Listener):
    def stream(self, data):
        """Broadcast data to all clients."""
        self.broadcast(data)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()
        return False


class StreamClient(Client):
    def __init__(self, address, family=None, authkey=None, alive=None, reconnect=True):
        """Create the client connection to another process.

        Warning:
            This class saves the authkey if reconnect is True!

        Args:
            address (tuple/object): The address to be used by the bound socket or named pipe (EX: "IP Address", Port)
            family (socket.family/str)[None]: Type of socket or named pipe to use (EX: 'AF_INET', 'AF_UNIX', 'AF_PIPE')
            authkey (bytes)[None]: The secret key (password) for an HMAC-based authentication challenge. No auth if None
                Warning! This class saves the authkey when reconnect is True.
            alive (threading.Event) [None]: Threading alive Event to control the running state.
            reconnect (bool)[True]: Try to reconnect when disconnected.

        Raises:
            AuthenticationError: If reconnect is False, authkey is given, and authentication fails
        """
        if isinstance(authkey, str):
            authkey = authkey.encode('utf-8')

        if alive is None:
            alive = threading.Event()
        self.alive = alive
        self._thread = None
        self.reconnect = reconnect
        self._authkey = None

        if self.reconnect:
            self._authkey = authkey
        super(StreamClient, self).__init__(address, family, authkey=authkey)

    def is_connected(self):
        """Return if the client is connected."""
        return self.client is not None

    def connect(self, address=None, family=None, authkey=None):
        """Connect the multiprocessing client."""
        if self.reconnect:
            if authkey is None:
                authkey = self._authkey
            else:
                self._authkey = authkey

            # Try to connect
            try:
                super(StreamClient, self).connect(address=address, family=family, authkey=authkey)
            except (EOFError, OSError, ConnectionResetError, ConnectionRefusedError):
                self.client = None
        else:
            # Connect or error
            super(StreamClient, self).connect(address=address, family=family, authkey=authkey)

    @classmethod
    def stream_handler(cls, client, data):
        """Main function to handle the incoming (received) stream data.

        Args:
            client (multiprocessing.connection.Connection): Client socket in case you need to respond to the given data.
            data (object): Data object that was streamed to this client.
        """
        # Do processing here
        pass

    def is_running(self):
        """Return if the thread is running."""
        try:
            return self.alive.is_set()
        except AttributeError:
            return False

    def start(self):
        """Start the stream client thread."""
        self.alive.set()
        self._thread = threading.Thread(target=self.listen)
        self._thread.daemon = True
        self._thread.start()

    def listen(self):
        """Continuously listen for communication"""
        self.alive.set()
        while self.is_running():
            if self.client is None:
                time.sleep(0.01)
                self.connect()
                if self.client is None:
                    continue

            try:
                data = self.recv_socket(self.client)
                self.stream_handler(self.client, data)
            except (EOFError, ConnectionResetError):
                self.client = None
                if not self.reconnect:
                    break

        self.alive.clear()

    run = listen

    def stop(self):
        """Stop listening"""
        try:
            self.alive.clear()
        except:
            pass
        try:
            self._thread.join(0)
        except:
            pass
        self._thread = None

    def close(self):
        """Close the connection"""
        self.stop()
        super(StreamClient, self).close()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()
        return False
