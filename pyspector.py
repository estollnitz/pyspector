import builtins
import matplotlib
import matplotlib.pyplot
import numpy
import sys
from PyQt5.QtWidgets import QApplication
from MainWindow import MainWindow
from Model import Model

if __name__ == '__main__':
    app = QApplication(sys.argv)
    config = { 'modules': [sys.modules[__name__], builtins, sys, numpy, matplotlib, matplotlib.pyplot] }
    # config = { 'modules': [Model] }
    mainWindow = MainWindow(config)
    sys.exit(app.exec())
