import argparse
import ipc_mngr

# Share the Command object which is sent between files
from cmd_msgs import Command


if __name__ == '__main__':
    P = argparse.ArgumentParser('Send a schedule command to the scheduler.')
    P.add_argument('cmd_type', nargs="?", default=None, choices=['add', 'remove', 'quit'])
    P.add_argument('--name', type=str, default=None, help='Job name.')
    P.add_argument('--interval', type=int, default=None, help='Time interval to do the task.')
    P.add_argument('--time_unit', type=str, default=None, help='Schedule time unit to do the action at.')
    P.add_argument('--script', type=str, default=None, help='Command line script with arguments to run.')

    ARGS = P.parse_args()

    CMD_TYPE, NAME, SCRIPT, INTERVAL, UNIT = ARGS.cmd_type, ARGS.name, ARGS.script, ARGS.interval, ARGS.time_unit
    if CMD_TYPE is None:
        CMD_TYPE = input('Enter Command Type ("add", "remove", "quit"): ').lower()
        if CMD_TYPE != 'quit':
            NAME = input("Give a Unique Schedule Name: ")
            if CMD_TYPE == 'add':
                SCRIPT = input('Run Script (with command line arguments): ')
                INTERVAL = input('Schedule Interval (leave blank to run now): ')
                try:
                    INTERVAL = int(INTERVAL)
                except:
                    INTERVAL = None
                if INTERVAL is not None:
                    UNIT = input('Schedule unit ("hour", "minute", "day", "days", ...): ').strip()

    COMMAND = Command(CMD_TYPE, NAME, SCRIPT, INTERVAL, UNIT)

    with ipc_mngr.Client(('127.0.0.1', 8111), authkey='12345') as client:
        client.send(COMMAND)
