import re

from PyQt5.QtWidgets import QDialog, QVBoxLayout

from .Ui_dialog import Ui_Dialog
from .video import Video


class Dialog(Ui_Dialog, QDialog):
    def __init__(self, parent=None):
        super(Dialog, self).__init__(parent)
        self.setupUi(self)

        self.videos = []

        self.edtURL.textChanged.connect(self.edt_changed)
        self.btnAdd.clicked.connect(self.add_video)

    def get_video_id(self):
        video_id = None
        link = re.sub(r'[<>]', '', self.edtURL.text())
        parts = re.split(r'(vi/|v=|/v/|youtu\.be/|/embed/)', link)
        if len(parts) > 2:
            video_id = re.split(r'[^0-9a-zA-Z_-]', parts[2])
            video_id = video_id[0]
        elif not re.search(r'[^0-9a-zA-Z_-]', link):
            video_id = link
        return video_id

    def edt_changed(self):
        self.btnAdd.setEnabled(bool(self.get_video_id()))

    def add_video(self):
        video = Video(self.get_video_id(), self)
        lyt = self.lstVideos.layout()  # type: QVBoxLayout
        lyt.addWidget(video)
        video.start()
