# External imports:
from PyQt5.QtCore import Qt, QSortFilterProxyModel
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLabel, QLineEdit, QVBoxLayout

# Local imports:
from ModuleSelectionModel import ModuleSelectionModel
from TreeView import TreeView

class ModuleSelectionDialog(QDialog):
    '''A dialog for choosing which modules to inspect.'''

    _moduleSelectionModel = None

    def __init__(self, parent, selectedModuleNames):
        '''Initializes a ModuleSelectionModel instance.'''
        super().__init__(parent)
        self.setWindowModality(Qt.ApplicationModal)

        self._selectedModuleNames = selectedModuleNames
        self._createModel()

        label = QLabel()
        label.setText('Select modules')

        self._searchEdit = QLineEdit()
        self._searchEdit.setClearButtonEnabled(True)
        self._searchEdit.setPlaceholderText('Search')
        self._searchEdit.textChanged.connect(self._searchEditTextChanged)

        self._treeView = TreeView()
        self._treeView.setModel(self._sortFilterProxyModel)
        self._treeView.setSortingEnabled(True)
        self._treeView.sortByColumn(0, Qt.AscendingOrder)
        self._treeView.setColumnWidth(0, 200)
        self._treeView.setColumnWidth(1, 600)
        self._treeView.setMinimumWidth(850)
        self._treeView.setMinimumHeight(650)
        self._treeView.dataChanged

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self._acceptButtonPressed)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(label)
        mainLayout.addWidget(self._searchEdit)
        mainLayout.addWidget(self._treeView)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

    @property
    def selectedModuleNames(self):
        '''The list of selected module names.'''
        return self._selectedModuleNames

    def _createModel(self):
        '''Creates the hierarchical model of items to display.'''
        # Create a cached hierarchy of all available modules, if we haven't already.
        # TODO: This time-consuming operation blocks the UI. Can we do it in the background,
        # or at least show a spinner while the work is being done?
        if ModuleSelectionDialog._moduleSelectionModel == None:
            ModuleSelectionDialog._moduleSelectionModel = ModuleSelectionModel()

        # Build the corresponding tree of Qt standard items.
        self._model = QStandardItemModel()
        self._model.setHorizontalHeaderLabels(['Module', 'Location'])
        rootItem = self._model.invisibleRootItem()
        self._createItems(rootItem, ModuleSelectionDialog._moduleSelectionModel.allModules)

        # Create a proxy for filtering.
        self._sortFilterProxyModel: QSortFilterProxyModel = QSortFilterProxyModel()
        self._sortFilterProxyModel.setSourceModel(self._model)
        self._sortFilterProxyModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self._sortFilterProxyModel.setRecursiveFilteringEnabled(True)

    def _createItems(self, parentItem: QStandardItem, moduleDataList: list) -> None:
        '''Creates the items associsted with a list of module data, and recurses.'''
        for moduleData in moduleDataList:
            item1 = QStandardItem(moduleData.name)
            item1.setCheckable(True)
            item1.setEditable(False)
            isChecked = moduleData.name in self._selectedModuleNames
            item1.setCheckState(Qt.Checked if isChecked else Qt.Unchecked)
            item2 = QStandardItem(moduleData.location)
            item2.setEditable(False)
            parentItem.appendRow((item1, item2))
            self._createItems(item1, moduleData.children)

    def _searchEditTextChanged(self, text: str) -> None:
        '''Filters the tree view to show just those items relevant to the search text.'''
        self._sortFilterProxyModel.setFilterFixedString(text)

    def _acceptButtonPressed(self) -> None:
        '''Gathers a list of selected module names and closes the dialog.'''
        selectedModuleNames = []
        self._listSelectedModules(self._model.invisibleRootItem(), selectedModuleNames)
        self._selectedModuleNames = selectedModuleNames
        self.accept()

    def _listSelectedModules(self, parentItem: QStandardItem, selectedModuleNames: list) -> None:
        '''Recursively gathers a list of selected module names.'''
        for i in range(parentItem.rowCount()):
            item = parentItem.child(i)
            if item.checkState() == Qt.Checked:
                selectedModuleNames.append(item.text())
            self._listSelectedModules(item, selectedModuleNames)
