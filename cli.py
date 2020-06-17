#!/usr/bin/env python3
import itertools
import logging
import os
import tempfile
import time
from threading import Thread

from copy import copy
import random
import click
import requests
import m3u8
import urllib3

from urllib.request import urlopen, Request
from urllib.parse import urljoin
from cameras import cameras


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s")

user_agents = [
    'Mozilla/5.0 (Windows NT 6.0; WOW64) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.45 Safari/535.19',
]

default_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'User-Agent': random.choice(user_agents)
}

class VideoStream:
    def __init__(self, uik_obj, index, stream_url, output):
        self.uik_obj = uik_obj
        self.index = index
        self.directory = self.last_file = ''
        self.hls_url = stream_url
        self.output = output
        self.part_num = self.media_sequence = 0
        self.meta = self.hls = None
        self.stop = self.stopped = False
        self.tasks = []
        self.logger = logging.getLogger(f'UIK #{uik_obj["uik"]} / cam {index}')
        
        self.headers = copy(default_headers)
        #self.headers['Referer'] = referer()  # TODO

    def load_hls(self):
        try:
            with tempfile.TemporaryDirectory() as dir:
                file_path = os.path.join(dir, 'playlist.m3u8')
                with open(file_path, 'wb') as f:
                    f.write(requests.get(self.hls_url, verify=False).content)
                return m3u8.load(file_path)
        except:
            return None

    def _get_available_dir(self):
        for i in itertools.count():
            path = os.path.join(self.output, f'UIK #{self.uik_obj["uik"]} ({i})', f'cam {self.index}')
            if not os.path.exists(path):
                return path

    def _dl_chunk(self, url, path, length):
        try:
            with open(path, 'wb') as f:
                for i in range(10):
                    try:
                        request = urlopen(Request(url, headers=self.headers), timeout=60)
                        f.write(request.read())
                        break
                    except requests.ConnectionError:
                        self.logger.warning('Cannot download chunk, retrying...')
                        time.sleep(1)
        except IOError:
            self.logger.error('Disk write error')
            raise
        return length

    def run(self):
        self.directory = self._get_available_dir()
        try:
            os.makedirs(self.directory)
        except OSError:
            self.logger.error('Cannot create directories')
            return

        self.logger.info('Started')

        hls = self.load_hls()
        if not hls:
            self.logger.error('Initial playlist download error')
            return
        self.media_sequence = hls.media_sequence
        while True:
            if not hls.files:
                continue
            if self.stop:
                self.stopped = True
                logging.warning('Stopped')
                return
            try:
                idx = hls.files.index(self.last_file) + 1
            except ValueError:
                if self.media_sequence != hls.media_sequence:
                    idx = 0
                else:
                    idx = -1
            self.last_file = hls.files[-1]
            for i, file in enumerate(hls.files[idx:]):
                file_name = os.path.join(self.directory, f'part.{self.part_num:06d}.ts')
                self._dl_chunk(self.hls_url + file, file_name, hls.segments[idx+i].duration)
                self.logger.info(f'Chunk {self.part_num} downloaded')
                self.part_num += 1
            while True:
                hls = self.load_hls()
                if hls:
                    break
            time.sleep(1)


@click.command()
@click.option('--start', type=int)
@click.option('--end', type=int)
@click.option('--output', type=click.Path(file_okay=False, writable=True), default='output')
def record(start, end, output):
    threads = []
    streams = []
    for uik in range(start, end+1):
        try:
            uik_obj = cameras[str(uik)]
            for i, stream_url in enumerate(uik_obj['streams'], 1):
                streams.append(VideoStream(uik_obj, i, stream_url, output))
                threads.append(Thread(target=streams[-1].run))
                threads[-1].start()
        except KeyError:
            logging.warning(f'UIK #{uik} was not found')
            continue
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logging.warning('Stopping...')
        for stream in streams:
            stream.stop = True
        while not all(stream.stopped for stream in streams):
            time.sleep(1)


if __name__ == '__main__':
    record()
