import itertools
import os
import time
from urllib.parse import parse_qs

from PyQt5.QtCore import QThread, pyqtSignal
import requests
import m3u8


class DownloadFileWorker(QThread):
    finished = pyqtSignal(float)

    def __init__(self, url, path, length):
        super(DownloadFileWorker, self).__init__()

        self.url = url
        self.path = path
        self.length = length

    def run(self):
        with open(self.path, 'wb') as f:
            f.write(requests.get(self.url).content)
        self.finished.emit(self.length)


class DownloadVideoWorker(QThread):
    started = pyqtSignal(str)
    downloaded_chunk = pyqtSignal(float)
    stopped = pyqtSignal()

    def __init__(self, video_id):
        super(DownloadVideoWorker, self).__init__()
        self.video_id = video_id
        self.directory = self.hls_url = self.last_file = ''
        self.part_num = self.media_sequence = 0
        self.meta = self.hls = None
        self.stop = False
        self.tasks = []

    def _get_available_dir(self):
        for i in itertools.count():
            path = os.path.join('output', f'{self.video_id}.{i}')
            if not os.path.exists(path):
                return path

    def _load_meta(self):
        r = requests.get('https://www.youtube.com/get_video_info', {'video_id': self.video_id})
        data = parse_qs(r.text)

        self.meta = m3u8.load(data['hlsvp'][0])
        self.hls_url = self.meta.playlists[-1].uri
        self.hls = m3u8.load(self.hls_url)

        self.started.emit(data['title'][0])

    def _dl_chunk(self, url, path, length):
        dl_worker = DownloadFileWorker(url, path, length)
        dl_worker.finished.connect(self.downloaded_chunk)
        self.tasks.append(dl_worker)
        dl_worker.start()

    def run(self):
        self.directory = self._get_available_dir()
        os.mkdir(self.directory)

        self._load_meta()

        hls = m3u8.load(self.hls_url)
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
                self._dl_chunk(file, file_name, hls.segments[idx+i].duration)
                self.part_num += 1
            time.sleep(hls.target_duration)
            hls = m3u8.load(self.hls_url)
