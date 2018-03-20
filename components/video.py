import uuid

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QWidget

from components.download_worker import DownloadVideoWorker
from .Ui_video import Ui_Video


class Video(Ui_Video, QWidget):
    def __init__(self, video_id, dialog, parent=None):
        super(Video, self).__init__(parent)
        self.setupUi(self)
        self.setObjectName(str(uuid.uuid4()))
        self.video_id = video_id
        self.dialog = dialog
        self.btnRemove.setVisible(False)
        self.length = 0.
        self.directory = ''
        self.part_num = 0
        self.task = None

        self.btnStop.clicked.connect(self.stop)
        self.btnRemove.clicked.connect(self.remove)

    def update_length(self, duration):
        self.length += duration
        hours = int(self.length // (60 * 60))
        minutes = int(self.length % (60 * 60) // 60)
        seconds = int(self.length % 60)
        self.lblLength.setText(f'{hours:02d}:{minutes:02d}:{seconds:02d}')

    def start(self):
        self.task = DownloadVideoWorker(self.video_id)
        self.task.started.connect(self.started)
        self.task.downloaded_chunk.connect(self.update_length)
        self.task.stopped.connect(self.stopped)
        self.task.start()

    def started(self, title):
        self.lblState.setStyleSheet('color: #090')
        self.lblState.setText('Downloading...')
        self.btnStop.setEnabled(True)

        fm = QFontMetrics(self.lblTitle.font())
        width = self.lblTitle.width()
        self.lblTitle.setText(fm.elidedText(title, Qt.ElideRight, width))

    def stop(self):
        self.lblState.setStyleSheet('')
        self.lblState.setText('Stopping...')
        self.btnStop.setEnabled(False)
        self.task.stop = True

    def stopped(self):
        self.lblState.setText('Stopped')
        self.btnStop.setVisible(False)
        self.btnRemove.setVisible(True)

    def remove(self):
        self.dialog.lstVideos.layout().removeWidget(self)
        self.deleteLater()
