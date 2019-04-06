# External imports:
import sys
from os import makedirs
from os.path import expanduser
from PyQt5.QtWidgets import QApplication

# Local imports:
from Config import Config
from MainWindow import MainWindow

if __name__ == '__main__':
    # Make sure the configuration directory exists.
    homeDir = expanduser('~')
    configDir = f'{homeDir}/.config/pyspector'
    makedirs(configDir, exist_ok = True)

    # Create a configuration object by reading the configuration file, if it exists.
    configPath = f'{configDir}/config.json'
    config = Config(configPath)

    # Create the appliction and main window.
    app = QApplication(sys.argv)
    mainWindow = MainWindow(config)

    # Exit after running the application main loop.
    sys.exit(app.exec())
