import uuid

from PySide2.QtWidgets import QWidget
# from PyQt5.QtWidgets import QWidget

from components.download_worker import DownloadVideoWorker
from .Ui_video import Ui_Video


class Video(Ui_Video, QWidget):
    def __init__(self, uik_obj, index, stream, dialog, parent=None):
        super(Video, self).__init__(parent)
        self.setupUi(self)
        self.setObjectName(str(uuid.uuid4()))
        self.uik_obj = uik_obj
        self.index = index
        self.stream = stream
        self.dialog = dialog
        self.btnRemove.setVisible(False)
        self.length = 0.
        self.directory = ''
        self.part_num = 0
        self.task = None

        # self.lblTitle.setText('УИК №{} [камера {}]'.format(uik_obj['uik'], index))
        self.lblTitle.setText(uik_obj['uik'])

        self.btnStop.clicked.connect(self.stop)
        self.btnRemove.clicked.connect(self.remove)

    def update_length(self, duration):
        self.length += duration
        hours = int(self.length // (60 * 60))
        minutes = int(self.length % (60 * 60) // 60)
        seconds = int(self.length % 60)
        self.lblLength.setText(f'{hours:02d}:{minutes:02d}:{seconds:02d}')

    def start(self):
        self.task = DownloadVideoWorker(self.uik_obj, self.index, self.stream)
        self.task.started.connect(self.started)
        self.task.downloaded_chunk.connect(self.update_length)
        self.task.stopped.connect(self.stopped)
        self.task.errored.connect(self.errored)
        self.task.start()

    def started(self):
        self.lblState.setStyleSheet('color: #090')
        self.lblState.setText('Recording in progress...')
        self.btnStop.setEnabled(True)

    def stop(self):
        self.lblState.setStyleSheet('')
        self.lblState.setText('Recording stops...')
        self.btnStop.setEnabled(False)
        self.task.stop = True

    def stopped(self):
        self.lblState.setText('Stopped')
        self.btnStop.setVisible(False)
        self.btnRemove.setVisible(True)
        self.btnRemove.setEnabled(True)

    def errored(self, msg):
        self.lblState.setStyleSheet('color: #900')
        self.lblState.setText(msg)
        self.btnStop.setVisible(False)

    def remove(self):
        self.dialog.lstVideos.layout().removeWidget(self)
        self.deleteLater()
