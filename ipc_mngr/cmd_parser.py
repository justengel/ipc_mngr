from .com_mngr import IPCError

__all__ = ['IPCError', 'CommandParser', 'CommandInterface']


class CommandParser(object):
    CMD_TYPES = {}  # ID: Command, NAME: Command,
    REQUIRED_ATTRS = ['ID', 'NAME', 'decode', '__bytes__']

    @classmethod
    def add_cmd_type(cls, cmd):
        """Add a command type to the command lookup table"""
        if not any((hasattr(cmd, attr) for attr in cls.REQUIRED_ATTRS)):
            raise IPCError('Invalid Command class given! Required attributes {}'.format(cls.REQUIRED_ATTRS))

        cls.CMD_TYPES[cmd.ID] = cmd
        cls.CMD_TYPES[cmd.NAME] = cmd
        return cmd

    @classmethod
    def remove_cmd_type(cls, cmd=None, cmd_name=None, cmd_id=None):
        """Remove the given command.

        Args:
            cmd (object/Command)[None]: Command class to remove
            cmd_name (str)[None]: Command name to remove.
            cmd_id (int)[None]: Command id to remove.

        Returns:
            cmd (object/Command)[None]: Command class that was removed
        """
        try:
            cmd = cls.CMD_TYPES.pop(cmd)
        except (KeyError, ValueError, TypeError):
            pass
        try:
            if cmd_name is None:
                cmd_name = cmd.NAME
            obj = cls.CMD_TYPES.pop(cmd_name)
            if cmd is None:
                cmd = obj
        except (KeyError, ValueError, TypeError, AttributeError):
            pass
        try:
            if cmd_id is None:
                cmd_id = cmd.ID
            obj = cls.CMD_TYPES.pop(cmd_id)
            if cmd is None:
                cmd = obj
        except (KeyError, ValueError, TypeError, AttributeError):
            pass
        return cmd

    @classmethod
    def get_cmd_type(cls, cmd_name_id):
        """Return the command from the command name or id."""
        try:
            return cls.CMD_TYPES[cmd_name_id]
        except KeyError:
            pass
        raise IPCError("Command '{}' not found!".format(cmd_name_id))

    @classmethod
    def encode(cls, data):
        """Encode the given command to bytes"""
        return data  # Normal send/recv is pickling objects

    @classmethod
    def decode(cls, data):
        """Decode a command from the given bytes."""
        return data  # Normal send/recv is pickling objects


class CommandInterface(object):
    """Commands can be any object but they must be known to the listener process."""
