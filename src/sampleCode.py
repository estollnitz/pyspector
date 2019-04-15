'''
Sample code to test PythonSyntaxHighlighter.
'''

# Comments:
# - Words like TODO, BUG, FIXME, HACK, NOTE, and XXX are highlighted.
# - Escapes like \n and \t are not.

# Integers:
i = 0_000_000 + 0o_000 + 0o123 + 0x1_2abc_CAFE + 0b_1011_0110 + 1_2_3_4_5

# Floats:
f = [3.14, 10., .001, 1e100, 3.14e-10, 0e0, 3.14_15_93, 7.e-3, .99e+12, 12_345.678_910]

# Imaginary:
im = 2.3e-1j + 9_876e+2J + .5j

# Strings:
s1 = 'string'
s2 = "s"
s3 = 'nested "quote"'
s4 = 'nested """ triple quote'
s5 = "the ''' other way"
s6 = 'quote\'s escaped'
s7 = "isn't \"this\""" nice?"
s8 = 'This \n is \a a \b test \r of \u301a escape \
    \N{GRINNING FACE} sequences \U0001F600.'
s9 = "string with # hash character" # comment starts here
s10 = "string with \# bad escape character" # comment starts here

# Raw strings:
sr1 = r'raw\string\nwith\aescapes'
sr2 = r'multiline \
    raw string'
sr3 = r'escaped \' quote in raw string'

# Formatted strings:
sf1 = f'formatted {s1}'
sf2 = f'formatted {s1}{{in brackets}}{s2}{s3}'
# BUG: Nested brackets aren't handled properly in formatted replacements.
sf3 = F'formatted {s1:{s2}} nested' 

# Raw formatted strings:
srf1 = rf'raw formatted {s1}\n'
srf2 = FR"raw formatted '{s3}'"
srf3 = rF"raw {{formatted}} '{s3}'"

# Triple-quoted strings:
sl1 = '''Here's a test''' + """of long strings + ''' + with \n escapes and "fun" quotes"""
sl2 = '''What about '' this? \'''' # oh fun! '
sl3 = r"""Here's stuff ''' \n
    in 'quotes' on multiple lines # with fake comments.
    """
sl4 = '''More 'n' more
    stuff on multiple lines # with fake comments.
    '''

# Bytes:
b1 = b'bytes\n'
b2 = B"more\tbytes"
br1 = rb'raw bytes\n'
br2 = rB'raw bytes\n'
br3 = bR'raw bytes\n'
br4 = BR'raw \
    bytes\n'

# Functions:
def hello(a: str, b: int, c: float) -> str:
    '''
    A simple test function.
    '''
    return a + str(b) + str(c)

# Classes:
class SampleBaseClass:
    '''
    Silly base class.
    '''

    def foo(self):
        print('hello')

    def bar(self):
        return 4

    @property
    def fizz(self):
        return self._baz

    @fizz.setter
    def fizz(self, value):
        self._baz = value

    @staticmethod
    def buzz():
        return 42

    @classmethod
    def fizzbuzz(cls, a, b):
        return cls.__name__ + a + b

class SampleDerivedClass(SampleBaseClass):
    """Derived class."""

    def bar(self):
        print('whatever')

    class NestedClass:
        '''Nested class.'''

        def __init__(self, baz):
            self._baz = baz

        def baz(self):
            return self._baz
