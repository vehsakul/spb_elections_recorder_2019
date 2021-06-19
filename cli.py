import asyncio
import logging
import sys
import time
import traceback
import os
from pathlib import Path

import click

from components.asyncio_download_worker import DownloadVideoWorker, DownloadHandler
from components.config import init_logging
from components.csv_reader import get_camera_stream, get_camera_full_name

# See: https://bugs.python.org/issue29288
u''.encode('idna')

# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def excepthook(etype, value, tb):
    traceback.print_exception(etype, value, tb)

@click.command()
@click.option('--start', type=int, default=0)
@click.option('--end', type=int, default=9999999)
@click.option('--output', type=click.Path(file_okay=False, writable=True), default='output')
@click.option('--dev/--prod', default=False)
@click.option('--instance', default=0)
@click.option('--num-instances', default=1)
@click.option('--work-dir', required=True)
def record(start, end, output, dev, instance, num_instances, work_dir):
    # setting exception hook for pycharm
    sys.excepthook = excepthook

    os.chdir(work_dir)
    streams = []
    init_logging(dev)
    DownloadHandler.init()
    with open('cameras.csv') as f:
        for i, c in enumerate(f):
            c = c.strip()
            if i < start:
                continue
            if i > end:
                break
            if i % num_instances == instance:
                streams.append(DownloadVideoWorker(Path(output) / get_camera_full_name(c), i, get_camera_stream(c), get_camera_full_name(c)))
                streams[-1].start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.warning('Stopping...')
        while True:
            for task in asyncio.all_tasks(DownloadHandler.loop):
                if not task.cancelled():
                    task.cancel()
            time.sleep(1)
            if len(asyncio.all_tasks(DownloadHandler.loop)) == 0:
                break
    finally:
        DownloadHandler.deinit()


if __name__ == '__main__':
    record()