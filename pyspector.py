import abc
import builtins
import collections.abc
# import docutils
# import docutils.parsers
# import docutils.parsers.rst
# import docutils.parsers.rst.directives
# import docutils.parsers.rst.directives.admonitions
# import docutils.parsers.rst.directives.body
# import docutils.parsers.rst.roles
# import docutils.writers
# import docutils.writers.html4css1
import matplotlib
import matplotlib.pyplot
import numpy
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
        # docutils,
        # docutils.parsers,
        # docutils.parsers.rst,
        # docutils.parsers.rst.directives,
        # docutils.parsers.rst.directives.admonitions,
        # docutils.parsers.rst.directives.body,
        # docutils.parsers.rst.roles,
        # docutils.writers,
        # docutils.writers.html4css1,
        matplotlib,
        matplotlib.pyplot,
        numpy,
        sampleCode,
        sys,
    ] }
    mainWindow = MainWindow(config)
    sys.exit(app.exec())
