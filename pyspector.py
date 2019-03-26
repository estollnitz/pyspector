import inspect
import matplotlib
import matplotlib.pyplot
import numpy
import sys
import markdown
from PyQt5.QtCore import (Qt, QSortFilterProxyModel, QRegularExpression)
from PyQt5.QtGui import (QStandardItemModel, QStandardItem)
from PyQt5.QtWidgets import (QApplication, QLineEdit, QTreeView, QWidget, QHBoxLayout, QVBoxLayout,
    QTextBrowser, QSplitter)

def getMemberType(memberValue):
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

def openFile(filePath):
    '''Opens a file using the system's default application.'''
    import subprocess, os, platform
    if platform.system() == 'Darwin':
        subprocess.call(('open', filePath))
    elif platform.system() == 'Windows':
        os.startfile(filePath)
    else:
        subprocess.call(('xdg-open', filePath))

class MainWindow(QWidget):
    def __init__(self, config):
        '''Constructs a new MainWindow.'''
        super().__init__()
        self.setWindowTitle('pyspector')
        self.setGeometry(100, 100, 1000, 600)

        self.searchEdit = QLineEdit()
        self.searchEdit.setClearButtonEnabled(True)

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
        splitter.addWidget(leftWidget)
        splitter.addWidget(self.textBrowser)

        mainLayout = QHBoxLayout()
        mainLayout.addWidget(splitter)
        self.setLayout(mainLayout)
        self.show()

        self.treeModel = self.createTreeModel(config)
        self.sortFilterProxyModel = QSortFilterProxyModel(self)
        self.sortFilterProxyModel.setSourceModel(self.treeModel)
        self.sortFilterProxyModel.setFilterRegularExpression(QRegularExpression('^[^_]'))
        self.sortFilterProxyModel.setFilterKeyColumn(0)
        self.treeView.setModel(self.sortFilterProxyModel)
        selectionModel = self.treeView.selectionModel()
        selectionModel.currentChanged.connect(self.treeViewSelectionChanged)

    def createTreeModel(self, config):
        '''Creates the hierarchical model used by the TreeView.'''
        model = QStandardItemModel()
        rootItem = model.invisibleRootItem()
        for module in config['modules']:
            item = QStandardItem(module.__name__)
            item.setData({ 'type': 'module', 'value': module })
            item.setEditable(False)
            rootItem.appendRow(item)
            self.inspectObject(item, module, 1)
        return model

    def inspectObject(self, parentItem, obj, depth):
        '''Recursively adds object to the hierarchical model.'''
        members = []
        for (memberName, memberValue) in inspect.getmembers(obj):
            memberType = getMemberType(memberValue)
            members.append((memberName, memberType, memberValue))
        # sortedMembers = sorted(members, key=lambda member: member[1])
        for (memberName, memberType, memberValue) in members:
            item = QStandardItem(memberName)
            item.setData({ 'type': memberType, 'value': memberValue })
            item.setEditable(False)
            parentItem.appendRow(item)
            if depth < 2 and memberType == 'class':
                self.inspectObject(item, memberValue, depth + 1)

    def treeViewSelectionChanged(self, index, oldIndex):
        '''Determines which object was selected and displays appropriate info.'''
        sourceIndex = self.sortFilterProxyModel.mapToSource(index)
        item = self.treeModel.itemFromIndex(sourceIndex)
        self.displayInfo(item)

    def displayInfo(self, item):
        '''Updates the detailed view to show information about the selected object.'''
        data = item.data()
        memberType = data['type']
        memberValue = data['value']

        # Display the fully qualified name of the item.
        fullName = item.text()
        tempItem = item.parent()
        while tempItem:
            fullName = tempItem.text() + '.' + fullName
            tempItem = tempItem.parent()
        html = f'<h2>{fullName}</h2>'

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

        # Display the signature of callable objects.
        try:
            sig = inspect.signature(memberValue)
            sigText = str(sig)
            if sig.return_annotation != inspect.Signature.empty:
                sigText += f' -> {sig.return_annotation}'
            html += f'<p><b>Signature:</b> {item.text()}{sigText}</p>'
        except:
            pass

        # Display any documentation, converting from markdown to HTML.
        doc = inspect.getdoc(data['value'])
        if doc:
            docHtml = markdown.markdown(doc)
            html += f'<p><b>Documentation:</b><p>{docHtml}</p>'
    
        self.textBrowser.setHtml(html)

    def linkClicked(self, url):
        openFile(url.path())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    config = { 'modules': [sys, numpy, matplotlib, matplotlib.pyplot] }
    mainWindow = MainWindow(config)
    sys.exit(app.exec_())
