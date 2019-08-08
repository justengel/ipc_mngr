import socket
import threading
import time
from multiprocessing.connection import Listener as MpListener, Client as MpClient


__all__ = ['IPCError', 'MY_IP', 'get_local_addrs', 'Listener', 'Client']


class IPCError(Exception):
    pass


MY_IP = socket.gethostbyname(socket.gethostname())


def get_local_addrs():
    """Return all of the local IP Addresses."""
    return [addr[4][0] for addr in socket.getaddrinfo(socket.gethostname(), None)]


class Listener(MpListener):
    """Process server to listen for incoming commands.

    Args:
        address (tuple/object): The address to be used by the bound socket or named pipe (EX: "IP Address", Port)
        family (socket.family/str)[None]: Type of socket or named pipe to use (EX: 'AF_INET', 'AF_UNIX', 'AF_PIPE')
        backlog (int)[1]: If a socket is used backlog is passed to the listen() method
        authkey (bytes)[None]: The secret key (password) for an HMAC-based authentication challenge. No auth if None

    Raises:
        AuthenticationError: If authkey is given and authentication fails
    """

    MY_IP = MY_IP
    get_local_addrs = staticmethod(get_local_addrs)

    def __init__(self, address=None, family=None, backlog=1, authkey=None, alive=None):
        """Initialize the listener object.

        Args:
            address (tuple/object): The address to be used by the bound socket or named pipe (EX: "IP Address", Port)
            family (socket.family/str)[None]: Type of socket or named pipe to use (EX: 'AF_INET', 'AF_UNIX', 'AF_PIPE')
            backlog (int)[1]: If a socket is used backlog is passed to the listen() method
            authkey (bytes)[None]: The secret key (password) for an HMAC-based authentication challenge. No auth if None
            alive (threading.Event) [None]: Threading alive Event to control the running state.

        Raises:
            AuthenticationError: If authkey is given and authentication fails
        """
        if alive is None:
            alive = threading.Event()
        self.alive = alive

        if isinstance(authkey, str):
            authkey = authkey.encode('utf-8')

        self.client_lock = threading.RLock()
        self.clients = {}  # Hold {address: sock}
        self._thread = None
        super(Listener, self).__init__(address=address, family=family, backlog=backlog, authkey=authkey)

    @classmethod
    def msg_handler(cls, sock, cmd):
        """Main function to handle the incoming (received) command.

        Args:
            sock (multiprocessing.connection.Connection): Client socket in case you need to respond to the given command
            cmd (object): Command object that was sent to this process
        """
        # Do processing here
        pass

    @classmethod
    def error_handler(cls, sock, error):
        """Handle the error that occurred while trying to receive and handle the incoming command.

        Args:
            sock (multiprocessing.connection.Connection): Client socket in case you need to respond to the given command
            error (Exception): Error that occurred
        """
        pass

    @staticmethod
    def recv_socket(sock):
        """Receive data from the connection."""
        return sock.recv()

    @staticmethod
    def send_socket(sock, data):
        """Send data to the connection."""
        sock.send(data)

    def broadcast(self, data):
        """Broadcast data to all clients."""
        with self.client_lock:
            for addr, sock in self.clients.items():
                # try:
                self.send_socket(sock, data)
                # except (ValueError, TypeError, Exception) as err:
                #     pass

    def client_connected(self, sock, address):
        """Notify that a client was connected.

        Args:
            sock (socket.socket/Connection): Client socket that was accepted.
            address (tuple): Tuple of ('IP Address', port)
        """
        with self.client_lock:
            self.clients[address] = sock
        # print('Client connected {}!'.format(id(sock)))

    def client_disconnected(self, sock, address):
        """Notify that a client was disconnected.

        Args:
            sock (socket.socket/Connection): Client socket that was accepted.
            address (tuple): Tuple of ('IP Address', port)
        """
        with self.client_lock:
            try:
                self.clients.pop(address)
            except (KeyError, TypeError, Exception):
                pass
        # print('Client disconnected {}!'.format(id(sock)))

    def listener_handler(self, alive, sock, address):
        """Continuously listen for communication"""
        self.client_connected(sock, address)

        while alive.is_set():
            cmd = None
            try:
                cmd = self.recv_socket(sock)
                self.msg_handler(sock, cmd)  # Custom user function
            except (EOFError, ConnectionResetError):
                break  # Socket disconnected
            except IPCError as err:
                self.error_handler(sock, err)

        self.client_disconnected(sock, address)

    def is_running(self):
        """Return if the Listener is running and listening for connections to run commands."""
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
        """Listen for incoming connections and block forever."""
        self.alive.set()

        while self.alive.is_set():
            try:
                sock = self.accept()
                address = self.last_accepted
                th = threading.Thread(target=self.listener_handler, args=(self.alive, sock, address))
                th.daemon = True  # Python keeps track and a reference of all daemon threads
                th.start()
            except OSError:
                break

        self.close()

    run = listen

    def stop(self):
        """Stop listening."""
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
        """Close the bound socket or named pipe of `self`."""
        self.stop()
        super(Listener, self).close()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()
        return False


class Client(object):
    """Send a command to a listener process.

    Args:
        address (tuple/object): The address to be used by the bound socket or named pipe (EX: "IP Address", Port)
        family (socket.family/str)[None]: Type of socket or named pipe to use (EX: 'AF_INET', 'AF_UNIX', 'AF_PIPE')
        authkey (bytes)[None]: The secret key (password) for an HMAC-based authentication challenge. No auth if None

    Raises:
        AuthenticationError: If authkey is given and authentication fails
    """

    MY_IP = MY_IP
    get_local_addrs = staticmethod(get_local_addrs)

    def __init__(self, address, family=None, authkey=None):
        """Create the client connection to another process.

        Args:
            address (tuple/object): The address to be used by the bound socket or named pipe (EX: "IP Address", Port)
            family (socket.family/str)[None]: Type of socket or named pipe to use (EX: 'AF_INET', 'AF_UNIX', 'AF_PIPE')
            authkey (bytes)[None]: The secret key (password) for an HMAC-based authentication challenge. No auth if None

        Raises:
            AuthenticationError: If authkey is given and authentication fails
        """
        if isinstance(authkey, str):
            authkey = authkey.encode('utf-8')

        # Connection settings
        self.address = address
        self.family = family
        # self.authkey = authkey  # Probably not good to save the authkey
        self.client = None
        self.connect(address, family, authkey)

    def connect(self, address=None, family=None, authkey=None):
        """Connect the multiprocessing client."""
        if address is not None:
            self.address = address
        if family is not None:
            self.family = family
        self.client = MpClient(self.address, family=self.family, authkey=authkey)  # Why is this a function!? F

    def msg_handler(self, cmd):
        """Handle the response after sending a command.

        This is where you would receive an ack or nack from the socket.

        Args:
            cmd (object): Command that was sent.

        Returns:
            success (bool): True if the message sent successfully!
        """
        return True

    @staticmethod
    def recv_socket(sock):
        """Receive data from the connection."""
        return sock.recv()

    @staticmethod
    def send_socket(sock, data):
        """Send data to the connection."""
        sock.send(data)

    def send(self, cmd):
        """Send the data to the server."""
        self.send_socket(self.client, cmd)
        return self.msg_handler(cmd)

    def recv(self):
        """Receive data from the server."""
        return self.recv_socket(self.client)

    def poll(self, timeout=0.0):
        """Whether there is any input available to be read"""
        return self.client.poll(timeout=timeout)

    @property
    def closed(self):
        """True if the connection is closed"""
        return self.client.closed

    @property
    def readable(self):
        """True if the connection is readable"""
        return self.client.readable

    @property
    def writable(self):
        """True if the connection is writable"""
        return self.client.writable

    def fileno(self):
        """File descriptor or handle of the connection"""
        return self.client.fileno()

    def close(self):
        """Close the connection"""
        time.sleep(0.01)  # Could be sending a message
        self.client.close()

    stop = close

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()
        return False
