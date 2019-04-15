# External imports:
from PyQt5.QtCore import pyqtSignal, Qt, QObject, QTimer
from PyQt5.QtGui import QKeyEvent, QKeySequence
from PyQt5.QtWidgets import QLineEdit

class SearchEdit(QLineEdit):
    '''Customizes keyboard handling of QLineEdit and offers a delayedTextChanged event.'''

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._timer = QTimer()
        self._timer.setInterval(500)
        self._timer.setSingleShot(True)

        self.setClearButtonEnabled(True)
        shortcutText = QKeySequence(QKeySequence.Find).toString(QKeySequence.NativeText)
        self.setPlaceholderText(f'Search ({shortcutText})')
        self.textChanged.connect(self._restartTimer)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        '''Handles key press events, using the escape key to clear.'''
        if event.key() == Qt.Key_Escape:
            self.clear()
        else:
            super().keyPressEvent(event)

    @property
    def delayedTextChanged(self) -> pyqtSignal:
        return self._timer.timeout

    def _restartTimer(self) -> None:
        self._timer.stop()
        self._timer.start()
