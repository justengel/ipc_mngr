import ipc_mngr
import argparse


class Item(object):
    def __init__(self, name='', value=0):
        self.name = name
        self.value = value


class ListItems(ipc_mngr.CommandInterface):
    def __init__(self, items=None):
        self.items = items or []


# COMS
ITEMS = {}


def cmd_handler(sock, cmd):
    """Handle received commands.

    Args:
        sock (multiprocessing.connection.Client): Client socket that received the command.
        cmd (object): Command object that was received.
    """
    global ITEMS
    if isinstance(cmd, Item):
        # Store the sent item
        ITEMS[cmd.name] = cmd.value
    elif isinstance(cmd, ListItems):
        # Return a list of all items.
        li = ListItems([Item(k, v) for k, v in ITEMS.items()])
        sock.send(li)


def print_list(client):
    """Recv the list items response and print the items."""
    cmd = client.recv()
    print('List Items:')
    for item in cmd.items:
        print('\tItem: {} = {}'.format(item.name, item.value))


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
        ipc_mngr.send_command(ListItems(), args.address, args.port, args.authkey, response_handler=print_list)

    elif args.send:
        name, value = args.name, args.value
        if name is None:
            name, value = input('Enter Name=value: ').split('=')
        item = Item(name.strip(), int(value))
        ipc_mngr.send_command(item, args.address, args.port, args.authkey)

    else:
        ipc_mngr.run_listener(cmd_handler, args.address, args.port, args.authkey)
