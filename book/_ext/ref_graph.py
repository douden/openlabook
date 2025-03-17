from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from docutils.parsers.rst import directives
from docutils import nodes
from sphinx_design.shared import SEMANTIC_COLORS
from docutils.nodes import reference
import os

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
            self.content = content
            value = self.parse_content_to_nodes()
        else:
            value = []

        tags_node = tags()
        tags_node['group'] = self.arguments[0]
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
    app.add_config_value("ref_graph_default_ref_file","references.txt",'env')
    app.add_config_value("ref_graph_default_group_file","groups.txt",'env')

    app.setup_extension("sphinx_design")

    app.add_directive("tags", TagsDirective)

    app.add_node(tags,
                 html=(visit_tags_node, depart_tags_node),
                 latex=(visit_tags_node, depart_tags_node),
                 text=(visit_tags_node, depart_tags_node))
    
    app.connect('env-purge-doc', purge_tags)
    app.connect('doctree-resolved', process_tags_nodes)

    return {'parallel_write_safe': False}

def purge_tags(app, env, docname):
    if not hasattr(env, 'ref_graph_all_tags'):
        return
    env.ref_graph_all_tags = [tags for tags in env.ref_graph_all_tags if tags['docname'] != docname]

def process_tags_nodes(app, doctree, fromdocname):
    # Add here the collection of all tags and create the information for the graph 
    print('!!!!!!!!!!!!!!!!!!!!!!!!!!')
    print('!!! START PROCESS TAGS !!!')
    print('!!!!!!!!!!!!!!!!!!!!!!!!!!')
    all_refs = []
    unique_refs = set()
    all_groups = []
    unique_groups = set()

    for node in doctree.traverse(tags):
        for child in node.children:
            # Should be a paragraph
            for grandchild in child.children:
                if isinstance(grandchild,reference):
                    display_text = grandchild.children[0].rawsource.strip()
                    target = grandchild.attributes['refuri'].strip()
                    # change target to origin md file
                    html = target.find(".html")
                    target = target[:html]+".md"
                    ref = (display_text,target)
                    # prevent double references
                    if ref not in unique_refs:
                        unique_refs.add(ref)
                        all_refs.append((f"{fromdocname}.md",*ref))
        group = node.attributes['group']
        group_entry = (f"{fromdocname}.md",group.strip())
        if group_entry not in unique_groups:
            unique_groups.add(group_entry)
            all_groups.append(group_entry)

    if len(all_refs)>0:
        staticdir = os.path.join(app.builder.outdir, '_static')
        filename = os.path.join(staticdir,app.config.ref_graph_default_ref_file)
        with open(filename,"a", encoding="utf-8") as out:
            for md_file, text, target in all_refs:
                out.write(f"{md_file} -> [text: '{text}'] [target: '{target}']\n")
    
    if len(all_groups)>0:
        print(all_groups)
        staticdir = os.path.join(app.builder.outdir, '_static')
        filename = os.path.join(staticdir,app.config.ref_graph_default_group_file)
        with open(filename,"a", encoding="utf-8") as out:
            for md_file, tag in all_groups:
                out.write(f"{md_file} -> [tag: '{tag}']\n")
    
    print('!!!!!!!!!!!!!!!!!!!!!!!!!!')
    print('!!!! END PROCESS TAGS !!!!')
    print('!!!!!!!!!!!!!!!!!!!!!!!!!!')

    pass