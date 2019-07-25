"""This module is meant for message passing using bytes instead of pickling."""
from ipc_mngr.com_mngr import Listener, Client
from ipc_mngr.cmd_parser import CommandParser
from tests.bytes_ack_nack.ack_com_mngr import AckListenerMixin, AckClientMixin, ACK, NACK


__all__ = ['BytesCommandParser', 'BytesListener', 'BytesClient', 'BytesAckListener', 'BytesAckClient']


class BytesCommandParser(CommandParser):
    CMD_TYPES = {}  # ID: Command, NAME: Command,
    REQUIRED_ATTRS = ['ID', 'NAME', 'decode', '__bytes__']

    @classmethod
    def encode(cls, cmd_name, *args, **kwargs):
        """Encode the given command to bytes"""
        if isinstance(cmd_name, (str, int, type)):
            cmd = cls.get_cmd_type(cmd_name)(*args, **kwargs)
        else:
            cmd = cmd_name  # Simply convert to bytes below
        return bytes(cmd)

    @classmethod
    def decode(cls, byts):
        """Decode a command from the given bytes."""
        cmd_id = byts[0]
        cmd = cls.get_cmd_type(cmd_id)()
        cmd.decode(byts[1:])
        return cmd


BytesCommandParser.add_cmd_type(ACK)
BytesCommandParser.add_cmd_type(NACK)


class BytesListener(Listener):
    """Process server to listen for incoming bytes commands. All commands are sent and received as bytes."""

    @classmethod
    def cmd_handler(cls, sock, cmd):
        """Main function to handle the incoming (received) command.

        Args:
            sock (multiprocessing.connection.Connection): Client socket in case you need to respond to the given command
            cmd (object): Command object that was sent to this process
        """
        # Do processing here
        # Send data with (cls.send_client(sock, cmd)
        pass

    @staticmethod
    def recv_socket(sock):
        """Receive data from the connection."""
        return BytesCommandParser.decode(sock.recv())

    @staticmethod
    def send_socket(sock, data):
        """Send data to the connection."""
        sock.send(BytesCommandParser.encode(data))


class BytesClient(Client):
    """Send a command to a listener process. All commands are sent and received as bytes."""

    @staticmethod
    def recv_socket(sock):
        """Receive data from the connection."""
        return BytesCommandParser.decode(sock.recv())

    @staticmethod
    def send_socket(sock, data):
        """Send data to the connection."""
        sock.send(BytesCommandParser.encode(data))


class BytesAckListener(AckListenerMixin, BytesListener):
    """Process server to listen for incoming commands and ack/nack with the client."""
    pass


class BytesAckClient(AckClientMixin, BytesClient):
    """Send a command to a listener process and wait for an ack/nack."""
    pass
