# External imports:
from PyQt5.QtCore import (Qt, QModelIndex)
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QTreeView

class TreeView(QTreeView):
    '''Slightly customizes keyboard handling of QTreeView.'''

    def keyPressEvent(self, event: QKeyEvent) -> None:
        '''Handles key press events, using the left arrow key to collapse items.'''
        currentIndex: QModelIndex = self.currentIndex()
        if event.key() == Qt.Key_Left and currentIndex.isValid():
            if self.isExpanded(currentIndex):
                self.collapse(currentIndex)
            elif currentIndex.parent().isValid():
                self.setCurrentIndex(currentIndex.parent())
        else:
            super().keyPressEvent(event)
