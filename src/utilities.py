# External imports:
import os
import platform
import subprocess
from typing import Callable
from PyQt5.QtCore import QAbstractProxyModel, QModelIndex
from PyQt5.QtGui import QStandardItem

def openFile(filePath):
    '''Opens a file using the system's default application.'''
    if platform.system() == 'Darwin':
        subprocess.call(('open', filePath))
    elif platform.system() == 'Windows':
        os.startfile(filePath)
    else:
        subprocess.call(('xdg-open', filePath))

def getItemFromIndex(model: QAbstractProxyModel, index: QModelIndex) -> QStandardItem:
    '''Returns the item corresponding to the given index.'''
    while isinstance(model, QAbstractProxyModel):
        index = model.mapToSource(index)
        model = model.sourceModel()
    return model.itemFromIndex(index)

ItemPredicate = Callable[[QStandardItem], bool]

def findIndexInModel(model: QAbstractProxyModel, predicate: ItemPredicate,
    parentIndex: QModelIndex = QModelIndex()) -> QModelIndex:
    '''Returns the index of the first item in a hierarchical model that satisfies the given predicate.'''
    rowCount = model.rowCount(parentIndex)
    for row in range(rowCount):
        index = model.index(row, 0, parentIndex)

        # Check this item.
        item = getItemFromIndex(model, index)
        if predicate(item):
            return index

        # Recurse into children.
        childIndex = findIndexInModel(model, predicate, index)
        if childIndex.isValid():
            return childIndex

    return QModelIndex()
