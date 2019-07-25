import argparse
import ipc_mngr

# Share the Command object which is sent between files
from cmd_msgs import Command, ListJobs


if __name__ == '__main__':
    P = argparse.ArgumentParser('List all of the jobs in the schedule')
    ARGS = P.parse_args()

    with ipc_mngr.Client(('127.0.0.1', 8111), authkey='12345') as client:
        client.send(ListJobs())

        li = client.recv()
        print('Current Schedule:')
        for name, script in li.jobs.items():
            print('\t', name, ':', script)
