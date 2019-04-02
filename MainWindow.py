import inspect
from markdown import markdown
from PyQt5.QtCore import (Qt, QSortFilterProxyModel, QRegularExpression)
from PyQt5.QtGui import (QStandardItemModel, QStandardItem)
from PyQt5.QtWidgets import (QApplication, QLineEdit, QTreeView, QWidget, QHBoxLayout, QVBoxLayout,
    QTextBrowser, QSplitter, QMainWindow, QAction, QCheckBox)
from Model import Model
from utilities import openFile

# TODO
# - Always include built-in modules
# - Provide a way to add and remove other modules
# - Figure out how to get main menu working

class MainWindow(QMainWindow):
    def __init__(self, config):
        '''Constructs a new MainWindow.'''
        super().__init__()

        # Create model.
        self._model = Model()
        self._model.addModules(config['modules'])

        # Configure window.
        self.setWindowTitle('pyspector')
        self.setGeometry(100, 100, 1200, 800)
        self.initializeMenu()

        # Crete user interface widgets.
        self._searchEdit = QLineEdit()
        self._searchEdit.setClearButtonEnabled(True)
        self._searchEdit.setPlaceholderText('Search')
        self._searchEdit.textChanged.connect(self.searchEditTextChanged)

        matchCaseCheckBox = QCheckBox()
        matchCaseCheckBox.setText('Match case')
        matchCaseCheckBox.setCheckState(Qt.Checked if self._model.matchCase else Qt.Unchecked)
        matchCaseCheckBox.stateChanged.connect(self.matchCaseCheckBoxStateChanged)

        includePrivateCheckBox = QCheckBox()
        includePrivateCheckBox.setText('Include private members')
        includePrivateCheckBox.setCheckState(Qt.Checked if self._model.includePrivateMembers else Qt.Unchecked)
        includePrivateCheckBox.stateChanged.connect(self.includePrivateCheckBoxStateChanged)

        includeInheritedCheckBox = QCheckBox()
        includeInheritedCheckBox.setText('Include inherited members')
        includeInheritedCheckBox.setCheckState(Qt.Checked if self._model.includeInheritedMembers else Qt.Unchecked)
        includeInheritedCheckBox.stateChanged.connect(self.includeInheritedCheckBoxStateChanged)

        sortByTypeCheckBox = QCheckBox()
        sortByTypeCheckBox.setText('Sort by type')
        sortByTypeCheckBox.setCheckState(Qt.Checked if self._model.sortByType else Qt.Unchecked)
        sortByTypeCheckBox.stateChanged.connect(self.sortByTypeCheckBoxStateChanged)

        self._treeView = QTreeView()
        self._treeView.setUniformRowHeights(True)
        self._treeView.setAlternatingRowColors(True)
        self._treeView.setHeaderHidden(True)
        self._treeView.setModel(self._model.filteredTreeModel)
        self._treeView.hideColumn(1)
        self._treeView.hideColumn(2)
        selectionModel = self._treeView.selectionModel()
        selectionModel.currentChanged.connect(self.treeViewSelectionChanged)

        leftLayout = QVBoxLayout()
        leftLayout.addWidget(self._searchEdit)
        leftLayout.addWidget(matchCaseCheckBox)
        leftLayout.addWidget(includePrivateCheckBox)
        leftLayout.addWidget(includeInheritedCheckBox)
        leftLayout.addWidget(sortByTypeCheckBox)
        leftLayout.addWidget(self._treeView)
        leftLayout.setContentsMargins(0, 0, 0, 0)
        leftWidget = QWidget()
        leftWidget.setLayout(leftLayout)

        self._textBrowser = QTextBrowser()
        self._textBrowser.setOpenLinks(False)
        self._textBrowser.anchorClicked.connect(self.linkClicked)

        splitter = QSplitter()
        splitter.setHandleWidth(20)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(leftWidget)
        splitter.addWidget(self._textBrowser)
        splitter.setSizes([300, 900])

        centralLayout = QHBoxLayout()
        centralLayout.addWidget(splitter)
        centralWidget = QWidget()
        centralWidget.setLayout(centralLayout)
        self.setCentralWidget(centralWidget)

        # Show the window.
        self.show()

    def initializeMenu(self):
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('File')
        quitAction = QAction('Quit', self)
        quitAction.setShortcut('Cmd+Q')
        quitAction.setStatusTip('Exit application')
        quitAction.triggered.connect(self.close)
        fileMenu.addAction(quitAction)

    def searchEditTextChanged(self, text):
        '''Filters the tree view to show just those items relevant to the search text.'''
        self._model.searchText = text

    def matchCaseCheckBoxStateChanged(self, state):
        '''Determines whether matching is case-sensitive.'''
        self._model.matchCase = state

    def includePrivateCheckBoxStateChanged(self, state):
        ''' Includes or excludes private members from the tree view.'''
        self._model.includePrivateMembers = state

    def includeInheritedCheckBoxStateChanged(self, state):
        ''' Includes or excludes inherited members from the tree view.'''
        self._model.includeInheritedMembers = state

    def sortByTypeCheckBoxStateChanged(self, state):
        ''' Includes or excludes private members from the tree view.'''
        self._model.sortByType = state

    def treeViewSelectionChanged(self, index, oldIndex):
        '''Determines which object was selected and displays appropriate info.'''
        item = self._model.getItemFromIndex(index)
        self.displayInfo(item)

    def displayInfo(self, item):
        '''Updates the detailed view to show information about the selected object.'''
        data = item.data()
        memberType = data['type']
        memberValue = data['value']

        # Display the fully qualified name of the item.
        # TODO: Use __qualname__?
        fullName = item.text()
        tempItem = item.parent()
        while tempItem:
            fullName = tempItem.text() + '.' + fullName
            tempItem = tempItem.parent()
        html = f'<h2>{fullName}</h2>'
        if hasattr(memberValue, '__qualname__'):
            html += f'<h2>{memberValue.__qualname__}</h2>'

        # Display the type.
        displayType = memberType
        if memberType == 'object':
            displayType = str(type(memberValue))
            displayType = displayType.replace("<class '", '').replace("'>", '')
        html += f'<p><b>Type:</b> {displayType}</p>'

        # Display object value.
        if memberType == 'object':
            html += f'<p><b>Value:</b> {repr(memberValue)}'

        # Display the filename for modules.
        # See if we can find the source file for other objects.
        if memberType == 'module' and hasattr(memberValue, '__file__'):
            html += f'<p><b>File:</b> <a href="file:{memberValue.__file__}">{memberValue.__file__}</a></p>'
        else:
            try:
                sourceFile = inspect.getsourcefile(memberValue)
                lines = inspect.getsourcelines(memberValue)
                html += f'<p><b>File:</b> <a href="file:{sourceFile}">{sourceFile} ({lines[1]})</a></p>'
            except:
                pass

        # Display the inheritance hierarchy of classes.
        if 'class' in memberType:
            try:
                baseClasses = inspect.getmro(memberValue)
                if len(baseClasses) > 1:
                    html += '<p><b>Base classes:</b></p><ul>'
                    baseClasses = list(baseClasses)[1:] # omit the first entry
                    for baseClass in reversed(baseClasses):
                        moduleName = baseClass.__module__
                        className = baseClass.__qualname__
                        html += f'<li><a href="item:{moduleName}/{className}">{className}</a> from {moduleName}</li>'
                    html += '</ul>'
                derivedClasses = memberValue.__subclasses__()
                if len(derivedClasses) > 0:
                    html += '<p><b>Derived classes:</b></p><ul>'
                    for derivedClass in derivedClasses:
                        moduleName = derivedClass.__module__
                        className = derivedClass.__qualname__
                        html += f'<li><a href="item:{moduleName}/{className}">{className}</a> from {moduleName}</li>'
                    html += '</ul>'
            except:
                pass

        # Display the signature of callable objects.
        try:
            sig = inspect.signature(memberValue)
            sigText = str(sig)
            # if sig.return_annotation != inspect.Signature.empty:
            #     sigText += f' -> {sig.return_annotation}'
            html += f'<p><b>Signature:</b> {memberValue.__name__}{sigText}</p>'
        except:
            pass

        # Display documentation for non-object types, converting from markdown to HTML.
        if memberType != 'object':
            doc = inspect.getdoc(data['value'])
            if doc:
                docHtml = markdown(doc)
                html += f'<hr>{docHtml}'
    
        self._textBrowser.setHtml(html)

    def linkClicked(self, url):
        if url.scheme() == 'file':
            # Open the file in an external application.
            openFile(url.path())
        elif url.scheme() == 'item':
            # Clear the search and select the item (if present in the tree).
            self._searchEdit.clear()
            self._model.searchText = ''
            index = self._model.findItem(url.path())
            if index.isValid():
                self._treeView.setCurrentIndex(index)
