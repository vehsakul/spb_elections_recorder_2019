import itertools
import os
import tempfile
import time

from PySide2.QtCore import QThread, Signal
import requests
import m3u8


class DownloadFileWorker(QThread):
    finished = Signal(float)

    def __init__(self, url, path, length):
        super(DownloadFileWorker, self).__init__()

        self.url = url
        self.path = path
        self.length = length

    def run(self):
        with open(self.path, 'wb') as f:
            f.write(requests.get(self.url, verify=False).content)
        self.finished.emit(self.length)


class DownloadVideoWorker(QThread):
    started = Signal()
    downloaded_chunk = Signal(float)
    stopped = Signal()

    def __init__(self, uik_obj, index, stream_url):
        super(DownloadVideoWorker, self).__init__()
        self.uik_obj = uik_obj
        self.index = index
        self.directory = self.last_file = ''
        self.hls_url = stream_url
        self.part_num = self.media_sequence = 0
        self.meta = self.hls = None
        self.stop = False
        self.tasks = []

    def _get_available_dir(self):
        for i in itertools.count():
            path = os.path.join('output', f'УИК #{self.uik_obj["uik"]} ({i})', f'Камера {self.index}')
            if not os.path.exists(path):
                return path

    def _dl_chunk(self, url, path, length):
        dl_worker = DownloadFileWorker(url, path, length)
        dl_worker.finished.connect(self.downloaded_chunk)
        self.tasks.append(dl_worker)
        dl_worker.start()

    def load_hls(self):
        with tempfile.TemporaryDirectory() as dir:
            file_path = os.path.join(dir, 'playlist.m3u8')
            with open(file_path, 'wb') as f:
                f.write(requests.get(self.hls_url, verify=False).content)
            return m3u8.load(file_path)

    def run(self):
        self.directory = self._get_available_dir()
        os.makedirs(self.directory)

        self.started.emit()

        hls = self.load_hls()
        self.media_sequence = hls.media_sequence
        while True:
            if self.stop:
                self.stopped.emit()
                break
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
                self.part_num += 1
            time.sleep(hls.target_duration)
            hls = self.load_hls()
