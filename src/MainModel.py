# External imports:
import importlib
import inspect
from os.path import dirname
from PyQt5.QtCore import QSortFilterProxyModel, QRegularExpression, QModelIndex
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon, QBrush, QColor

# Local imports:
import utilities

class MainModel():
    '''Data model for pyspector.'''

    def __init__(self):
        '''Initializes a MainModel instance.'''
        self._searchText = ''
        self._matchCase = False
        self._includePrivateMembers = False
        self._includeInheritedMembers = False
        self._sortByType = True

        # Initialize icons.
        iconDir = f'{dirname(dirname(__file__))}/icons'
        self._icons = {
            'module': QIcon(f'{iconDir}/module.svg'),
            'abstract base class': QIcon(f'{iconDir}/abstract.svg'),
            'class': QIcon(f'{iconDir}/class.svg'),
            'function': QIcon(f'{iconDir}/function.svg'),
            'property': QIcon(f'{iconDir}/property.svg'),
            'object': QIcon(f'{iconDir}/object.svg')
        }

        # Create the unfiltered tree model.
        self._treeModel = QStandardItemModel()

        # Create regular expressions that exclude or include private members.
        self._excludePrivateRegEx = QRegularExpression('^[^_]|^__')
        self._includePrivateRegEx = QRegularExpression('')

        # Create regular expressions that exclude or include inherited members.
        self._excludeInheritedRegEx = QRegularExpression('^$')
        self._includeInheritedRegEx = QRegularExpression('')

        # Create a filtered tree model used to exclude or include private members.
        self._intermediateTreeModel = QSortFilterProxyModel()
        self._intermediateTreeModel.setSourceModel(self._treeModel)
        privateRegEx = self._includePrivateRegEx if self._includePrivateMembers else self._excludePrivateRegEx
        self._intermediateTreeModel.setFilterRegularExpression(privateRegEx)

        # Create a filtered tree model used to exclude or include inherited members.
        self._secondIntermediateTreeModel = QSortFilterProxyModel()
        self._secondIntermediateTreeModel.setSourceModel(self._intermediateTreeModel)
        self._secondIntermediateTreeModel.setFilterKeyColumn(2)
        inheritedRegEx = self._includeInheritedRegEx if self._includeInheritedMembers else self._excludeInheritedRegEx
        self._secondIntermediateTreeModel.setFilterRegularExpression(inheritedRegEx)

        # Create a filtered tree model that matches the search text.
        self._filteredTreeModel = QSortFilterProxyModel()
        self._filteredTreeModel.setSourceModel(self._secondIntermediateTreeModel)
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

    @property
    def includeInheritedMembers(self) -> bool:
        '''Whether or not inherited members are included in the tree.'''
        return self._includeInheritedMembers

    @includeInheritedMembers.setter
    def includeInheritedMembers(self, value: bool) -> None:
        self._includeInheritedMembers = value
        regEx = self._includeInheritedRegEx if value else self._excludeInheritedRegEx
        self._secondIntermediateTreeModel.setFilterRegularExpression(regEx)

    @property
    def sortByType(self) -> bool:
        '''Whether or not  members are sorted by type.'''
        return self._sortByType

    @sortByType.setter
    def sortByType(self, value: bool) -> None:
        self._sortByType = value
        self._sort()

    def setModuleNames(self, moduleNames) -> None:
        '''Adds the specified modules to the tree, removing any that are no longer needed.'''
        # Remove any modules that aren't in the list.
        rootItem: QStandardItem = self._treeModel.invisibleRootItem()
        for i in range(rootItem.rowCount() - 1, -1, -1):
            if rootItem.child(i).text() not in moduleNames:
                rootItem.removeRow(i)

        # Add all the modules in the list.
        for moduleName in moduleNames:
            self._addModule(moduleName)

        # Sort.
        self._sort()

    def _sort(self) -> None:
        # Sort all items alphabetically by name.
        self._treeModel.sort(0)

        # Optionally, sort by type.
        if self.sortByType:
            self._treeModel.sort(1)

    def _dumpTree(self, parentIndex = QModelIndex(), depth = 0) -> None:
        rowCount = self._treeModel.rowCount(parentIndex)
        for row in range(rowCount):
            index = self._treeModel.index(row, 0, parentIndex)
            item = self._treeModel.itemFromIndex(index)
            indent = '  ' * depth
            id = item.data()['id']
            print(f'{indent}{id}')
            self._dumpTree(index, depth + 1)

    def findItemByName(self, name: str) -> QModelIndex:
        '''Finds the item with the specified name.'''

        # Create search predicates for matching and containing name.
        if self.matchCase:
            itemHasName = lambda item: item.text() == name
            itemContainsName = lambda  item: name in item.text()
        else:
            nameNoCase = name.casefold()
            itemHasName = lambda item: item.text().casefold() == nameNoCase
            itemContainsName = lambda item: nameNoCase in item.text().casefold()

        # Try for a full match, then a partial match.
        for predicate in [itemHasName, itemContainsName]:
            index = utilities.findIndexInModel(self._filteredTreeModel, predicate)
            if index.isValid():
                break

        return index

    def findItemById(self, id: str) -> QModelIndex:
        '''Finds the item with the specified ID.'''
        print(f'looking for item with id {id}')
        predicate = lambda item: item.data()['id'] == id
        index = utilities.findIndexInModel(self._filteredTreeModel, predicate)
        return index

    def _addModule(self, moduleName, depth = 0):
        # Check to see if module has already been added.
        rootItem = self._treeModel.invisibleRootItem()
        if self._parentContainsItem(rootItem, moduleName):
            return

        try:
            module = importlib.import_module(moduleName)
            item = self._addItem(rootItem, moduleName, moduleName, 'module', module)
            self._inspectObject(item, module, depth)
        except:
            self._addItem(rootItem, moduleName, moduleName, 'module', None, error = 'Could not import module.')

    def _parentContainsItem(self, parentItem: QStandardItem, id: str) -> bool:
        for row in range(parentItem.rowCount()):
            childId = parentItem.child(row).data()['id']
            if childId == id:
                return True
        return False

    def _inspectObject(self, parentItem: QStandardItem, obj: object, depth: int) -> None:
        '''Recursively adds object to the hierarchical model.'''
        for (memberName, memberValue) in inspect.getmembers(obj):
            memberType = self._getMemberType(memberValue)

            # Skip "magic" members that are classes -- they cause problems.
            if memberName.startswith('__') and memberType == 'class':
                continue

            # Skip modules within modules.
            if memberType == 'module':
                # TODO: Should we add nested modules? Seems useful, but leads to a segfault in the
                # case of matplotlib. 
                #print(f'{"  "*depth}adding nested module {memberName}: {memberValue.__name__}')
                #self._addModule(memberValue, depth + 1)
                continue

            # Don't add the same item twice.
            parentId = parentItem.data()['id']
            id = f'{parentId}/{memberName}'
            if self._parentContainsItem(parentItem, id):
                continue

            # Check inheritance of class members.
            inheritance = 'inherited' if inspect.isclass(obj) and memberName not in obj.__dict__ else ''

            # For functions, try to include the signature in the name.
            name = memberName
            if memberType == 'function':
                try:
                    name += str(inspect.signature(memberValue))
                except:
                    pass

            # Add an item for the current member.
            item = self._addItem(parentItem, id, name, memberType, memberValue, inheritance)

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

    def _addItem(self, parentItem: QStandardItem, id: str, name: str, type: str, value: object, inheritance: str = '', error: str = '') -> QStandardItem:
        '''Adds one model item to a parent model item.'''
        key = type if type in self._icons else 'object'
        item1 = QStandardItem(self._icons[key], name)
        item1.setData({ 'id': id, 'type': type, 'value': value, 'error': error })
        item1.setEditable(False)
        if len(error):
            item1.setBackground(QBrush(QColor(255, 0, 0, 64)))
        item2 = QStandardItem(type)
        item2.setEditable(False)
        item3 = QStandardItem(inheritance)
        item3.setEditable(False)
        parentItem.appendRow([item1, item2, item3])
        return item1

    def _getMemberType(self, memberValue: object) -> str:
        '''Attempts to determine the type of a member from its value.'''
        if inspect.ismodule(memberValue):
            return 'module'
        if inspect.isabstract(memberValue):
            return 'abstract base class'
        if inspect.isclass(memberValue):
            return 'class'
        if inspect.isfunction(memberValue) or inspect.isbuiltin(memberValue) or inspect.isroutine(memberValue):
            return 'function'
        if inspect.isdatadescriptor(memberValue):
            return 'property'
        return 'object'
