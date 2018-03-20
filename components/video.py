import asyncio
import itertools
import os
import uuid
from urllib.parse import parse_qs

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QWidget
import m3u8
import requests

from .Ui_video import Ui_Video


class Video(Ui_Video, QWidget):
    def __init__(self, video_id, dialog, parent=None):
        from loop import loop
        self.loop = loop

        super(Video, self).__init__(parent)
        self.setupUi(self)
        self.setObjectName(str(uuid.uuid4()))
        self.video_id = video_id
        self.dialog = dialog
        self.btnRemove.setVisible(False)
        self.length = 0.
        self.stopped = False
        self.directory = ''
        self.part_num = 0

        self.btnStop.clicked.connect(self.stop)
        self.btnRemove.clicked.connect(self.remove)

    def _set_title(self, title):
        fm = QFontMetrics(self.lblTitle.font())
        width = self.lblTitle.width()
        self.lblTitle.setText(fm.elidedText(title, Qt.ElideRight, width))

    def _get_available_name(self, base):
        for i in itertools.count():
            path = f'{base}.{i}'
            if not os.path.exists(path):
                return path, i

    def _get_file_name(self, base, directory, part):
        return os.path.join('output', f'{base}.part{part}.ts')  # , self.video_id

    def update_length(self):
        hours = int(self.length // (60 * 60))
        minutes = int(self.length % (60 * 60) // 60)
        seconds = int(self.length % 60)
        self.lblLength.setText(f'{hours:02d}:{minutes:02d}:{seconds:02d}')

    async def dl_file(self, url, path, length):
        print(f'downloading {url}')
        with open(path, 'wb') as f:
            f.write(requests.get(url).content)
        self.length += length
        self.update_length()

        self.lblState.setText('Downloading...')
        self.lblState.setStyleSheet('color: #090')
        print(f'downloaded {url}')

    async def work(self):
        r = requests.get('https://www.youtube.com/get_video_info', {'video_id': self.video_id})
        data = parse_qs(r.text)
        self._set_title(data['title'][0])

        meta_stream_url = data['hlsvp'][0]
        meta = m3u8.load(meta_stream_url)
        hls_stream_url = meta.playlists[-1].uri

        self.lblState.setText('Downloading...')
        self.lblState.setStyleSheet('color: #090')
        self.btnStop.setEnabled(True)

        self.directory, _ = self._get_available_name(os.path.join('output', self.video_id))
        os.mkdir(self.directory)
        last_file = None
        hls = m3u8.load(hls_stream_url)
        media_sequence = hls.media_sequence
        _, self.part_num = self._get_available_name(os.path.join(self.directory, 'part'))
        while True:
            if self.stopped:
                self.lblState.setText('Stopped')
                self.btnStop.setVisible(False)
                self.btnRemove.setVisible(True)
                break
            try:
                idx = hls.files.index(last_file) + 1
            except ValueError:
                if media_sequence != hls.media_sequence:
                    idx = 0
                else:
                    idx = -1
            last_file = hls.files[-1]
            for i, file in enumerate(hls.files[idx:]):
                file_name = os.path.join(self.directory, f'part.{self.part_num:06d}.ts')
                self.loop.create_task(self.dl_file(file, file_name, hls.segments[idx+i].duration))
                self.part_num += 1
            await asyncio.sleep(hls.target_duration)
            hls = m3u8.load(hls_stream_url)

    def start(self):
        self.loop.create_task(self.work())

    def stop(self):
        self.lblState.setStyleSheet('')
        self.lblState.setText('Stopping...')
        self.stopped = True

    def remove(self):
        self.dialog.lstVideos.layout().removeWidget(self)
        self.deleteLater()
