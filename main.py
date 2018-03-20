import sys
import traceback

from PyQt5.QtWidgets import QApplication

from components.dialog import Dialog


def excepthook(etype, value, tb):
    traceback.print_exception(etype, value, tb)
    sys.exit()


if __name__ == '__main__':
    # setting exception hook for pycharm
    sys.excepthook = excepthook

    app = QApplication(sys.argv)
    dlg = Dialog()
    dlg.show()
    app.exec()
