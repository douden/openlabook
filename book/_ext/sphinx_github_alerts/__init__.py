import re

RECOGNISED_TYPES = {
    'note': 'note',
    'tip': 'tip',
    'important': 'important',
    'warning': 'warning',
    'caution': 'caution',
}

def convert_github_alerts(app, docname, source):
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("Starting converting GitHub alerts in:", docname)
    
    """Replace GitHub alerts with Sphinx admonitions."""

    # Find any block starting with '> [!type] and replace it
    # with the appropriate admonition syntax for Sphinx.'
    # type can only be one of 'note', 'tip', 'important', 'warning', 'caution', etc.
    # Capitalization does not matter.

    # Find each block within the source
    content = source[0]
    
    # Pattern to find consecutive lines starting with '>'
    pattern = r'^(?:>.*\n?)+' # Matches one or more consecutive lines starting with '>'
    
    # Find all matches
    matches = re.finditer(pattern, content, re.MULTILINE)
    
    for i,match in enumerate(matches):
        block = match.group(0)
        # Process each block here
        # print first line of block
        first_line = block.splitlines()[0]
        # extract type from first line and convert to lowercase
        type_match = re.search(r'>\s*\[!(\w+)\]', first_line)
        if type_match:
            type_match = type_match.group(1).lower()
            if type_match in RECOGNISED_TYPES:
                print(f"Type of block {i}: {type_match}")

    print("Finished converting GitHub alerts in:", docname)
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    return

def setup(app):

    app.connect('source-read', convert_github_alerts)
    
    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }