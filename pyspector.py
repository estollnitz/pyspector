import builtins
import matplotlib
import matplotlib.pyplot
import numpy
import sampleCode
import sys
from PyQt5.QtWidgets import QApplication
from MainWindow import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    config = { 'modules': [
        sys.modules[__name__],
        builtins,
        matplotlib,
        matplotlib.pyplot,
        numpy,
        sampleCode,
        sys,
    ] }
    mainWindow = MainWindow(config)
    sys.exit(app.exec())
