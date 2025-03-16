from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from docutils.parsers.rst import directives
from docutils import nodes
from sphinx_design.shared import SEMANTIC_COLORS

class TagsDirective(SphinxDirective):
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        "hidden": directives.unchanged,
        "color": directives.unchanged,
        "style": directives.unchanged
    }

    def run(self) -> list[nodes.Node]:

        assert self.arguments[0] is not None
        assert self.has_content is True

        hidden = self.options.get('hidden')
        if hidden=='True':
            hidden = True
        else:
            hidden = self.env.config.ref_graph_default_hidden

        assert hidden in [True,False]
        
        color = self.options.get('color')
        if color is None:
            color = self.env.config.ref_graph_default_color

        assert color in SEMANTIC_COLORS

        style = self.options.get('style')
        if style is None:
            style = self.env.config.ref_graph_default_style
        
        assert style in [None,'line']

        if not hidden:
            content = self.content
            for i,line in enumerate(content):
                if line != '':
                    if style is None:
                        content[i] = f"{{bdg-ref-{color}}}`{line}`"
                    else:
                        content[i] = f"{{bdg-ref-{color}-{style}}}`{line}`"
                    if i==0:
                        content[i] = "**Tags:** "+content[i]
            self.content = content
            value = self.parse_content_to_nodes()
        else:
            value = []

        tags_node = tags()
        tags_node.children = value

        # Add the node to all tags available
        env = self.state.document.settings.env
        if not hasattr(env, 'ref_graph_all_tags'):
            env.ref_graph_all_tags = []
        env.ref_graph_all_tags.append({
            'docname': env.docname,
            'tags': tags_node.deepcopy()
        })
        
        return [tags_node]
    
class tags(nodes.Admonition, nodes.Element):
    pass

def visit_tags_node(self, node):
    pass

def depart_tags_node(self, node):
    pass

def setup(app: Sphinx):

    app.add_config_value('ref_graph_default_hidden',True,'env')
    app.add_config_value('ref_graph_default_color','primary','env')
    app.add_config_value("ref_graph_default_style",None,'env')
    app.setup_extension("sphinx_design")

    app.add_directive("tags", TagsDirective)

    app.add_node(tags,
                 html=(visit_tags_node, depart_tags_node),
                 latex=(visit_tags_node, depart_tags_node),
                 text=(visit_tags_node, depart_tags_node))
    
    app.connect('env-purge-doc', purge_tags)
    app.connect('doctree-resolved', process_tags_nodes)

    return

def purge_tags(app, env, docname):
    if not hasattr(env, 'ref_graph_all_tags'):
        return
    env.ref_graph_all_tags = [tags for tags in env.ref_graph_all_tags if tags['docname'] != docname]

def process_tags_nodes(app, doctree, fromdocname):
    # Add here the collection of all tags and create the information for the graph 
    pass