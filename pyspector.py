import sys
from PyQt5.QtWidgets import QApplication
from MainWindow import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    config = {
        'moduleNames': [
            'builtins',
            'collections.abc',
            'matplotlib',
            'matplotlib.pyplot',
            'numpy',
            'sys'
        ]
     }
    mainWindow = MainWindow(config)
    sys.exit(app.exec())
