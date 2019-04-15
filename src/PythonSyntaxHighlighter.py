'''
Color syntax highlighting for the Python language.
'''

# External imports:
from enum import Enum
import re
import sys
import keyword
from PyQt5.QtGui import QBrush, QColor, QFont, QSyntaxHighlighter, QTextCharFormat

def format(colorName: str, style: str = '') -> QTextCharFormat:
    '''Return a QTextCharFormat with the given attributes.'''
    charFormat = QTextCharFormat()
    charFormat.setForeground(QBrush(QColor(colorName)))
    if 'bold' in style:
        charFormat.setFontWeight(QFont.Bold)
    if 'italic' in style:
        charFormat.setFontItalic(True)
    return charFormat

# Styles for various parts of the language, each consisting of a light-themed format and a
# dark-themed format:
STYLES = {
    # A comment may contain todo items.
    'comment': (format('green', 'italic'), format('seaGreen', 'italic')),
    'todo': (format('red', 'italic'), format('darkkhaki', 'italic')),

    # A string may contain escape sequences; a formatted string may contain formatted replacements.
    'string': (format('darkRed'), format('sienna')),
    'rawString': (format('firebrick'), format('brown')),
    'escapeSequence': (format('chocolate'), format('chocolate')),
    'formattedReplacement': (format('steelBlue'), format('steelBlue')),

    # A definition contains an identifier.
    'definition': (format('blue'), format('steelBlue')),
    'identifier': (format('black', 'bold'), format('white', 'bold')),

    # Additional parts of the language:
    'brace': (format('darkSlateGray'), format('gray')),
    'decorator': (format('steelBlue'), format('cadetBlue')),
    'keyword': (format('blue'), format('steelBlue')),
    'operator': (format('indigo'), format('aliceBlue')),
    'number': (format('darkGreen'), format('darkSeaGreen')),
    'self': (format('purple', 'italic'), format('mediumOrchid', 'italic')),
}

class Theme(Enum):
    LIGHT = 0
    DARK = 1

class PythonSyntaxHighlighter(QSyntaxHighlighter):
    '''A syntax highlighter for the Python language.'''

    # Python operators:
    _operators = [
        '=',
        # Comparison
        '==', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        '+', '-', '*', '/', '//', '%', '**',
        # In-place
        '+=', '-=', '*=', '/=', '%=',
        # Bitwise
        '^', '|', '&', '~', '>>', '<<',
    ]

    # Python braces:
    _braces = [
        '{', '}', '(', ')', '[', ']',
    ]

    # Characters that may be escaped within string literals:
    _escapedCharacters = [
        '\\', "'", '"', 'a', 'b', 'f', 'n', 'r', 't', 'v',
    ]

    def __init__(self, document):
        '''Initializes a PythonSyntaxHighlighter instance.'''
        super().__init__(document)

        self._theme = Theme.DARK

        # Create a pattern that matches a comment (from '#' until the end of the line), and a
        # subpattern for common labels used within comments.
        comment = self._makeNamedGroup('comment', rf'#.*')
        todoLabels = ['TODO', 'BUG', 'FIXME', 'HACK', 'NOTE', 'XXX']
        todo = self._makeNamedAlternatives('todo', [rf'\b{label}\b' for label in todoLabels])

        # Create patterns that match escape sequences within strings.
        escapePatterns = [r'\\' + re.escape(char)
            for char in PythonSyntaxHighlighter._escapedCharacters]
        escapePatterns += [
            r'\\N\{[^}]+\}',
            r'\\[0-7]{1,3}',
            r'\\u[0-9A-Fa-f]{4}',
            r'\\U[0-9A-Fa-f]{8}',
        ]
        escapeSequence = self._makeNamedAlternatives('escapeSequence', escapePatterns)

        # Create a pattern for formatted replacements within strings.
        # NOTE: This pattern isn't strictly correct; it should match balanced pairs of curly braces.
        formattedReplacementPattern = self._makeNamedGroup('formattedReplacement', r'\{.*?\}')
        formattedReplacement = r'\{\{|\}\}|' + formattedReplacementPattern

        # Create patterns for string (and bytes) literals, possibly containing escape sequences.
        # Bytes literals are prefixed by 'b', formatted string or bytes literals by 'f', and
        # backward-compatible Unicode string literals by 'u' (lower- or uppercase).
        stringOrBytesPrefix = self._makeNamedGroup('stringOrBytesPrefix', r'[BbFfUu]?')
        stringStart = self._makeNamedAlternatives('stringStart', ["'''", '"""', "'", '"'])
        stringEnd = self._makeNamedAlternatives('stringEnd', [r'(?P=stringStart)', r'\\?$'])
        stringPattern = rf'{stringOrBytesPrefix}{stringStart}[^\\]*?(?:\\.[^\\]*?)*?{stringEnd}'
        string = self._makeNamedGroup('string', stringPattern)

        # Create patterns for raw string (and bytes) literals, with no escape sequences.
        # Raw bytes literals are prefixed by 'rb', raw string literals by 'r', and raw formatted
        # string literals by 'rf' (lower- or uppercase, any order).
        rawStringOrBytesPrefix = self._makeNamedGroup('rawStringOrBytesPrefix', r'[Rr][BbFf]?|[BbFf][Rr]')
        rawStringStart = self._makeNamedAlternatives('rawStringStart', ["'''", '"""', "'", '"'])
        rawStringEnd = self._makeNamedAlternatives('rawStringEnd', [r'(?P=rawStringStart)', r'\\?$'])
        rawStringPattern = rf'{rawStringOrBytesPrefix}{rawStringStart}[^\\]*?(?:\\.[^\\]*?)*?{rawStringEnd}'
        rawString = self._makeNamedGroup('rawString', rawStringPattern)

        # Create patterns that match numbers.
        # NOTE: Match floats before decimal numbers, otherwise "7.e-3" only matches partially.
        digitPart = r'(?:[0-9](?:_?[0-9])*)'
        fraction = rf'(?:\.{digitPart})'
        exponent = rf'(?:[eE][+-]?{digitPart})'
        digitsWithFraction = rf'(?:(?:\b{digitPart})?{fraction})'
        digitsWithDot = rf'(?:\b{digitPart}\.)'
        pointFloat = rf'(?:{digitsWithFraction}|{digitsWithDot})'
        exponentFloat = rf'(?:{digitPart}|{pointFloat}){exponent}'
        floatNumber = rf'(?:{exponentFloat}|{pointFloat})'
        floatOrImaginaryNumber = rf'{floatNumber}(?:[jJ]\b)?'
        binaryNumber = r'\b0[bB](?:_?[01])+\b'
        octalNumber = r'\b0[oO](?:_?[0-7])+\b'
        decimalNumber = r'\b[1-9](?:_?[0-9])*\b|\b0+(?:_?0)*\b'
        hexadecimalNumber = r'\b0[xX](?:_?[0-9A-Fa-f])+\b'
        number = self._makeNamedAlternatives('number',
            [floatOrImaginaryNumber, binaryNumber, octalNumber, decimalNumber, hexadecimalNumber])

        # Create a pattern that matches a class or function definition.
        identifier = self._makeNamedGroup('identifier', r'\w+')
        definition = self._makeNamedGroup('definition', rf'\b(?:class|def)\b\s*{identifier}')

        # Create patterns that match keywords, operators, and braces.
        keywords = self._makeNamedAlternatives('keyword',
            [rf'\b{word}\b' for word in keyword.kwlist])
        operators = self._makeNamedAlternatives('operator',
            [re.escape(op) for op in PythonSyntaxHighlighter._operators])
        braces = self._makeNamedAlternatives('brace',
            [re.escape(brace) for brace in PythonSyntaxHighlighter._braces])

        # Create a pattern that matches a decorator ('@' followed by an identifier).
        decorator = self._makeNamedGroup('decorator', r'@[\w.]+\b')

        # Create a pattern for 'self' and 'cls' variables (not keywords, but common conventions).
        selfOrCls = self._makeNamedAlternatives('self', [r'\bself\b', r'\bcls\b'])

        # Combine all the top-level patterns into one regular expression.
        code = self._makeNamedAlternatives('code', [comment, string, rawString, number, definition,
            keywords, operators, braces, decorator, selfOrCls])
        self._code = re.compile(code)

        # Create regular expressions for sub-patterns that appear only in particular contexts.
        self._subpatterns = {
            'comment': [(re.compile(todo), 'todo')],
            'definition': [(re.compile(definition), 'identifier')],
            'string': [(re.compile(escapeSequence), 'escapeSequence')],
        }
        self._formattedReplacementSubpattern = re.compile(formattedReplacement)

    @property
    def theme(self) -> Theme:
        return self._theme

    @theme.setter
    def theme(self, value: Theme) -> None:
        self._theme = value
        self.rehighlight()

    def _makeNamedGroup(self, name: str, pattern: str) -> str:
        '''Returns a regular expression string for a named group matching the given pattern.'''
        return f'(?P<{name}>{pattern})'

    def _makeNamedAlternatives(self, name: str, alternatives: list) -> str:
        '''Returns a regular expression string for a named group matching any of the given
        alternative patterns.'''
        joinedAlternatives = '|'.join(alternatives)
        return self._makeNamedGroup(name, joinedAlternatives)

    def _makeUnnamedAlternatives(self, name: str, alternatives: list) -> str:
        '''Returns a regular expression string matching any of the given alternative patterns.'''
        joinedAlternatives = '|'.join(alternatives)
        return f'(?:{joinedAlternatives})'

    def highlightBlock(self, text: str) -> None:
        '''Applies syntax highlighting to the given block of text.'''

        # If the previous block state indicates that we're starting in the middle of an unclosed
        # string, prepend the appropriate quote to the current text line. Keep track of the
        # offset required when formatting text.
        state = self.previousBlockState()
        initialQuote = self._getInitialQuoteFromBlockState(state)
        text = initialQuote + text
        offset = len(initialQuote)

        # Iterate over matches on the current line of text.
        self.setCurrentBlockState(-1)
        for match in self._code.finditer(text):
            # See which role is played by the current match.
            for role in STYLES.keys():
                try:
                    start, end = match.span(role)
                    if start >= 0 and end > start:
                        # We found a role for the current match. Apply the corresponding style.
                        clampedStart = max(0, start - offset)
                        clampedEnd = max(0, end - offset)
                        textFormat = STYLES[role][self.theme.value]
                        self.setFormat(clampedStart, clampedEnd - clampedStart, textFormat)

                        # Now highlight any subpatterns within the span covered by this role.
                        self._highlightSubpatterns(text, start, end, offset, role)

                        # For formatted strings, also highlight the subpattern for
                        # formatted replacements.
                        if ((role == 'string' or role == 'rawString') and
                            'f' in match.group(role + 'OrBytesPrefix').lower()):
                            self._highlightSubpattern(text, start, end, offset,
                                self._formattedReplacementSubpattern, 'formattedReplacement')

                        # Check to see whether the current line ends with an unclosed string.
                        if ((role == 'string' or role == 'rawString') and end == len(text) and
                            match.group(role + 'End') != match.group(role + 'Start')):
                            # If so, set the block state so we'll remember for the next line.
                            state = self._getBlockStateFromStringMatch(role, match)
                            self.setCurrentBlockState(state)
                        break
                except:
                    pass

    def _getBlockStateFromStringMatch(self, role: str, match: re.Match) -> int:
        '''Encodes information about an unclosed string (whether it starts with one or three quotes,
        whether they are single- or double-quotes, whether the prefix specifies a raw string, a 
        formatted string, or a bytes literal) in an integer.'''
        quote = match.group(role + 'Start')
        isDoubleQuote = quote.startswith('"')
        isLongString = len(quote) == 3
        prefix = match.group(role + 'OrBytesPrefix').lower()
        isBytes = 'b' in prefix
        isFormatted = 'f' in prefix
        isRaw = 'r' in prefix
        return ((1 if isDoubleQuote else 0) | (2 if isLongString else 0) | (4 if isBytes else 0) |
            (8 if isFormatted else 0) | (16 if isRaw else 0))

    def _getInitialQuoteFromBlockState(self, state: int) -> str:
        '''Decodes information about an unclosed string (whether it starts with one or three quotes,
        whether they are single- or double-quotes, whether the prefix specifies a raw string, a 
        formatted string, or a bytes literal), returning the appropriate initial quote.'''
        if state < 0:
            return ''
        quote = '"' if (state & 1) else "'"
        quote = quote * (3 if (state & 2) else 1)
        quote = ('b' if (state & 4) else '') + quote
        quote = ('f' if (state & 8) else '') + quote
        quote = ('r' if (state & 16) else '') + quote
        quote += ' '
        return quote

    def _highlightSubpatterns(self, text: str, start: int, end: int, offset: int, role: str) -> None:
        if role in self._subpatterns:
            for subpattern, subrole in self._subpatterns[role]:
                self._highlightSubpattern(text, start, end, offset, subpattern, subrole)

    def _highlightSubpattern(self, text: str, start: int, end: int, offset: int,
        subpattern: re.Pattern, subrole: str) -> None:
        for match in subpattern.finditer(text, start, end):
            substart, subend = match.span(subrole)
            if substart >= 0 and subend > substart:
                clampedStart = max(0, substart - offset)
                clampedEnd = max(0, subend - offset)
                textFormat = STYLES[subrole][self.theme.value]
                self.setFormat(clampedStart, clampedEnd - clampedStart, textFormat)
