import abc
import builtins
import collections.abc
import matplotlib
import matplotlib.pyplot
import numpy
import docutils
import docutils.writers
import docutils.writers.html4css1
import sampleCode
import sys
from PyQt5.QtWidgets import QApplication
from MainWindow import MainWindow
from Model import Model

if __name__ == '__main__':
    app = QApplication(sys.argv)
    config = { 'modules': [
        sys.modules[__name__],
        abc,
        builtins,
        collections.abc,
        matplotlib,
        matplotlib.pyplot,
        numpy,
        docutils,
        docutils.writers,
        docutils.writers.html4css1,
        sampleCode,
        sys,
    ] }
    mainWindow = MainWindow(config)
    sys.exit(app.exec())
