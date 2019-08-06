"""
Server to stream out audio data to another process to test speed.

Requires:
  * numpy
  * pyaudio
"""
import argparse
import time

import ipc_mngr
import threading

import numpy as np
import pyaudio


def calculate_samples_per_buffer(sample_rate, update_rate=30):
    """Calculate and return the optimal samples per buffer (30 Hz of the sample rate).

    Args:
        sample_rate (float/int): Sample rate of the data
        update_rate (int): How fast to update in Hz. (30 is 30 times per second).

    Returns:
        samples_per_buffer (int): Power of 2 for the number of samples closest to the update rate.
    """
    size = max(sample_rate // update_rate, 32)

    # Force nearest power of two
    size = pow(2, round(np.log2(size)))
    return int(size)


if __name__ == '__main__':
    P = argparse.ArgumentParser('Stream audio data from this computer.')
    P.add_argument('--rate', type=int, default=44100, help='Sample rate to read in the audio data.')
    P.add_argument('--channels', type=int, default=2, help='Number of audio channels to read in.')
    ARGS = P.parse_args()

    FORMAT = pyaudio.paFloat32
    CHANNELS = ARGS.channels
    RATE = ARGS.rate
    CHUNK = calculate_samples_per_buffer(RATE)  # 1024
    RUNNING = threading.Event()
    RUNNING.set()

    print('Running stream . . .')
    with ipc_mngr.Streamer(('127.0.0.1', 8222), authkey='12345', alive=RUNNING) as streamer:
        def msg_handler(sock, cmd):
            """Message handler to do something when data is read in."""
            if cmd == 'stop':
                streamer.broadcast('stop')
                RUNNING.clear()

        streamer.msg_handler = msg_handler

        # Callback based PyAudio
        # def stream_audio(in_data, frame_count, time_info, status):
        #     data = np.frombuffer(in_data, dtype=np.dtype('|f4')).reshape((-1, CHANNELS))
        #     streamer.stream(data)
        #     return (in_data, pyaudio.paContinue)

        # Create the audio stream
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)  # stream_callback=stream_audio)

        # Block forever listening for clients to stream data to
        while RUNNING.is_set():
            data = np.frombuffer(stream.read(CHUNK), dtype=np.dtype('|f4')).reshape((-1, CHANNELS))
            streamer.stream(data)

    # Close the audio stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    print('Stream closed!')
