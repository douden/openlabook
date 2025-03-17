from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from docutils.parsers.rst import directives
from docutils import nodes
from sphinx_design.shared import SEMANTIC_COLORS
from docutils.nodes import reference
import os
import numpy as np

NAMED_COLORS = ['maroon',
'red',
'purple',
'fuchsia',
'green',
'lime',
'olive',
'yellow',
'navy',
'blue',
'teal',
'aqua',
'aliceblue',
'aqua',
'aquamarine',
'azure',
'beige',
'bisque',
'blanchedalmond',
'blue',
'blueviolet',
'brown',
'burlywood',
'cadetblue',
'chartreuse',
'chocolate',
'coral',
'cornflowerblue',
'cornsilk',
'crimson',
'cyan',
'darkblue',
'darkcyan',
'darkgoldenrod',
'darkgreen',
'darkkhaki',
'darkmagenta',
'darkolivegreen',
'darkorange',
'darkorchid',
'darkred',
'darksalmon',
'darkseagreen',
'darkslateblue',
'darkturquoise',
'darkviolet',
'deeppink',
'deepskyblue',
'dodgerblue',
'firebrick',
'forestgreen',
'fuchsia',
'gainsboro',
'gold',
'goldenrod',
'green',
'greenyellow',
'honeydew',
'hotpink',
'indianred',
'indigo',
'ivory',
'khaki',
'lavender',
'lavenderblush',
'lawngreen',
'lemonchiffon',
'lightblue',
'lightcoral',
'lightcyan',
'lightgoldenrodyellow',
'lightgreen',
'lightpink',
'lightsalmon',
'lightseagreen',
'lightskyblue',
'lightsteelblue',
'lightyellow',
'lime',
'limegreen',
'linen',
'magenta',
'maroon',
'mediumaquamarine',
'mediumblue',
'mediumorchid',
'mediumpurple',
'mediumseagreen',
'mediumslateblue',
'mediumspringgreen',
'mediumturquoise',
'mediumvioletred',
'midnightblue',
'mintcream',
'mistyrose',
'moccasin',
'navy',
'oldlace',
'olive',
'olivedrab',
'orange',
'orangered',
'orchid',
'palegoldenrod',
'palegreen',
'paleturquoise',
'palevioletred',
'papayawhip',
'peachpuff',
'peru',
'pink',
'plum',
'powderblue',
'purple',
'rebeccapurple',
'red',
'rosybrown',
'royalblue',
'saddlebrown',
'salmon',
'sandybrown',
'seagreen',
'seashell',
'sienna',
'silver',
'skyblue',
'slateblue',
'snow',
'springgreen',
'steelblue',
'tan',
'teal',
'thistle',
'tomato',
'turquoise',
'violet',
'wheat',
'yellow',
'yellowgreen'
]

class RefGraphDirective(SphinxDirective):
    has_content = False
    required_arguments = 0
    optional_arguments = 0
    option_spec = {
        "class": directives.class_option
    }

    def run(self) -> list[nodes.Node]:
        graph_node = ref_graph()
        html = f"""
			<div class="svg-container" style="width: 100%; aspect-ratio: 2 / 1; border: none; border-radius: 8px;">
					<svg id="graph"></svg>
			</div>
		"""
        svg_node = nodes.raw(None, html, format="html")
        graph_node.insert(0,svg_node)

        return [graph_node]

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
        hidden = self.options.get('hidden')
        if hidden=='True':
            hidden = True
        else:
            hidden = self.env.config.ref_graph_hidden

        assert hidden in [True,False]
        
        color = self.options.get('color')
        if color is None:
            color = self.env.config.ref_graph_color

        assert color in SEMANTIC_COLORS

        style = self.options.get('style')
        if style is None:
            style = self.env.config.ref_graph_style
        
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
    
class ref_graph(nodes.Admonition, nodes.Element):
    pass

def visit_ref_graph_node(self, node):
    pass

def depart_ref_graph_node(self, node):
    pass

class tags(nodes.Admonition, nodes.Element):
    pass

def visit_tags_node(self, node):
    pass

def depart_tags_node(self, node):
    pass

def setup(app: Sphinx):

    app.add_config_value('ref_graph_hidden',True,'env')
    app.add_config_value('ref_graph_color','primary','env')
    app.add_config_value("ref_graph_style",None,'env')
    app.add_config_value("ref_graph_ref_file","references.txt",'env')
    app.add_config_value("ref_graph_group_file","groups.txt",'env')
    app.add_config_value("ref_graph_unique_groups_file","unique_groups.txt",'env')
    app.add_config_value("ref_graph_color_map",{},'env')

    app.setup_extension("sphinx_design")
    app.setup_extension("sphinx_named_colors")

    app.add_directive("tags", TagsDirective)
    app.add_directive("refgraph", RefGraphDirective)

    app.add_node(tags,
                 html=(visit_tags_node, depart_tags_node),
                 latex=(visit_tags_node, depart_tags_node),
                 text=(visit_tags_node, depart_tags_node))
    
    app.add_node(ref_graph,
                 html=(visit_ref_graph_node, depart_ref_graph_node),
                 latex=(visit_ref_graph_node, depart_ref_graph_node),
                 text=(visit_ref_graph_node, depart_ref_graph_node))
    
    app.connect('env-purge-doc', purge_tags)
    app.connect('doctree-resolved', process_tags_nodes)

    app.connect('html-page-context',add_js_css)
    app.connect('build-finished',write_js_css)

    return {'parallel_write_safe': False}

def purge_tags(app, env, docname):
    if not hasattr(env, 'ref_graph_all_tags'):
        return
    env.ref_graph_all_tags = [tags for tags in env.ref_graph_all_tags if tags['docname'] != docname]

def process_tags_nodes(app, doctree, fromdocname):
    # Add here the collection of all tags and create the information for the graph 
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
            unique_groups.add(group)
            all_groups.append(group_entry)

    # each document should only contain one group
    
    assert len(unique_groups) <= 1, f"At most one group should be defined in {fromdocname}"

    if len(all_refs)>0:
        staticdir = os.path.join(app.builder.outdir, '_static')
        filename = os.path.join(staticdir,app.config.ref_graph_ref_file)
        with open(filename,"a", encoding="utf-8") as out:
            for md_file, text, target in all_refs:
                out.write(f"{md_file} -> [text: '{text}'] [target: '{target}']\n")
    
    if len(all_groups)>0:
        staticdir = os.path.join(app.builder.outdir, '_static')
        filename = os.path.join(staticdir,app.config.ref_graph_group_file)
        with open(filename,"a", encoding="utf-8") as out:
            for md_file, tag in all_groups:
                out.write(f"{md_file} -> [tag: '{tag}']\n")

    # update file with group names
    if len(all_groups)>0:
        staticdir = os.path.join(app.builder.outdir, '_static')
        filename = os.path.join(staticdir,app.config.ref_graph_unique_groups_file)  
        try:
            with open(filename,'r') as file:
                data = file.readlines()
        except:
            data = []
        for i,d in enumerate(data):
            data[i] = d.replace('\n','')
        data = list(set(data).union(unique_groups))
        for i,d in enumerate(data):
            data[i] = d+'\n'
        with open(filename,'w') as file:
            file.writelines(data)

    pass

def add_js_css(app, pagename, templatename, context, doctree):
    # check if a tags node is present >> change to ref_graph node
    present = False
    if doctree is not None:
        for node in doctree.traverse(ref_graph):
            present = True
            break
    
    if present:
        app.add_js_file('https://d3js.org/d3.v7.min.js')
        app.add_js_file('ref_graph.js',loading_method='defer')
        app.add_css_file('ref_graph.css')

    pass

def write_js_css(app,exc):
    
    # load and write default css content
    css_file = os.path.join(os.path.dirname(__file__), 'static', 'ref_graph.css')
    with open(css_file,'r') as css:
        css_file_content = css.read()
    if app.builder.format == 'html':
        staticdir = os.path.join(app.builder.outdir, '_static')
        outfile = os.path.join(staticdir,'ref_graph.css')
        with open(outfile,'w') as css:
            css.write(css_file_content)
    

    # load and write default js content
    js_file = os.path.join(os.path.dirname(__file__), 'static', 'ref_graph.js')
    with open(js_file,'r') as js:
        js_file_content = js.read()
    # link groups to TUD colors in a dict
    available_colors = NAMED_COLORS.copy()
    staticdir = os.path.join(app.builder.outdir, '_static')
    infile = os.path.join(staticdir,app.config.ref_graph_unique_groups_file)
    color_dict = {}
    with open(infile,'r') as groups:
        lines = groups.readlines()
    for line in lines:
        group = line.replace('\n','')
        if group in app.config.ref_graph_color_map:
            print(f'{group} found in user color map')
        else:
            print(f'{group} not found in user color map')
            rng = np.random.default_rng()
            color = rng.choice(available_colors,1)[0]
            available_colors.remove(color)
            if len(available_colors) == 0:
                available_colors = NAMED_COLORS.copy()
            color_dict[group] = str(color)
    color_dict = color_dict | app.config.ref_graph_color_map
    js_file_content = js_file_content.replace('// <groupColors>',str(color_dict).replace("{","").replace("}",""))
    js_file_content = js_file_content.replace('<references.txt>',app.config.ref_graph_ref_file)
    js_file_content = js_file_content.replace('<groups.txt>',app.config.ref_graph_group_file)
    if app.builder.format == 'html':
        staticdir = os.path.join(app.builder.outdir, '_static')
        outfile = os.path.join(staticdir,'ref_graph.js')
        with open(outfile,'w') as js:
            js.write(js_file_content)

    pass