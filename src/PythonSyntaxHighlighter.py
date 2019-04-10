'''
Color syntax highlighting for the Python language.

Loosely based on https://wiki.python.org/moin/PyQt/Python%20syntax%20highlighting.
'''

# External imports:
import re
import sys
import keyword
from PyQt5.QtCore import QRegularExpression, QRegularExpressionMatch, QRegularExpressionMatchIterator
from PyQt5.QtGui import QBrush, QColor, QTextCharFormat, QFont, QSyntaxHighlighter

# TODO: Fix highlighting of the following line so that the first hash character is not
# treated as the start of a comment.
'Bug: color should not change after # within a string' # but should change in comment.

# TODO: don't color escape sequences like \n and \r within comments.

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
    'brace': format('black'),
    'comment': format('green', 'italic'),
    'decorator': format('steelBlue'),
    'definition': format('black', 'bold'),
    'escapeSequence': format('chocolate'),
    'keyword': format('blue'),
    'operator': format('indigo'),
    'string': format('darkRed'),
    'multilineString': format('darkRed'),
    'number': format('darkGreen'),
    'self': format('purple', 'italic'),
    'todo': format('red', 'italic'),
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
        stringOrBytePrefixes = f'(?:{stringPrefixes}|{bytePrefixes})?'

        # Multiline strings begin and end with three single- or double-quotes.
        singleQuote = "'"
        doubleQuote = '"'
        threeSingleQuotes = singleQuote * 3
        threeDoubleQuotes = doubleQuote * 3
        threeQuotes = f'(?:({threeSingleQuotes})|({threeDoubleQuotes}))'
        self._threeSingleQuotes = QRegularExpression(threeSingleQuotes)
        self._threeDoubleQuotes = QRegularExpression(threeDoubleQuotes)
        self._multilineStringStart = QRegularExpression(f'{stringOrBytePrefixes}{threeQuotes}')

        # Add keyword, operator, and brace rules.
        rules = [(rf'\b{word}\b', 0, 'keyword')
            for word in keyword.kwlist]
        rules += [(re.escape(operator), 0, 'operator')
            for operator in PythonSyntaxHighlighter._operators]
        rules += [(re.escape(brace), 0, 'brace')
            for brace in PythonSyntaxHighlighter._braces]

        # Set up parts of a floating point number. Because it may start or end with a decimal
        # point, a float doesn't necessarily start or end at a '\b' boundary.
        digitPart = '(?:[0-9][0-9_]*)'
        fraction = rf'(?:\.{digitPart})'
        exponent = f'(?:[eE][+-]?{digitPart})'
        digitsWithFraction = f'(?:{digitPart}?{fraction})'
        digitsWithDot = rf'(?:{digitPart}\.)'
        pointFloat = f'(?:{digitsWithFraction}|{digitsWithDot})'
        exponentFloat = f'(?:{digitPart}|{pointFloat}){exponent}'
        floatNumber = f'(?:{exponentFloat}|{pointFloat})'

        # Add other rules.
        rules += [
            # Numeric literals:
            (r'\b0[bB][0-1_]+\b', 0, 'number'),        # binary
            (r'\b0[oO][0-7_]+\b', 0, 'number'),        # octal
            (r'\b[1-9][0-9_]*\b', 0, 'number'),        # decimal
            (r'\b0[xX][0-9A-Fa-f_]+\b', 0, 'number'),  # hexadecimal
            (floatNumber, 0, 'number'),                # float
            (rf'{floatNumber}[jJ]\b', 0, 'number'),    # imaginary

            # Decorator ('@' followed by an identifier):
            (r'@[\w.]+\b', 0, 'decorator'),

            # Class or function definition ('class' or 'def' followed by an identifier):
            (r'\b(class|def)\b\s*(\w+)', 2, 'definition'),

            # The 'self' or 'cls' variable (not a keyword, but a common convention):
            (r'\b(self|cls)\b', 0, 'self'),

            # Double-quoted string, possibly containing escape sequences:
            (stringOrBytePrefixes + r'"[^"\\]*(\\.[^"\\]*)*"', 0, 'string'),

            # Single-quoted string, possibly containing escape sequences:
            (stringOrBytePrefixes + r"'[^'\\]*(\\.[^'\\]*)*'", 0, 'string'),

            # Comment (from '#' until the end of the line):
            (r'#[^\n]*', 0, 'comment'),

            # Common labels used at the start of a comment:
            (r'#[ \t]*(TODO|BUG|FIXME|HACK|NOTE|XXX)', 1, 'todo'),
        ]

        # Store a regular expression in the rule for each pattern.
        self._rules = [(QRegularExpression(pattern), index, style)
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
        self._escapeRules = [(QRegularExpression(pattern), index, style)
            for (pattern, index, style) in escapeRules]

    def highlightBlock(self, text: str) -> None:
        '''Applies syntax highlighting to the given block of text.'''

        # Apply each of our syntax highlighting rules to the text.
        self._applyRules(text, self._rules)

        # Check for multiline strings.
        self.setCurrentBlockState(0)
        self._highlightMultilineStrings(text)

        # Apply our separate rules for escape sequences.
        self._applyRules(text, self._escapeRules)

    def _applyRules(self, text: str, rules: list):
        '''Applies regular-expression-based syntax highlighting rules.'''
        for expression, nth, style in rules:
            matchIterator = expression.globalMatch(text)
            while matchIterator.hasNext():
                match = matchIterator.next()
                start = match.capturedStart(nth)
                length = match.capturedLength(nth)
                self.setFormat(start, length, STYLES[style])

    def _highlightMultilineStrings(self, text: str) -> None:
        '''Highlights multiline strings.'''
        # If we're already inside a triple-quoted string, look for the ending triple-quote.
        state = self.previousBlockState()
        if state > 0:
            start = 0
            end = 0
            regexp = self._threeSingleQuotes if state == 1 else self._threeDoubleQuotes
            match = regexp.match(text, end)
            if match.hasMatch():
                length = match.capturedEnd() - start
                self.setCurrentBlockState(0)
            else:
                length = len(text) - start
                self.setCurrentBlockState(state)
            self.setFormat(start, length, STYLES['multilineString'])
        else:
            start = 0
            length = 0

        # As long as there's a delimiter match on this line...
        match = self._multilineStringStart.match(text, start + length)
        while match.hasMatch():
            state = 1 if match.capturedLength(1) else 2
            start = match.capturedStart()
            end = match.capturedEnd()

            # Look for the ending delimiter.
            regexp = self._threeSingleQuotes if state == 1 else self._threeDoubleQuotes
            match = regexp.match(text, end)
            if match.hasMatch():
                length = match.capturedEnd() - start
                self.setCurrentBlockState(0)
            else:
                length = len(text) - start
                self.setCurrentBlockState(state)
            self.setFormat(start, length, STYLES['multilineString'])

            # Look for the next match.
            match = self._multilineStringStart.match(text, start + length)
