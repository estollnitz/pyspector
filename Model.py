import inspect
from PyQt5.QtCore import (QSortFilterProxyModel, QRegularExpression)
from PyQt5.QtGui import (QStandardItemModel, QStandardItem)

class Model():
    def __init__(self):
        self._treeModel = QStandardItemModel()
        self._filteredTreeModel = QSortFilterProxyModel()
        self._filteredTreeModel.setSourceModel(self._treeModel)
        self._filteredTreeModel.setFilterRegularExpression(QRegularExpression('^[^_]'))
        self._filteredTreeModel.setFilterKeyColumn(0)
        self._filteredTreeModel.setRecursiveFilteringEnabled(True)

    @property
    def filteredTreeModel(self) -> QSortFilterProxyModel:
        return self._filteredTreeModel

    @property
    def searchFilter(self) -> str:
        return self._searchFilter

    @searchFilter.setter
    def searchFilter(self, value: str) -> None:
        self._searchFilter = value
        self._filteredTreeModel.setFilterFixedString(value)

    def getItemFromIndex(self, index) -> QStandardItem:
        unfilteredIndex = self._filteredTreeModel.mapToSource(index)
        item = self._treeModel.itemFromIndex(unfilteredIndex)
        return item

    def addModules(self, modules: list) -> None:
        '''Add all the members of the specified modules to the tree.'''
        rootItem = self._treeModel.invisibleRootItem()
        for module in modules:
            item = self._addItem(rootItem, module.__name__, 'module', module)
            self._inspectObject(item, module)

    def _inspectObject(self, parentItem, obj):
        '''Recursively adds object to the hierarchical model.'''
        for (memberName, memberValue) in inspect.getmembers(obj):
            # Skip "magic" members.
            if memberName.startswith('__'):
                continue

            memberType = self._getMemberType(memberValue)

            # Skip modules within modules.
            if memberType == 'module':
                continue

            item = self._addItem(parentItem, memberName, memberType, memberValue)

            # Recurse into classes.
            if memberType == 'class':
                self._inspectObject(item, memberValue)

            # Recurse into property getter, setter, deleter functions.
            # TODO: Generalize this to data descriptors other than just the 'property' class.
            if type(memberValue) == property:
                if memberValue.fget:
                    self._addItem(item, '[get]', 'function', memberValue.fget)
                if memberValue.fset:
                    self._addItem(item, '[set]', 'function', memberValue.fset)
                if memberValue.fdel:
                    self._addItem(item, '[delete]', 'function', memberValue.fdel)

    def _addItem(self, parentItem, name, type, value):
        item = QStandardItem(name)
        item.setData({ 'type': type, 'value': value })
        item.setEditable(False)
        parentItem.appendRow(item)
        return item

    def _getMemberType(self, memberValue):
        checks = [
            (inspect.ismodule, 'module'),
            (inspect.isclass, 'class'),
            (inspect.ismethod, 'method'),
            (inspect.isfunction, 'function'),
            (inspect.isgeneratorfunction, 'generator function'),
            (inspect.isgenerator, 'generator'),
            (inspect.iscoroutine, 'coroutine'),
            (inspect.isawaitable, 'awaitable'),
            (inspect.isasyncgenfunction, 'async generator function'),
            (inspect.isasyncgen, 'async generator iterator'),
            (inspect.istraceback, 'traceback'),
            (inspect.isframe, 'frame'),
            (inspect.iscode, 'code'),
            (inspect.isbuiltin, 'built-in function'),
            (inspect.isroutine, 'user-defined or built-in function or method'),
            (inspect.isabstract, 'abstract base class'),
            (inspect.ismethoddescriptor, 'method descriptor'),
            (inspect.isdatadescriptor, 'data descriptor'),
            (inspect.isgetsetdescriptor, 'get set descriptor'),
            (inspect.ismemberdescriptor, 'member descriptor'),
        ]
        for (check, typeName) in checks:
            if check(memberValue):
                return typeName
        typeName = str(type(memberValue))
        typeName = typeName.replace("<class '", '').replace("'>", '')
        return typeName