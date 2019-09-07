import itertools
import os
import tempfile
import time

from PySide2.QtCore import QThread, Signal
import requests
import m3u8


class DownloadFileWorker(QThread):
    finished = Signal(float, int)
    errored = Signal(str)

    def __init__(self, url, path, length, index):
        super(DownloadFileWorker, self).__init__()

        self.url = url
        self.path = path
        self.length = length
        self.index = index

    def run(self):
        try:
            with open(self.path, 'wb') as f:
                for i in range(10):
                    try:
                        f.write(requests.get(self.url, verify=False).content)
                        break
                    except requests.ConnectionError:
                        pass
        except IOError:
            self.errored.emit('Ошибка записи\n(проверьте свободное место на диске)')
            return
        self.finished.emit(self.length, self.index)
        self.quit()


class DownloadVideoWorker(QThread):
    started = Signal()
    downloaded_chunk = Signal(float)
    stopped = Signal()
    errored = Signal(str)

    def __init__(self, uik_obj, index, stream_url):
        super(DownloadVideoWorker, self).__init__()
        self.uik_obj = uik_obj
        self.index = index
        self.directory = self.last_file = ''
        self.hls_url = stream_url
        self.part_num = self.media_sequence = 0
        self.meta = self.hls = None
        self.stop = self.error = False
        self.tasks = {}

    def _get_available_dir(self):
        for i in itertools.count():
            path = os.path.join('output', f'УИК #{self.uik_obj["uik"]} ({i})', f'Камера {self.index}')
            if not os.path.exists(path):
                return path

    def _dl_chunk(self, url, path, length, index):
        dl_worker = DownloadFileWorker(url, path, length, index)
        dl_worker.finished.connect(self.on_downloaded_chunk)
        dl_worker.errored.connect(self.on_error)
        self.tasks[index] = dl_worker
        dl_worker.start()

    def load_hls(self):
        try:
            with tempfile.TemporaryDirectory() as dir:
                file_path = os.path.join(dir, 'playlist.m3u8')
                with open(file_path, 'wb') as f:
                    f.write(requests.get(self.hls_url, verify=False).content)
                return m3u8.load(file_path)
        except:
            return None

    def on_error(self, msg):
        self.error = True
        self.errored.emit(msg)

    def on_downloaded_chunk(self, length, index):
        self.downloaded_chunk.emit(length)
        # del self.tasks[index]

    def run(self):
        self.directory = self._get_available_dir()

        try:
            os.makedirs(self.directory)
        except OSError:
            self.errored.emit('Ошибка записи\n(проверьте свободное место на диске)')
            return

        self.started.emit()

        hls = self.load_hls()
        if not hls:
            self.error = True
            self.errored.emit('Ошибка загрузки плейлиста')
            return
        self.media_sequence = hls.media_sequence
        while True:
            if self.stop:
                self.stopped.emit()
                break
            if self.error:
                break
            if not hls.files:
                continue
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
                self._dl_chunk(self.hls_url + file, file_name, hls.segments[idx+i].duration, self.part_num)
                self.part_num += 1
            time.sleep(hls.target_duration)
            while True:
                hls = self.load_hls()
                if hls:
                    break
        self.quit()
