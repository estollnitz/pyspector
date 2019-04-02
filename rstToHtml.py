import docutils.core

def rstToHtml(s):
    '''Converts a reStructuredText documentation string to an HTML fragment.'''
    # Use a template file that discards the head and the surrounding body and html tags.
    # Specify an unencoded unicode string as output.
    settings = {
        'template': 'rstToHtmlTemplate.txt',
        'output_encoding': 'unicode'
    }
    return docutils.core.publish_string(s, writer_name = 'html', settings_overrides = settings)
