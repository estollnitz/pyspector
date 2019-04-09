'''
Color syntax highlighting for the Python language.

This is a test of escapes.\nDid highlighting work \u301a? # fake comment here

Loosely based on https://wiki.python.org/moin/PyQt/Python%20syntax%20highlighting.
'''

# External imports:
import re
import sys
import keyword
from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QBrush, QColor, QTextCharFormat, QFont, QSyntaxHighlighter

# TODO: Fix highlighting of the following line so that the first hash character is not
# treated as the start of a comment.
TODO_FIX_COMMENT_HIGHLIGHTING = 'def foo(bar): return "baz" # comment within string' # \n comment
# Also, don't color strings like 'this' and "that" and escape sequences like \n and \r within comments.

def format(colorName: str, style: str = '') -> QTextCharFormat:
    '''Return a QTextCharFormat with the given attributes.'''
    charFormat = QTextCharFormat()
    charFormat.setForeground(QBrush(QColor(colorName)))
    if 'bold' in style:
        charFormat.setFontWeight(QFont.Bold)
    if 'italic' in style:
        charFormat.setFontItalic(True)
    return charFormat

# Styles for various parts of the language:
STYLES = {
    'keyword': format('blue'),
    'operator': format('indigo'),
    'brace': format('black'),
    'definition': format('black', 'bold'),
    'string': format('darkRed'),
    'multilineString': format('darkRed'),
    'comment': format('green', 'italic'),
    'self': format('purple', 'italic'),
    'number': format('darkGreen'),
    'escapeSequence': format('chocolate'),
    'decorator': format('steelBlue'),
}

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

        # String literals can be prefixed by 'r' (for raw) or 'f' (for formatted).
        # Byte literals must be prefixed by 'b' (for bytes) and optionally by 'r' (for raw).
        stringPrefixes = 'r|u|R|U|f|F|fr|Fr|fR|FR|rf|rF|Rf|RF'
        bytePrefixes = 'b|B|br|Br|bR|BR|rb|rB|Rb|RB'
        stringOrBytePrefixes = f'({stringPrefixes}|{bytePrefixes})?'

        # Multiline strings begin and end with three single- or double-quotes.
        # The comments that end the following two lines help our highlighter work on this file.
        self._threeSingleQuotes = (QRegExp("'''"), 1, 'multilineString') # '''
        self._threeDoubleQuotes = (QRegExp('"""'), 2, 'multilineString') # """

        rules = []

        # Add keyword, operator, and brace rules.
        rules += [(rf'\b{word}\b', 0, 'keyword')
            for word in keyword.kwlist]
        rules += [(re.escape(operator), 0, 'operator')
            for operator in PythonSyntaxHighlighter._operators]
        rules += [(re.escape(brace), 0, 'brace')
            for brace in PythonSyntaxHighlighter._braces]

        # Add other rules.
        rules += [
            # Numeric literals:
            (r'\b[1-9][0-9_]*\b', 0, 'number'),        # decimal
            (r'\b0[bB][0-1_]+\b', 0, 'number'),        # binary
            (r'\b0[oO][0-7_]+\b', 0, 'number'),        # octal
            (r'\b0[xX][0-9A-Fa-f_]+\b', 0, 'number'),  # hexadecimal
            (r'\b[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, 'number'),

            # Decorator ('@' followed by an identifier):
            (r'@[\w.]+\b', 0, 'decorator'),

            # Class or function definition ('class' or 'def' followed by an identifier):
            (r'\b(class|def)\b\s*(\w+)', 2, 'definition'),

            # The 'self' variable (not a keyword, but a common convention):
            (r'\bself\b', 0, 'self'),

            # Double-quoted string, possibly containing escape sequences:
            (stringOrBytePrefixes + r'"[^"\\]*(\\.[^"\\]*)*"', 0, 'string'),

            # Single-quoted string, possibly containing escape sequences:
            (stringOrBytePrefixes + r"'[^'\\]*(\\.[^'\\]*)*'", 0, 'string'),

            # Comment (from '#' until the end of the line):
            (r'#[^\n]*', 0, 'comment'),
        ]

        # Store a regular expression in the rule for each pattern.
        self._rules = [(QRegExp(pattern), index, style)
            for (pattern, index, style) in rules]

        # Create separate rules for escape sequences.
        escapeRules = [(r'\\' + re.escape(char), 0, 'escapeSequence')
            for char in PythonSyntaxHighlighter._escapedCharacters]
        escapeRules += [
            (r'\\N\{[^}]+\}', 0, 'escapeSequence'),
            (r'\\[0-7]{1,3}', 0, 'escapeSequence'),
            (r'\\u[0-9A-Fa-f]{4}', 0, 'escapeSequence'),
            (r'\\U[0-9A-Fa-f]{8}', 0, 'escapeSequence'),
        ]
        self._escapeRules = [(QRegExp(pattern), index, style)
            for (pattern, index, style) in escapeRules]

    def highlightBlock(self, text: str) -> None:
        '''Applies syntax highlighting to the given block of text.'''

        # Apply each of our syntax highlighting rules to the text.
        self._applyRules(text, self._rules)

        # Check for multiline strings.
        self.setCurrentBlockState(0)
        inMultilineQuote = self._matchMultiline(text, *self._threeSingleQuotes)
        if not inMultilineQuote:
            inMultilineQuote = self._matchMultiline(text, *self._threeDoubleQuotes)

        # Apply our separate rules for escape sequences.
        self._applyRules(text, self._escapeRules)

    def _applyRules(self, text: str, rules: list):
        '''Applies regular-expression-based syntax highlighting rules.'''
        for expression, nth, style in rules:
            index = expression.indexIn(text, 0)
            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, STYLES[style])
                index = expression.indexIn(text, index + length)

    def _matchMultiline(self, text: str, delimiter: QRegExp, inState: int, style: str) -> bool:
        '''Highlights multiline strings.
        
        `delimiter` is a `QRegExp` for three single- or double-quotes, and `inState` is a unique
        integer representing the corresponding state changes when inside those strings. Returns
        `True` if we're still inside a multiline string when this function finishes.
        '''
        # If we're already inside a triple-quoted string, start at position 0.
        if self.previousBlockState() == inState:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line.
        else:
            start = delimiter.indexIn(text)
            # Move past this match.
            add = delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter.
            # It the ending delimiter on this line?
            end = delimiter.indexIn(text, start + add)
            if end >= add:
                # Yes. Turn off the block state.
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            else:
                # No. We're inside a multiline string, so set the block state.
                self.setCurrentBlockState(inState)
                length = len(text) - start + add

            # Apply formatting to `length` characters beginning at index `start`.
            self.setFormat(start, length, STYLES[style])

            # Look for the next match.
            start = delimiter.indexIn(text, start + length)

        # Return True if we're still inside a multiline string.
        return self.currentBlockState() == inState