from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from docutils.parsers.rst import directives
from docutils import nodes


class TagsDirective(SphinxDirective):
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        "hidden": directives.unchanged,
        "badge": directives.unchanged
    }

    def run(self) -> list[nodes.Node]:

        assert self.arguments[0] is not None
        assert self.has_content is True

        hidden = self.options.get('hidden')
        if hidden is None or hidden=='True' or hidden=='Yes':
            hidden = True
        else:
            hidden = False
        
        badge = self.options.get('badge')
        if badge is None:
            badge = 'bdg-link-primary'
        else:
            badge = 'bdg-link-'+badge
        
        content = self.content
        paragraphs = []
        if not hidden:
            for line in content:
                paragraphs.append(nodes.paragraph(rawsource=f'{{{badge}}}`{line}`'))
        return paragraphs
        

def setup(app: Sphinx):

    app.add_directive("tags", TagsDirective)

    return