import inspect
from PyQt5.QtCore import (QSortFilterProxyModel, QRegularExpression, QModelIndex)
from PyQt5.QtGui import (QStandardItemModel, QStandardItem, QIcon)

class Model():
    '''Data model for pyspector.'''

    def __init__(self):
        '''Does this appear anywhere?'''
        self._searchText = ''
        self._matchCase = False
        self._includePrivateMembers = False

        # Initialize icons.
        self._icons = {
            'module': QIcon('icons/module.svg'),
            'abstract base class': QIcon('icons/abstract.svg'),
            'class': QIcon('icons/class.svg'),
            'function': QIcon('icons/function.svg'),
            'built-in function': QIcon('icons/function.svg'),
            'user-defined or built-in function or method': QIcon('icons/function.svg'),
            'data descriptor': QIcon('icons/property.svg'),
            'object': QIcon('icons/object.svg')
        }

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
        for module in modules:
            self._addModule(module)
        self._filteredTreeModel.sort(0)

    def _dumpTree(self, parentIndex = QModelIndex(), depth = 0) -> None:
        rowCount = self._treeModel.rowCount(parentIndex)
        for row in range(rowCount):
            index = self._treeModel.index(row, 0, parentIndex)
            item = self._treeModel.itemFromIndex(index)
            indent = '  ' * depth
            id = item.data()['id']
            print(f'{indent}{id}')
            self._dumpTree(index, depth + 1)

    def findItem(self, id: str) -> QModelIndex:
        '''Finds the item with the specified ID.'''
        print(f'looking for item with id {id}')
        index = self._findItem(QModelIndex(), id)
        if index.isValid():
            # Convert unfiltered index to a filtered index.
            intermediateIndex = self._intermediateTreeModel.mapFromSource(index)
            filteredIndex = self._filteredTreeModel.mapFromSource(intermediateIndex)
            return filteredIndex
        return index

    def _findItem(self, parentIndex: QModelIndex, id: str) -> QModelIndex:
        rowCount = self._treeModel.rowCount(parentIndex)
        for row in range(rowCount):
            index = self._treeModel.index(row, 0, parentIndex)
            # Check this item.
            item = self._treeModel.itemFromIndex(index)
            if item.data()['id'] == id:
                return index
            # Recurse into children.
            childIndex = self._findItem(index, id)
            if childIndex.isValid():
                return childIndex
        return QModelIndex()

    def _addModule(self, module, depth = 0):
        # Check to see if module has already been added.
        rootItem = self._treeModel.invisibleRootItem()
        if self._parentContainsItem(rootItem, module.__name__):
            print(f'module {module.__name__} is already present')
            return
        item = self._addItem(rootItem, module.__name__, module.__name__, 'module', module)
        self._inspectObject(item, module, depth)

    def _parentContainsItem(self, parentItem: QStandardItem, id: str) -> bool:
        for row in range(parentItem.rowCount()):
            childId = parentItem.child(row).data()['id']
            if childId == id:
                return True
        return False

    def _inspectObject(self, parentItem: QStandardItem, obj: object, depth) -> None:
        '''Recursively adds object to the hierarchical model.'''
        for (memberName, memberValue) in inspect.getmembers(obj):
            # Skip "magic" members.
            if memberName.startswith('__'):
                continue

            memberType = self._getMemberType(memberValue)

            # Skip modules within modules.
            if memberType == 'module':
                # TODO: Should we add nested modules? Seems useful, but leads to a segfault in the
                # case of matplotlib. 
                #print(f'{"  "*depth}adding nested module {memberName}: {memberValue.__name__}')
                #self._addModule(memberValue, depth + 1)
                continue

            parentId = parentItem.data()['id']
            id = f'{parentId}/{memberName}'
            if self._parentContainsItem(parentItem, id):
                continue
            item = self._addItem(parentItem, id, memberName, memberType, memberValue)

            # Recurse into classes (but not if it's the same class we're inspecting).
            if 'class' in memberType and memberValue != obj:
                print(f'{"  "*depth}inspecting class {memberName} in module {memberValue.__module__}')
                self._inspectObject(item, memberValue, depth + 1)

            # Recurse into property getter, setter, deleter functions.
            # TODO: Generalize this to data descriptors other than just the 'property' class.
            if type(memberValue) == property:
                if memberValue.fget:
                    self._addItem(item, f'{id}/get', '[get]', 'function', memberValue.fget)
                if memberValue.fset:
                    self._addItem(item, f'{id}/set', '[set]', 'function', memberValue.fset)
                if memberValue.fdel:
                    self._addItem(item, f'{id}/delete', '[delete]', 'function', memberValue.fdel)

    def _addItem(self, parentItem: QStandardItem, id: str, name: str, type: str, value: object) -> QStandardItem:
        '''Adds one model item to a parent model item.'''
        key = type if type in self._icons else 'object'
        item = QStandardItem(self._icons[key], name)
        item.setData({ 'id': id, 'type': type, 'value': value })
        item.setEditable(False)
        parentItem.appendRow(item)
        return item

    def _getMemberType(self, memberValue: object) -> str:
        '''Attempts to determine the type of a member from its value.'''
        checks = [
            (inspect.ismodule, 'module'),
            (inspect.isabstract, 'abstract base class'),
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
