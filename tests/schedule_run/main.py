"""
Example to show how to use this with a long running schedule process which can have jobs dynamically added or removed.

Example:
 ..code-block:: python

     $ python tests/schedule_run/main.py

     # New terminal
     $ python tests/schedule_run/send_schedule.py add --name hello --script "hello.bat 2 seconds" --interval 2 --time_unit seconds
     $ python tests/schedule_run/send_schedule.py add --name "hello 2" --script "hello.bat 1 minute" --interval 1 --time_unit minute

     $ python tests/schedule_run/list_schedule.py
     Current Schedule:
         hello : hello.bat 2 seconds
         hello 2 : hello.bat 1 minute

     $ python tests/schedule_run/send_schedule.py quit
"""
import threading
import time
import ipc_mngr
import schedule
import shlex
import subprocess

# Share the Command object which is sent between files
from cmd_msgs import Command, ListJobs


JOBS = {}  # Save Jobs. Not runnable


class RunScript(object):
    def __init__(self, script):
        self.script = script
        self.process = None

    def stop(self):
        try:
            self.process.terminate()
        except:
            pass
        self.process = None

    def start(self):
        try:
            if self.process.poll() is not None:
                self.stop()
        except:
            pass
        if self.process is None:
            self.process = subprocess.Popen(shlex.split(self.script))

    def __call__(self):
        self.start()

    def __eq__(self, other):
        try:
            return self.script == other.script
        except:
            return False

    def __hash__(self):
        return self.script


def stop_script(name):
    """Stop the script with the given name."""
    job = JOBS.get(name, None)
    try:
        runnable = job.job_func
        runnable.stop()
    except:
        pass
    try:
        schedule.cancel_job(job)
    except:
        pass
    print('Canceled script {}'.format(name))


def start_script(name, script, interval, time_unit):
    """Run the script or schedule the script with the given name."""
    if interval is None:
        # Run Now
        RunScript(script).start()
        print('Running script {}'.format(name))
    else:
        if name in JOBS:
            stop_script(name)

        # Run on schedule
        runnable = RunScript(script)

        # schedule.every(1).hour.do(job)
        JOBS[name] = job = schedule.every(interval)  # Get Job for interval
        getattr(job, time_unit).do(runnable)
        print('Scheduled script {}'.format(name))


if __name__ == '__main__':
    listener = ipc_mngr.Listener(('127.0.0.1', 8111), authkey=b'12345')

    def msg_handler(sock, cmd):
        """Handle received commands.

        Args:
            sock (multiprocessing.connection.Client): Client socket that received the command.
            cmd (Command): Command object that was received.
        """
        # assert isinstance(cmd, Command)
        if isinstance(cmd, ListJobs):
            cmd.jobs = {k: v.job_func.script for k, v in JOBS.items()}
            listener.send_socket(sock, cmd)
            return

        cmd_type = str(cmd.cmd_type).lower()
        if cmd_type == 'quit':
            listener.stop()
        elif cmd_type == 'remove':
            stop_script(cmd.name)
        else:
            start_script(cmd.name, cmd.script, cmd.interval, cmd.time_unit)

    listener.msg_handler = msg_handler

    th = threading.Thread(target=listener.listen)
    th.daemon = True
    th.start()

    print('Scheduler running ...')
    while listener.is_running():
        schedule.run_pending()
        time.sleep(1)
