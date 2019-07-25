# Shared Command objects


class Command(object):
    """Command to add or remove a schedule item.

    Args:
        cmd_type (str): "remove" or "add" to add or remove a schedule script to run
        name (str): Unique Name identifier
        script (str): Command line script with arguments to run.
        interval (int/float): Time interval to do the task.
        time_unit (str): Schedule time unit to do the action at.
            (EX: time_unit=="hour" -> schedule.every(interval).hour.do(job))
    """
    def __init__(self, cmd_type, name, script=None, interval=None, time_unit=None):
        self.cmd_type = cmd_type
        self.name = name
        self.script = script
        self.interval = interval
        self.time_unit = time_unit


class ListJobs(object):
    def __init__(self, jobs=None):
        self.jobs = jobs or []
