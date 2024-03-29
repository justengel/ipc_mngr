"""
Simple example of a service that saves items which can be added or requested from a separate process.

Example:
 ..code-block:: python

     $ python tests/run_send_recv.py --listen

     # New terminal
     $ python tests/run_send_recv.py --send --name abc --value 1
     $ python tests/run_send_recv.py --send --name fun --value 2

     $ python tests/run_send_recv.py --list
     $   List Items:
     $     Item: abc = 1
     $     Item: fun = 2
"""
import ipc_mngr
import argparse


class Item(object):
    def __init__(self, name='', value=0):
        self.name = name
        self.value = value


class ListItems(object):
    def __init__(self, items=None):
        self.items = items or []


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
        with ipc_mngr.Client((args.address, args.port), authkey=args.authkey) as client:
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

        with ipc_mngr.Client((args.address, args.port), authkey=args.authkey) as client:
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
                sock.send(li)

        listener = ipc_mngr.Listener((args.address, args.port), authkey=args.authkey)
        listener.msg_handler = msg_handler
        print("listening ...")
        listener.listen()  # Listen forever
