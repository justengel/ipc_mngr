"""
Client to read in audio data and plot it.

Requires:
  * numpy
  * matpltolib
"""
import argparse
import ipc_mngr
import numpy as np

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


if __name__ == '__main__':
    P = argparse.ArgumentParser('Stream audio data from this computer.')
    P.add_argument('--rate', type=int, default=44100, help='Sample rate to read in the audio data.')
    P.add_argument('--seconds', type=float, default=2, help='Display the given number of seconds.')
    ARGS = P.parse_args()

    # Variables
    RATE = ARGS.rate
    SECONDS = ARGS.seconds
    SIZE = int(np.ceil(RATE * SECONDS))

    # Data Storage
    t = -(np.arange(SIZE) / RATE)[::-1]
    buffer = None

    # ===== Plot =====
    fig, ax = plt.subplots()
    ax.set_xlim((-SECONDS, 0))
    ax.set_ylim((-1, 1))
    ax.set_xlabel('Time (sec)')
    ax.set_ylabel('Amplitude')
    # fig.show()
    lines = []

    def update_plot(*args, **kwargs):
        """Update the plot with the latest data"""
        global buffer
        global lines
        if buffer is not None:
            for i in range(buffer.shape[1]):
                try:
                    lines[i].set_data(t[-len(buffer):], buffer[:, i])
                except:
                    ln, = plt.plot(t[-len(buffer):], buffer[:, i])
                    lines.append(ln)
        return lines

    animate = FuncAnimation(fig, update_plot, interval=30, blit=True)

    # ===== Audio Stream =====
    def stream_handler(client, data):
        """Main function to handle the incoming (received) stream data.

        Args:
            client (multiprocessing.connection.Connection): Client socket in case you need to respond to the given data.
            data (object): Data object that was streamed to this client.
        """
        global buffer
        if isinstance(data, str) and data == 'stop':
            plt.close('all')
        elif buffer is None:
            buffer = data
        else:
            buffer = np.append(buffer, data, axis=0)[-SIZE:]


    with ipc_mngr.StreamClient(('127.0.0.1', 8222), authkey='12345') as streamer:
        streamer.stream_handler = stream_handler

        print('Reading stream . . .')
        plt.show()  # Block forever
