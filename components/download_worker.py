import itertools
import os
import tempfile
import time

from PySide2.QtCore import QThread, Signal
# from PyQt5.QtCore import QThread
import requests
import m3u8
import ssl

ssl._create_default_https_context = ssl._create_unverified_context


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
                        time.sleep(1)
            self.finished.emit(self.length, self.index)
        except IOError:
            self.errored.emit('Ошибка записи\n(проверьте свободное место на диске)')
        self.quit()
        self.deleteLater()


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
            path = os.path.join('output', f'{self.uik_obj["uik"]} ({i})')
            if not os.path.exists(path):
                return path

    def _dl_chunk(self, url, path, length, index):
        # print(url)
        url = url.replace('mono.m3u8', '')
        print (url)
        # print (url)

        dl_worker = DownloadFileWorker(url, path, length, index)
        dl_worker.finished.connect(self.on_downloaded_chunk)
        dl_worker.errored.connect(self.on_error)
        self.tasks[index] = dl_worker
        dl_worker.start()

    def load_hls(self):
        # print (self.hls_url)
        # ff = open('d:\\tmp\\#cam\\test.txt', 'wb')
        try:
        #     with tempfile.TemporaryDirectory() as dir:
        #         file_path = os.path.join(dir, 'playlist.m3u8')
        #         with open(file_path, 'wb') as f:
        #             # f.write(requests.get(self.hls_url, verify=False).content)
        #             a = requests.get(self.hls_url, verify=False).content
        #             # f.write(a.replace('2020','https://flu01.pride-net.ru/cam_60let59/tracks-v1/2020'))
        #             # print (a)
        #             f.write(a)
        #             # f.write(requests.get(self.hls_url, verify=False).content)
        #             # ff.write(requests.get(self.hls_url, verify=False).content)
        #             # ff.write(a)
        #         # return m3u8.load(file_path)
        #
        #         m3u8_obj = m3u8.load('https://flu01.pride-net.ru/cam_60let59/tracks-v1/mono.m3u8')
        #
        #         print (m3u8_obj.segments)
        #         print (m3u8_obj.target_duration)
        #
        #         # return m3u8.load('https://flu01.pride-net.ru/cam_60let59/tracks-v1/mono.m3u8')
                print (requests.get(self.hls_url, verify=False).text)

                return m3u8.load(self.hls_url)

        except:
            return None

    def on_error(self, msg):
        self.error = True
        self.errored.emit(msg)

    def on_downloaded_chunk(self, length, index):
        self.downloaded_chunk.emit(length)
        del self.tasks[index]

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
            try:
                hls = self.load_hls()
            except:
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
                time.sleep(1)
        self.quit()
        self.deleteLater()
