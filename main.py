import sys
from PyQt5.QtWidgets import QApplication

from components.dialog import Dialog

app = QApplication(sys.argv)

dlg = Dialog()
dlg.show()

app.exec()
