import docutils.core
import docutils.nodes
import docutils.parsers.rst
import docutils.utils

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

def rstToHtml(s):
    '''Converts a reStructuredText documentation string to an HTML fragment.'''
    settings = {
        'template': 'rstToHtmlTemplate.txt',   # Use a template that discards all but the body.
        'output_encoding': 'unicode',          # Provide output as an unencoded Unicode string.
        'report_level': 3,                     # Ignore info (1) and warning (2) messages.
        'halt_level': 3,                       # Stop for error (3) or severe (4) messages.
        'traceback': True,                     # Raise an exception if an error occurs.
    }
    return docutils.core.publish_string(s, writer_name = 'html', settings_overrides = settings)
