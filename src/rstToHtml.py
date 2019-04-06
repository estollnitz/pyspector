# External imports:
import docutils.core
import docutils.nodes
import docutils.parsers.rst
import docutils.utils
import re
from os.path import dirname

def customRoleHandler(name, rawText, text, lineNo, inliner, options = {}, content = []):
    '''Inserts a reference node when interpreted text with a custom role is encountered.'''
    # Use the text as the label.
    label = docutils.utils.unescape(text)

    # Use slash instead of dot as a delimiter in the link address.
    address = label.replace('.', '/')

    # When the text starts with a tilde, shorten the label to just the local name.
    if label.startswith('~'):
        label = label.split('.')[-1]
        address = address.replace('~', '')

    # Prepend our custom "item:" scheme to the link address.
    uri = f'item:{address}'

    # Create and return a new reference node.
    node = docutils.nodes.reference(rawText, label, refuri = uri, **options)
    return [node], []

# Register our custom role handler for each of the roles used in Python documentation.
# See https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html and
# https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html#python-roles
# for roles recognized by Sphinx in reStructuredText documentation for Python.
for role in ['mod', 'func', 'data', 'const', 'class', 'meth', 'attr', 'exc', 'obj', 'ref']:
    docutils.parsers.rst.roles.register_local_role(role, customRoleHandler)
    docutils.parsers.rst.roles.register_local_role('py:' + role, customRoleHandler)

class HeaderedDirective(docutils.parsers.rst.Directive):
    '''Base class for handling directives that need a custom header before their content.'''
    has_content = True
    header = ''

    def run(self):
        self.assert_has_content()
        em = docutils.nodes.emphasis()
        header = self.__class__.header
        em += docutils.nodes.Text(header, header)
        text = '\n'.join(self.content)
        em += docutils.nodes.Text(text, text)
        para = docutils.nodes.paragraph()
        para += em
        return [para]

class VersionAdded(HeaderedDirective):
    '''Handles "versionadded" directives in reStructuredText input.'''
    # For an example of the "versionadded" directive in use, see numpy.sum.
    header = 'Version added: '

class VersionChanged(HeaderedDirective):
    '''Handles "versionchanged" directives in reStructuredText input.'''
    # For an example of the "versionchanged" directive in use, see numpy.unravel_index.
    header = 'Version changed: '

class Deprecated(HeaderedDirective):
    '''Handles "deprecated" directives in reStructuredText input.'''
    # For an example of the "deprecated" directive in use, see matplotlib.RcParams.msg_depr.
    header = 'Deprecated: '

# Register custom directives.
docutils.parsers.rst.directives.register_directive('versionadded', VersionAdded)
docutils.parsers.rst.directives.register_directive('versionchanged', VersionChanged)
docutils.parsers.rst.directives.register_directive('deprecated', Deprecated)

def rstToHtml(rstText, defaultRole = 'code'):
    '''Converts a reStructuredText documentation string to an HTML fragment.'''
    # Initialize settings.
    templateFile = f'{dirname(dirname(__file__))}/templates/rstTohtml.txt'
    settings = {
        'template': templateFile,              # Use a template that discards all but the body.
        'output_encoding': 'unicode',          # Provide output as an unencoded Unicode string.
        'report_level': 3,                     # Ignore info (1) and warning (2) messages.
        'halt_level': 3,                       # Stop for error (3) or severe (4) messages.
        'traceback': True,                     # Raise an exception if an error occurs.
    }

    # Set the default role to use when role is not specified before interpreted text.
    # Note that matplotlib.cycler presumes default role is 'obj', while most other files presume
    # default role is 'code'.
    modifiedRstText = f'.. default-role:: {defaultRole}\n{rstText}'

    # Convert from reStructuredText to HTML.
    html = docutils.core.publish_string(modifiedRstText, writer_name = 'html', settings_overrides = settings)

    # Permit unpaired asterisk delimiters that docutils finds problematic.
    asteriskRegEx = '<a href=".*"><span class="problematic" id=".*">\\*</span></a>'
    return re.sub(asteriskRegEx, '*', html)
