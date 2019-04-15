# External imports:
import inspect
import platform
from html import escape
from markdown import markdown
from PyQt5.QtCore import Qt, QEvent, QItemSelectionModel, QModelIndex, QUrl
from PyQt5.QtGui import (QColor, QFont, QKeySequence, QStandardItem, QStandardItemModel,
    QTextCursor, QTextFormat)
from PyQt5.QtWidgets import (QAction, QCheckBox, QHBoxLayout, QMainWindow, QPlainTextEdit,
    QPushButton, QShortcut, QSplitter, QTextBrowser, QTextEdit, QVBoxLayout, QWidget)
import webbrowser

# Local imports:
from Config import Config
from MainModel import MainModel
from ModuleSelectionDialog import ModuleSelectionDialog
from PythonSyntaxHighlighter import PythonSyntaxHighlighter, Theme
from rstToHtml import rstToHtml
from SearchEdit import SearchEdit
from TreeView import TreeView
import utilities

class MainWindow(QMainWindow):
    '''The main window of the application.'''

    def __init__(self, config: Config):
        '''Initializes a MainWindow instance.'''
        super().__init__()

        # Store configuration.
        self._config = config

        # Create model.
        self._model = MainModel()
        self._model.matchCase = config.matchCase
        self._model.includePrivateMembers = config.includePrivateMembers
        self._model.includeInheritedMembers = config.includeInheritedMembers
        self._model.sortByType = config.sortByType
        self._model.setModuleNames(config.moduleNames)

        # Configure window.
        self.setWindowTitle('pyspector')
        self.setGeometry(100, 100, 1200, 800)

        # Crete user interface widgets.
        self._searchEdit = SearchEdit()
        self._searchEdit.textChanged.connect(self._searchEditTextChanged)
        self._searchEdit.delayedTextChanged.connect(self._selectFirstMatch)

        matchCaseCheckBox = QCheckBox()
        matchCaseCheckBox.setText('Match case')
        matchCaseCheckBox.setCheckState(Qt.Checked if self._model.matchCase else Qt.Unchecked)
        matchCaseCheckBox.stateChanged.connect(self._matchCaseCheckBoxStateChanged)

        includePrivateCheckBox = QCheckBox()
        includePrivateCheckBox.setText('Include private members')
        includePrivateCheckBox.setCheckState(Qt.Checked if self._model.includePrivateMembers else Qt.Unchecked)
        includePrivateCheckBox.stateChanged.connect(self._includePrivateCheckBoxStateChanged)

        includeInheritedCheckBox = QCheckBox()
        includeInheritedCheckBox.setText('Include inherited members')
        includeInheritedCheckBox.setCheckState(Qt.Checked if self._model.includeInheritedMembers else Qt.Unchecked)
        includeInheritedCheckBox.stateChanged.connect(self._includeInheritedCheckBoxStateChanged)

        sortByTypeCheckBox = QCheckBox()
        sortByTypeCheckBox.setText('Sort by type')
        sortByTypeCheckBox.setCheckState(Qt.Checked if self._model.sortByType else Qt.Unchecked)
        sortByTypeCheckBox.stateChanged.connect(self._sortByTypeCheckBoxStateChanged)

        self._treeView = TreeView()
        self._treeView.setUniformRowHeights(True)
        self._treeView.setAlternatingRowColors(True)
        self._treeView.setHeaderHidden(True)
        self._treeView.setModel(self._model.filteredTreeModel)
        self._treeView.hideColumn(1)
        self._treeView.hideColumn(2)
        selectionModel = self._treeView.selectionModel()
        selectionModel.currentChanged.connect(self._treeViewSelectionChanged)

        selectModulesButton = QPushButton()
        selectModulesButton.setText('Select modules')
        selectModulesButton.clicked.connect(self._selectModulesButtonClicked)

        leftLayout = QVBoxLayout()
        leftLayout.addWidget(self._searchEdit)
        leftLayout.addWidget(matchCaseCheckBox)
        leftLayout.addWidget(includePrivateCheckBox)
        leftLayout.addWidget(includeInheritedCheckBox)
        leftLayout.addWidget(sortByTypeCheckBox)
        leftLayout.addWidget(self._treeView)
        leftLayout.addWidget(selectModulesButton)
        leftLayout.setContentsMargins(0, 0, 0, 0)
        leftWidget = QWidget()
        leftWidget.setLayout(leftLayout)

        self._textBrowser = QTextBrowser()
        self._textBrowser.setOpenLinks(False)
        self._textBrowser.anchorClicked.connect(self._linkClicked)

        fontFamily = 'Menlo' if platform.system() == 'Darwin' else 'Consolas'
        fixedPitchFont = QFont(fontFamily)
        fixedPitchFont.setFixedPitch(True)
        self._sourceTextViewer = QPlainTextEdit()
        self._sourceTextViewer.setReadOnly(True)
        self._sourceTextViewer.setFont(fixedPitchFont)
        self._sourceTextViewer.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._sourceTextHighlighter = PythonSyntaxHighlighter(self._sourceTextViewer.document())

        rightSplitter = QSplitter()
        rightSplitter.setOrientation(Qt.Vertical)
        rightSplitter.setHandleWidth(20)
        rightSplitter.setChildrenCollapsible(False)
        rightSplitter.addWidget(self._textBrowser)
        rightSplitter.addWidget(self._sourceTextViewer)

        splitter = QSplitter()
        splitter.setHandleWidth(20)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(leftWidget)
        splitter.addWidget(rightSplitter)
        splitter.setSizes([300, 900])

        centralLayout = QHBoxLayout()
        centralLayout.addWidget(splitter)
        centralWidget = QWidget()
        centralWidget.setLayout(centralLayout)
        self.setCentralWidget(centralWidget)

        # Create keyboard shortcuts.
        findShortcut = QShortcut(QKeySequence.Find, centralWidget)
        findShortcut.activated.connect(self._findShortcutActivated)

        # Make sure colors are correct for current palette.
        self._updateColors()

        # Show the window.
        self.show()

    def _findShortcutActivated(self) -> None:
        self._searchEdit.selectAll()
        self._searchEdit.setFocus()

    def _searchEditTextChanged(self, text: str) -> None:
        '''Filters the tree view to show just those items relevant to the search text.'''
        self._model.searchText = text

    def _matchCaseCheckBoxStateChanged(self, state: Qt.CheckState) -> None:
        '''Determines whether matching is case-sensitive.'''
        isChecked = state == Qt.Checked
        self._config.matchCase = isChecked
        self._model.matchCase = isChecked
        self._selectFirstMatch()

    def _includePrivateCheckBoxStateChanged(self, state: Qt.CheckState) -> None:
        ''' Includes or excludes private members from the tree view.'''
        isChecked = state == Qt.Checked
        self._config.includePrivateMembers = isChecked
        self._model.includePrivateMembers = isChecked
        self._selectFirstMatch()

    def _includeInheritedCheckBoxStateChanged(self, state: Qt.CheckState) -> None:
        ''' Includes or excludes inherited members from the tree view.'''
        isChecked = state == Qt.Checked
        self._config.includeInheritedMembers = isChecked
        self._model.includeInheritedMembers = isChecked
        self._selectFirstMatch()

    def _sortByTypeCheckBoxStateChanged(self, state: Qt.CheckState) -> None:
        ''' Includes or excludes private members from the tree view.'''
        isChecked = state == Qt.Checked
        self._config.sortByType = isChecked
        self._model.sortByType = isChecked

    def _selectFirstMatch(self) -> None:
        # Select the first match to the current search text (if any).
        searchText = self._model.searchText
        index = self._model.findItemByName(searchText) if len(searchText) else QModelIndex()
        if index.isValid():
            self._treeView.expandAll()
            self._treeView.scrollTo(index)
            self._treeView.selectionModel().select(index, QItemSelectionModel.ClearAndSelect)
            self._updateInfo(index)
        else:
            self._treeView.collapseAll()
            selectedIndexes = self._treeView.selectedIndexes()
            if len(selectedIndexes):
                self._treeView.scrollTo(selectedIndexes[0])

    def changeEvent(self, event: QEvent) -> None:
        '''Updates colors when palette change events occur.'''
        if event.type() == QEvent.PaletteChange:
            self._updateColors()

    def _updateColors(self) -> None:
        '''Modifies colors when the palette changes from dark to light or vice versa.'''
        isDark = self.palette().window().color().valueF() < 0.5
        textColor = 'silver' if isDark else 'black'
        linkColor = 'steelBlue' if isDark else 'blue'
        self._textBrowser.document().setDefaultStyleSheet(f'* {{ color: {textColor}; }} a {{ color: {linkColor}; }}')
        self._updateInfo()
        self._sourceTextViewer.setStyleSheet(f'QPlainTextEdit {{ color: {textColor}; }}')
        self._sourceTextHighlighter.theme = Theme.DARK if isDark else Theme.LIGHT

    def _treeViewSelectionChanged(self, index: QModelIndex, oldIndex: QModelIndex) -> None:
        '''Displays appropriate information whenever the tree view selection changes.'''
        self._updateInfo(index)

    def _updateInfo(self, index: QModelIndex = QModelIndex()) -> None:
        '''Determines which object is selected and displays appropriate info.'''
        if not index.isValid():
            selectedIndexes = self._treeView.selectedIndexes()
            if len(selectedIndexes):
                index = selectedIndexes[0]

        item = utilities.getItemFromIndex(self._model.filteredTreeModel, index)
        if item:
            self._displayInfo(item)
        else:
            self._textBrowser.clear()

    def _displayInfo(self, item: QStandardItem) -> None:
        '''Updates the detailed view to show information about the selected object.'''
        data = item.data()
        memberType = data['type']
        memberValue = data['value']
        error = data['error']

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
        html += f'<p><b>Type:</b> {escape(displayType)}</p>'

        # Display object value.
        if memberType == 'object':
            html += f'<p><b>Value:</b> {escape(repr(memberValue))}'

        # Display error message.
        if len(error):
            html += f'<p><b>Error:</b> {escape(error)}'

        # Display the filename for modules.
        # See if we can find the source file for other objects.
        if memberType == 'module' and hasattr(memberValue, '__file__'):
            html += f'<p><b>File:</b> <a href="file:{memberValue.__file__}">{memberValue.__file__}</a></p>'
            self._displaySource(memberValue.__file__)
        else:
            try:
                # Substitute the getter, setter, or deleter for a property instance.
                # TODO: Generalize this to data descriptors other than just the 'property' class.
                if isinstance(memberValue, property):
                    if memberValue.fget:
                        memberValue = memberValue.fget
                    elif memberValue.fset:
                        memberValue = memberValue.fset
                    elif memberValue.fdel:
                        memberValue = memberValue.fdel

                # Note that inspect.getsourcelines calls unwrap, while getsourcefile does not.
                sourceFile = inspect.getsourcefile(inspect.unwrap(memberValue))
                lines = inspect.getsourcelines(memberValue)
                html += f'<p><b>File:</b> <a href="file:{sourceFile}">{sourceFile} ({lines[1]})</a></p>'
                self._displaySource(sourceFile, lines[1], len(lines[0]))
            except:
                self._displaySourceError('Could not locate source code.')

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
            signature = str(inspect.signature(memberValue))
            html += f'<p><b>Signature:</b> {memberValue.__name__}{signature}</p>'
        except:
            pass

        # Display documentation for non-object types, converting from reStructuredText or markdown
        # to HTML.
        if memberType != 'object':
            doc = inspect.getdoc(data['value'])
            if doc:
                # Check for special cases where docstrings are plain text.
                if fullName in ['sys']:
                    docHtml = f'<pre>{escape(doc)}</pre>'
                else:
                    # If we encounter improper reStructuredText markup leading to an exception
                    # or a "problematic" span, just treat the input as markdown.
                    try:
                        docHtml = rstToHtml(doc)
                        if '<span class="problematic"' in docHtml:
                            docHtml = markdown(doc)
                    except:
                        docHtml = markdown(doc)
                html += f'<hr>{docHtml}'
    
        self._textBrowser.setHtml(html)

    def _displaySource(self, filename: str, startLine: int = None, lineCount: int = None) -> None:
        '''Shows source code within the source text viewer.'''
        try:
            # Read the file and populate the source text viewer.
            with open(filename) as fp:
                lines = fp.readlines()
                self._sourceTextViewer.setPlainText(''.join(lines))

            # Restart the Python syntax highlighter.
            self._sourceTextHighlighter.setDocument(self._sourceTextViewer.document())

            # If line numbers are available, highlight the lines encompassing the currently
            # selected member.
            if startLine != None:
                cursor = QTextCursor(self._sourceTextViewer.document())
                cursor.movePosition(QTextCursor.Start)
                if startLine > 1:
                    cursor.movePosition(QTextCursor.NextBlock, QTextCursor.MoveAnchor, startLine - 1)
                self._sourceTextViewer.setTextCursor(cursor)
                cursor.movePosition(QTextCursor.NextBlock, QTextCursor.KeepAnchor, lineCount)
                lineColor = QColor(255, 255, 0, 48)
                extraSelection = QTextEdit.ExtraSelection()
                extraSelection.format.setBackground(lineColor)
                extraSelection.format.setProperty(QTextFormat.FullWidthSelection, True)
                extraSelection.cursor = cursor
                self._sourceTextViewer.setExtraSelections([extraSelection])
                self._sourceTextViewer.centerCursor()
            else:
                self._sourceTextViewer.setExtraSelections([])
        except:
            self._displaySourceError('Could not open file.')

    def _displaySourceError(self, errorMessage: str) -> None:
        '''Displays an error message within the source text viewer.'''
        self._sourceTextViewer.setPlainText(errorMessage)
        self._sourceTextViewer.setExtraSelections([])
        self._sourceTextHighlighter.setDocument(None)

    def _linkClicked(self, url: QUrl) -> None:
        scheme = url.scheme()
        if scheme == 'file':
            # Open the file in an external application.
            utilities.openFile(url.path())
        elif scheme == 'http' or scheme == 'https':
            # Open the web page in the default browser.
            webbrowser.open_new_tab(url.toString())
        elif scheme == 'item':
            # Clear the search and select the item (if present in the tree).
            self._searchEdit.clear()
            self._model.searchText = ''
            index = self._model.findItemById(url.path())
            if index.isValid():
                self._treeView.setCurrentIndex(index)

    def _selectModulesButtonClicked(self) -> None:
        self._moduleSelectionDialog = ModuleSelectionDialog(self, self._config.moduleNames)
        self._moduleSelectionDialog.finished.connect(self._moduleSelectionDialogFinished)
        self._moduleSelectionDialog.open()

    def _moduleSelectionDialogFinished(self, result: int) -> None:
        if result == ModuleSelectionDialog.Accepted:
            moduleNames = self._moduleSelectionDialog.selectedModuleNames
            self._model.setModuleNames(moduleNames)
            self._config.moduleNames = moduleNames
            self._selectFirstMatch()
