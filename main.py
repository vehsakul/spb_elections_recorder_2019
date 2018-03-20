import asyncio
import sys
from PyQt5.QtWidgets import QApplication

from components.dialog import Dialog

app = QApplication(sys.argv)
from loop import loop
asyncio.set_event_loop(loop)

dlg = Dialog()
dlg.show()

with loop:
    loop.run_forever()
