import threading
from .com_mngr import Listener, Client, IPCError


__all__ = ['Streamer', 'StreamClient', 'IPCError']


class Streamer(Listener):
    def stream(self, data):
        """Broadcast data to all clients."""
        self.broadcast(data)


class StreamClient(Client):
    def __init__(self, address, family=None, authkey=None, alive=None):
        """Create the client connection to another process.

        Args:
            address (tuple/object): The address to be used by the bound socket or named pipe (EX: "IP Address", Port)
            family (socket.family/str)[None]: Type of socket or named pipe to use (EX: 'AF_INET', 'AF_UNIX', 'AF_PIPE')
            authkey (bytes)[None]: The secret key (password) for an HMAC-based authentication challenge. No auth if None
            alive (threading.Event) [None]: Threading alive Event to control the running state.

        Raises:
            AuthenticationError: If authkey is given and authentication fails
        """
        if alive is None:
            alive = threading.Event()
        self.alive = alive

        self._thread = None
        super().__init__(address, family=family, authkey=authkey)

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
            try:
                data = self.recv_socket(self.client)
                self.stream_handler(self.client, data)
            except (EOFError, ConnectionResetError, Exception):
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
        super().close()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()
        return False
