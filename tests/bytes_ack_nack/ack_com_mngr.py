"""This module is meant for message passing using bytes instead of pickling."""
import socket
from ipc_mngr.com_mngr import IPCError, Listener, Client
from ipc_mngr.cmd_parser import CommandParser, CommandInterface


__all__ = ['ACK', 'NACK', 'AckListener', 'AckClient', 'AckListenerMixin', 'AckClientMixin']


@CommandParser.add_cmd_type
class ACK(CommandInterface):
    ID = 0xff
    NAME = 'ACK'

    def __init__(self, cmd=''):
        """Initialize the ack.

        Args:
            cmd (str/CommandInterface): Command name.
        """
        if not isinstance(cmd, str):
            cmd = cmd.__class__.__name__
        self.cmd = cmd

    def compare(self, cmd):
        """Return if the given command equals this command"""
        if not isinstance(cmd, str):
            cmd = cmd.__class__.__name__
        return self.cmd == cmd

    def decode(self, byts):
        self.cmd = byts.decode('utf-8')

    def __bytes__(self):
        return b''.join((
            self.ID.to_bytes(1, 'big'),
            self.cmd.encode('utf-8')
            ))


@CommandParser.add_cmd_type
class NACK(CommandInterface):
    ID = 0xfe
    NAME = 'NACK'

    def __init__(self, error=''):
        self.error = str(error)

    def decode(self, byts):
        self.error = byts.decode('utf-8')

    def __bytes__(self):
        return b''.join((
            self.ID.to_bytes(1, 'big'),
            str(self.error).encode('utf-8')
            ))


class AckListenerMixin(object):
    """Process server to listen for incoming commands and ack/nack with the client."""
    def listener_handler(self, alive, sock):
        """Continuously listen for communication"""
        self.client_connected(sock)

        while alive.is_set():
            cmd = None
            try:
                cmd = self.recv_socket(sock)
                self.ack(sock, cmd)
                self.msg_handler(sock, cmd)  # Custom user function
            except EOFError as err:
                break  # Socket disconnected
            except IPCError as err:
                self.nack(sock, err)
                self.error_handler(sock, err)

        self.client_disconnected(sock)

    def ack(self, sock, cmd):
        self.send_socket(sock, ACK(cmd))  # Acknowledge that data was received

    def nack(self, sock, error):
        try:
            self.send_socket(sock, NACK(error))  # Send not acknowledge because there was an error
        except:
            pass


class AckClientMixin(object):
    """Send a command to a listener process and wait for an ack/nack."""

    ATTEMPTS = 5

    def msg_handler(self, cmd):
        """Handle the response after sending a command.

        This is where you would receive an ack or nack from the socket. Use self.recv() to decode the incoming data.

        Args:
            cmd (object): Command that was sent.

        Returns:
            success (bool): True if the message sent successfully! False to retry sending the message
        """
        success = False
        # Poll to prevent waiting forever on blocking recv.
        if self.poll(timeout=3):
            msg = self.recv()  # Blocking receive the item
            if isinstance(msg, ACK):
                # Mark that the message was ACK'ed
                success = msg.compare(cmd)
            elif isinstance(msg, NACK):
                print('NACK:', msg.error)
                success = False
            else:
                print('ACK/NACK was not sent!')
        return success

    @classmethod
    def error_handler(cls, sock, error):
        """Handle the error that occurred while trying to receive and handle the incoming command.

        Args:
            sock (multiprocessing.connection.Connection): Client socket in case you need to respond to the given command
            error (Exception): Error that occurred
        """
        pass

    def notify_retry(self, attempt):
        """Notify that a send command is retrying.

        Args:
            attempt (int): Attempt number
        """
        # print('Retrying to send the command attempt {} of {} . . .'.format(attempt, self.attempts))
        pass

    def send(self, cmd):
        """Repeatedly send the command until an ACK is received."""
        success = False
        trials = 0

        while not success and trials <= self.ATTEMPTS:
            try:
                # Check to print retry
                if trials > 0:
                    self.notify_retry(trials)

                # Send the command
                self.send_socket(self.client, cmd)
                success = self.msg_handler(cmd)
            except EOFError:
                break  # socket disconnected
            except (socket.error, Exception) as error:
                self.error_handler(self.client, error)

            trials += 1

        if not success:
            raise IPCError('Command Failed! Did not receive Acknowledgement for command {}'.format(str(cmd)))


class AckListener(AckListenerMixin, Listener):
    """Process server to listen for incoming commands and ack/nack with the client."""
    pass


class AckClient(AckClientMixin, Client):
    """Send a command to a listener process and wait for an ack/nack."""
    pass
