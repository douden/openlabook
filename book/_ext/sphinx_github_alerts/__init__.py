def convert_github_alerts(app, docname, source):
    """Replace GitHub alerts with Sphinx admonitions."""

    # Find any line starting with '> ![type] and replace it
    # with the appropriate admonition syntax for Sphinx.'
    # type can be 
    return

def setup(app):
     app.connect('source-read', convert_github_alerts)
    
    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }