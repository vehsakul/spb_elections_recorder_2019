import json
import re

from PySide2.QtWidgets import QDialog, QVBoxLayout

from .Ui_dialog import Ui_Dialog
from .video import Video


class Dialog(Ui_Dialog, QDialog):
    def __init__(self, parent=None):
        super(Dialog, self).__init__(parent)
        self.setupUi(self)

        self.videos = []

        self.edtURL.textChanged.connect(self.edt_changed)
        self.btnAdd.clicked.connect(self.add_video)
        with open('cameras.csv') as f:
            self.cameras = [line.rstrip() for line in f]
        self.edt_changed()

    def edt_changed(self):
        try:
            self.cameras[int(self.edtURL.text())]
        except IndexError:
            self.btnAdd.setEnabled(False)
            self.lblCameraInfo.setText('index out of range')
        except ValueError as e:
            self.btnAdd.setEnabled(False)
            self.lblCameraInfo.setText('enter camera index')
        else:
            self.btnAdd.setEnabled(True)
            self.lblCameraInfo.setText('')


    def add_video(self):
            index = int(self.edtURL.text())
            video = Video(self.cameras[index], index, self)
            lyt = self.lstVideos.layout()  # type: QVBoxLayout
            lyt.addWidget(video)
            video.start()
        # for i, stream in enumerate(cameras[self.edtURL.text()]['streams'], 1):
        #     video = Video(cameras[self.edtURL.text()], i, stream, self)
        #     lyt = self.lstVideos.layout()  # type: QVBoxLayout
        #     lyt.addWidget(video)
        #     video.start()
