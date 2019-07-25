Interprocess Communication (IPC) Manager
========================================

Interprocess Communication (IPC) Manager to help create a Command structure for sending and receiving messages between processes.


Simple Listener/Client
----------------------
.. code-block:: python

    # main.py
    import ipc_mngr

    def msg_handler(sock, cmd):
        """Handle received commands.

        Args:
            sock (multiprocessing.connection.Client): Client socket that received the command.
            cmd (object): Command object that was received.
        """
        print('Received Command:', cmd)

    listener = ipc_mngr.Listener(('127.0.0.1', 8111), authkey='12345')
    listener.msg_handler = msg_handler
    print("listening ...")
    listener.listen()  # Listen forever


.. code-block:: python

    # send_cmd.py
    import ipc_mngr

    with ipc_mngr.Client(('127.0.0.1', 8111), authkey='12345') as client:
        # Send the command
        client.send("Hello World!")


Schedule Example
----------------
See tests/schedule_run directory for how to use this as a permanent job scheduler.
