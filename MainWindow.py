import inspect
from markdown import markdown
from PyQt5.QtCore import (Qt, QSortFilterProxyModel, QRegularExpression)
from PyQt5.QtGui import (QStandardItemModel, QStandardItem)
from PyQt5.QtWidgets import (QApplication, QLineEdit, QTreeView, QWidget, QHBoxLayout, QVBoxLayout,
    QTextBrowser, QSplitter, QMainWindow, QAction)
from Model import Model
from utilities import openFile

# TODO
# - Add icons to tree view
# - Filter by search terms
# - Show class inheritance hierarchy
# - Provide option to show/hide "private" members (starting with underscore)
# - Provide option to show/hide inherited members
# - Always include built-in modules
# - Provide a way to add and remove other modules
# - Figure out how to get main menu working

class MainWindow(QMainWindow):
    def __init__(self, config):
        '''Constructs a new MainWindow.'''
        super().__init__()
        self.setWindowTitle('pyspector')
        self.setGeometry(100, 100, 1200, 800)

        self.initializeMenu()
 
        self.searchEdit = QLineEdit()
        self.searchEdit.setClearButtonEnabled(True)
        self.searchEdit.setPlaceholderText('Search')
        self.searchEdit.textChanged.connect(self.searchEditTextChanged)

        self.treeView = QTreeView()
        self.treeView.setUniformRowHeights(True)
        self.treeView.setAlternatingRowColors(True)
        self.treeView.setHeaderHidden(True)

        leftLayout = QVBoxLayout()
        leftLayout.addWidget(self.searchEdit)
        leftLayout.addWidget(self.treeView)
        leftLayout.setContentsMargins(0, 0, 0, 0)
        leftWidget = QWidget()
        leftWidget.setLayout(leftLayout)

        self.textBrowser = QTextBrowser()
        self.textBrowser.setOpenLinks(False)
        self.textBrowser.anchorClicked.connect(self.linkClicked)

        splitter = QSplitter()
        splitter.setHandleWidth(20)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(leftWidget)
        splitter.addWidget(self.textBrowser)
        splitter.setSizes([1, 200])

        centralLayout = QHBoxLayout()
        centralLayout.addWidget(splitter)
        centralWidget = QWidget()
        centralWidget.setLayout(centralLayout)
        self.setCentralWidget(centralWidget)
        self.show()

        self.model = Model()
        self.model.addModules(config['modules'])
        self.treeView.setModel(self.model.filteredTreeModel)
        selectionModel = self.treeView.selectionModel()
        selectionModel.currentChanged.connect(self.treeViewSelectionChanged)

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
        self.model.searchFilter = text

    def treeViewSelectionChanged(self, index, oldIndex):
        '''Determines which object was selected and displays appropriate info.'''
        item = self.model.getItemFromIndex(index)
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
        html += f'<p><b>Type:</b> {memberType}</p>'

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
        if memberType == 'class':
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

        # Display the signature of callable objects.
        try:
            sig = inspect.signature(memberValue)
            sigText = str(sig)
            # if sig.return_annotation != inspect.Signature.empty:
            #     sigText += f' -> {sig.return_annotation}'
            html += f'<p><b>Signature:</b> {memberValue.__name__}{sigText}</p>'
        except:
            pass

        # Display any documentation, converting from markdown to HTML.
        doc = inspect.getdoc(data['value'])
        if doc:
            docHtml = markdown(doc)
            html += f'<hr>{docHtml}'
    
        self.textBrowser.setHtml(html)

    def linkClicked(self, url):
        if url.scheme() == 'file':
            openFile(url.path())
        elif url.scheme() == 'item':
            parts = url.path().split('/', 2)
            print(f'select class {parts[1]} in module {parts[0]}.')
