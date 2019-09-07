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
        with open('cameras.json') as f:
            self.cameras = json.load(f)

        self.edtURL.textChanged.connect(self.edt_changed)
        self.btnAdd.clicked.connect(self.add_video)
        self.edt_changed()

    def edt_changed(self):
        try:
            uik = self.cameras[self.edtURL.text()]
            self.btnAdd.setEnabled(True)
            self.lblCameraInfo.setText('Район: {}\nУчреждение: {}\nАдрес: {}'.format(
                uik['city_area_name'], uik['address_title'], uik['address']))
        except KeyError:
            self.btnAdd.setEnabled(False)
            self.lblCameraInfo.setText('Район: -\nУчреждение: -\nАдрес: -')

    def add_video(self):
        for i, stream in enumerate(self.cameras[self.edtURL.text()]['streams'], 1):
            video = Video(self.cameras[self.edtURL.text()], i, stream, self)
            lyt = self.lstVideos.layout()  # type: QVBoxLayout
            lyt.addWidget(video)
            video.start()
