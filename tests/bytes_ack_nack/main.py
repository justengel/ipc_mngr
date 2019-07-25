"""
Use the ipc_mngr to send raw bytes instead of pickling objects

Example:
 ..code-block:: python

     $ python tests/bytes_ack_nack/main.py --listen

     # New terminal
     $ python tests/bytes_ack_nack/main.py --send --name abc --value 1
     $ python tests/bytes_ack_nack/main.py --send --name fun --value 2

     $ python tests/bytes_ack_nack/main.py --list
     $   List Items:
     $     Item: abc = 1
     $     Item: fun = 2
"""
import ipc_mngr
import argparse

from bytes_com_mngr import BytesAckListener, BytesAckClient, BytesCommandParser


@BytesCommandParser.add_cmd_type
class Item(object):
    ID = 0
    NAME = "Item"

    def __init__(self, name='', value=0):
        self.name = name
        self.value = value

    def decode(self, byts):
        name, value = byts.split(b',')
        self.name = name.decode('utf-8')
        value = value.decode('utf-8')
        try:
            value = int(value)
        except:
            try:
                value = float(value)
            except:
                pass
        self.value = value

    def __bytes__(self):
        return b''.join((self.ID.to_bytes(1, 'big'),
                         str(self.name).encode('utf-8'), b',',
                         str(self.value).encode('utf-8')))


@BytesCommandParser.add_cmd_type
class ListItems(object):
    ID = 1
    NAME = "Item"

    def __init__(self, items=None):
        self.items = items or []

    def decode(self, byts):
        self.items = [BytesCommandParser.decode(item) for item in byts.split(b';') if len(item) > 0]

    def __bytes__(self):
        return self.ID.to_bytes(1, 'big') + b';'.join((bytes(item) for item in self.items))


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description='Listen for commands from a separate process or send commands')

    PARSER.add_argument('--address', default=ipc_mngr.MY_IP, type=str, help='IP Address to connect to')
    PARSER.add_argument('--port', default=54212, type=int, help='Port to connect with')
    PARSER.add_argument('--authkey', default=None, type=bytes, help='Password to protect the connection')

    PARSER.add_argument('--list', action='store_true', help='Send the list items command.')
    PARSER.add_argument('--send', action='store_true', help='If this is a command to send an item.')

    PARSER.add_argument('--name', default=None, type=str, help='Item name to send to the listener')
    PARSER.add_argument('--value', default=0, type=int, help='Item value to send to the listener')

    args = PARSER.parse_args()
    if args.list:
        # ===== Send the ListItems Command and print the list of items when received =====
        with BytesAckClient((args.address, args.port), authkey=args.authkey) as client:
            # Send the command
            client.send(ListItems())

            # Receive the ListItems filled with items to print
            msg = client.recv()
            if isinstance(msg, ListItems):
                print('List Items:')
                for item in msg.items:
                    print('\tItem: {} = {}'.format(item.name, item.value))
            else:
                raise ipc_mngr.IPCError('Invalid response message. The response message should have been ListItems')

    elif args.send:
        # ===== Send an item =====
        name, value = args.name, args.value
        if name is None:
            name, value = input('Enter Name=value: ').split('=')
        item = Item(name.strip(), int(value))

        with BytesAckClient((args.address, args.port), authkey=args.authkey) as client:
            # Send the command
            client.send(item)

    else:
        # ===== Listen for commands =====
        ITEMS = {}

        def msg_handler(sock, cmd):
            """Handle received commands.

            Args:
                sock (multiprocessing.connection.Client): Client socket that received the command.
                cmd (object): Command object that was received.
            """
            if isinstance(cmd, Item):
                # Store the sent item
                ITEMS[cmd.name] = cmd.value

            elif isinstance(cmd, ListItems):
                # Return a list of all items.
                li = ListItems([Item(k, v) for k, v in ITEMS.items()])
                BytesAckListener.send_socket(sock, li)

        listener = BytesAckListener((args.address, args.port), authkey=args.authkey)
        listener.msg_handler = msg_handler
        print('listening ...')
        listener.listen()  # Listen forever
