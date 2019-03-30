import inspect
from PyQt5.QtCore import (QSortFilterProxyModel, QRegularExpression, QModelIndex)
from PyQt5.QtGui import (QStandardItemModel, QStandardItem)

class Model():
    '''Data model for pyspector.'''

    def __init__(self):
        '''Does this appear anywhere?'''
        self._searchText = ''
        self._matchCase = False
        self._includePrivateMembers = False

        # Create the unfiltered tree model.
        self._treeModel = QStandardItemModel()

        # Create regular expressions that exclude or include private members.
        self._excludePrivateRegEx = QRegularExpression('^[^_]|^__')
        self._includePrivateRegEx = QRegularExpression('')

        # Create a filtered tree model used to exclude or include private members.
        self._intermediateTreeModel = QSortFilterProxyModel()
        self._intermediateTreeModel.setSourceModel(self._treeModel)
        regEx = self._includePrivateRegEx if self._includePrivateMembers else self._excludePrivateRegEx
        self._intermediateTreeModel.setFilterRegularExpression(regEx)

        # Create a filtered tree model that matches the search text.
        self._filteredTreeModel = QSortFilterProxyModel()
        self._filteredTreeModel.setSourceModel(self._intermediateTreeModel)
        self._filteredTreeModel.setRecursiveFilteringEnabled(True)
        self._filteredTreeModel.setFilterFixedString(self._searchText)
        self._filteredTreeModel.setFilterCaseSensitivity(1 if self._matchCase else 0)

    @property
    def filteredTreeModel(self) -> QSortFilterProxyModel:
        '''The filtered version of the tree model.'''
        return self._filteredTreeModel

    @property
    def searchText(self) -> str:
        '''The current search text.'''
        return self._searchText

    @searchText.setter
    def searchText(self, value: str) -> None:
        self._searchText = value
        self._filteredTreeModel.setFilterFixedString(value)

    @property
    def matchCase(self) -> bool:
        '''Whether or not case-sensitive matching is used.'''
        return self._matchCase

    @matchCase.setter
    def matchCase(self, value: bool) -> None:
        self._matchCase = value
        self._filteredTreeModel.setFilterCaseSensitivity(1 if value else 0)

    @property
    def includePrivateMembers(self) -> bool:
        '''Whether or not private members (beginning with "_") are included in the tree.'''
        return self._includePrivateMembers

    @includePrivateMembers.setter
    def includePrivateMembers(self, value: bool) -> None:
        self._includePrivateMembers = value
        regEx = self._includePrivateRegEx if value else self._excludePrivateRegEx
        self._intermediateTreeModel.setFilterRegularExpression(regEx)

    def getItemFromIndex(self, index: QModelIndex) -> QStandardItem:
        '''Returns the model item corresponding to the given index.'''
        intermediateIndex = self._filteredTreeModel.mapToSource(index)
        unfilteredIndex = self._intermediateTreeModel.mapToSource(intermediateIndex)
        item = self._treeModel.itemFromIndex(unfilteredIndex)
        return item

    def addModules(self, modules: list) -> None:
        '''Adds all the members of the specified modules to the tree.'''
        rootItem = self._treeModel.invisibleRootItem()
        for module in modules:
            item = self._addItem(rootItem, module.__name__, 'module', module)
            self._inspectObject(item, module)

    def _inspectObject(self, parentItem: QStandardItem, obj: object) -> None:
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

    def _addItem(self, parentItem: QStandardItem, name: str, type: str, value: object) -> QStandardItem:
        '''Adds one model item to a parent model item.'''
        item = QStandardItem(name)
        item.setData({ 'type': type, 'value': value })
        item.setEditable(False)
        parentItem.appendRow(item)
        return item

    def _getMemberType(self, memberValue: object) -> str:
        '''Attempts to determine the type of a member from its value.'''
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
