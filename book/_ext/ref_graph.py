from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from docutils.parsers.rst import directives
from docutils import nodes
from docutils.parsers.rst import Parser
from docutils.frontend import OptionParser
from docutils.utils import new_document
from docutils.nodes import NodeVisitor

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
            badge = 'primary'
        
        if not hidden:
            content = self.content
            for i,line in enumerate(content):
                content[i] = f"{{bdg-ref-{badge}}}`{line}`"
            self.content = content
            value = self.parse_content_to_nodes()
        else:
            value = []

        return value
        

def setup(app: Sphinx):

    app.setup_extension("sphinx_design")

    app.add_directive("tags", TagsDirective)

    return