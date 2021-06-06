import sys
import traceback
# import PySide2
import urllib3

from PySide2.QtWidgets import QApplication
# from PyQt5.QtWidgets import QApplication
# hiddenimports = collect_submodules('scipy')

from components.dialog import Dialog

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def excepthook(etype, value, tb):
    traceback.print_exception(etype, value, tb)
    sys.exit()


if __name__ == '__main__':
    # setting exception hook for pycharm
    sys.excepthook = excepthook

    app = QApplication(sys.argv)
    dlg = Dialog()
    dlg.show()
    app.exec_()
