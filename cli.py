import logging
import sys
import time
import traceback
from pathlib import Path

import click

from components.asyncio_download_worker import DownloadVideoWorker, DownloadHandler
from components.config import init_logging
from components.csv_reader import get_camera_stream, get_camera_full_name


# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def excepthook(etype, value, tb):
    traceback.print_exception(etype, value, tb)

@click.command()
@click.option('--start', type=int, default=0)
@click.option('--end', type=int, default=9999999)
@click.option('--output', type=click.Path(file_okay=False, writable=True), default='output')
def record(start, end, output):
    # setting exception hook for pycharm
    sys.excepthook = excepthook

    streams = []
    init_logging()
    DownloadHandler.init()
    with open('cameras.csv') as f:
        for i, c in enumerate(f):
            c = c.strip()
            if i < start:
                continue
            if i > end:
                break
            streams.append(DownloadVideoWorker(Path(output) / get_camera_full_name(c), i, get_camera_stream(c)))
            streams[-1].start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.warning('Stopping...')
        for stream in streams:
            stream.stop = True
        while not all(stream.stopped for stream in streams):
            time.sleep(1)
    finally:
        DownloadHandler.deinit()


if __name__ == '__main__':
    record()