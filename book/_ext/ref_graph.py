from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from docutils.parsers.rst import directives
from docutils import nodes
from sphinx_design.shared import SEMANTIC_COLORS
from docutils.nodes import reference
import os
import numpy as np
from sphinx.addnodes import number_reference

from d3graph import d3graph, vec2adjmat

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

    def run(self) -> list[nodes.Node]:
        graph_node = ref_graph()
        classes = "dark-light" # still to implement correctly
        html = f'<iframe class="{classes}" id="ref_graph" src="placeholder" style="width: 100%; aspect-ratio: 1 / 1; border: none; border-radius: 8px;"></iframe>'
        
        html_node = nodes.raw(None, html, format="html")
        graph_node.insert(0,html_node)

        return [graph_node]
    
class ref_graph(nodes.Admonition, nodes.Element):
    pass

def visit_ref_graph_node(self, node):
    pass

def depart_ref_graph_node(self, node):
    pass

def setup(app: Sphinx):

    app.add_config_value("ref_graph_temp_file","ref_graph.temp",'env')
    app.add_config_value("ref_graph_html_file","ref_graph.html",'env')
    app.add_config_value("ref_graph_js_file","ref_graph.js",'env')

    app.add_directive("refgraph", RefGraphDirective)

    app.add_node(ref_graph,
                 html=(visit_ref_graph_node, depart_ref_graph_node),
                 latex=(visit_ref_graph_node, depart_ref_graph_node),
                 text=(visit_ref_graph_node, depart_ref_graph_node))
    
    app.connect('doctree-resolved', process_ref_nodes)
    app.connect('build-finished',write_js)
    app.connect('build-finished',write_html)

    app.add_js_file(app.config.ref_graph_js_file)

    return {'parallel_write_safe': False}

# def purge_tags(app, env, docname):
#     if not hasattr(env, 'ref_graph_all_tags'):
#         return
#     env.ref_graph_all_tags = [tags for tags in env.ref_graph_all_tags if tags['docname'] != docname]

def process_ref_nodes(app, doctree, fromdocname):
    # Add here the collection of all tags and create the information for the graph 
    all_refs = []

    for node in doctree.traverse(reference):
        target = None
        # only internal references are interesting
        if isinstance(node,number_reference):
            if 'refuri' in node.attributes:
                target = node['refuri']
        else:
            if 'internal' in node.attributes:
                if 'refuri' in node.attributes:
                    target = node['refuri']
        if target:
            # make sure ALL urls are absolute and only point to a html file
            # 0) strip everything after .html from target and strip first / if present
            hashtag = target.find("#")
            if hashtag>-1:
                target = target[:hashtag]
            # 1) extract base folder from fromdocname
            parts = fromdocname.split('/')
            if len(parts)==1:
                folder = ''
            else:
                folder = "/".join(parts[:-1])
            # 2) now compare base folder with target
            #    if target has no folder, it was relative to original folder
            #    so prepend folder
            #    if target has folders and starts with one or more .., change folder and prepend
            #    otherwise prepend
            parts = target.split('/')
            if len(parts)>1:
                while parts[0] == "..":
                    # so first go one up, then go to another folder.
                    # this means the folder has to be adapted before it can be prepended to the target
                    folder = "/".join(folder.split("/")[:-1])
                    if folder != '':
                        if folder[0]=="/":
                            folder = folder[1:]
                    parts = parts[1:]
                    target = "/".join(parts)
                    if target[0] == "/":
                        target=target[1:]    
            
            target = "/".join([folder,target])
            if target[0] == "/":
                target=target[1:]
            # 3) make the source an html file
            source = fromdocname + ".html"
            
            # store the reference:
            all_refs.append((source,target))

    if len(all_refs)>0:
        staticdir = os.path.join(app.builder.outdir, '_static')
        filename = os.path.join(staticdir,app.config.ref_graph_temp_file)
        with open(filename,"a", encoding="utf-8") as out:
            for source, target in all_refs:
                out.write(f"{source} -> {target}\n")

    pass

def write_html(app,exc):

    # import the (finished) ref_graph temp file and convert it to an adjacency matrix
    # Step 0: load data from temp file as set of lines
    staticdir = os.path.join(app.builder.outdir, '_static')
    filename = os.path.join(staticdir,app.config.ref_graph_temp_file)
    with open(filename,"r", encoding="utf-8") as temp:
        lines = temp.readlines()
    lines = [x.strip() for x in lines]
    # Step 1: extract list of nodes and links from lines
    node_list = []
    link_list = []
    weight_list = []
    for line in lines:
        source,target = line.split(" -> ")
        # check if source already in node_list, if not, add
        if source not in node_list:
            node_list.append(source)
        # check if target already in node_list, if not, add
        if target not in node_list:
            node_list.append(target)
        link = [source,target]
        if link not in link_list:
            link_list.append(link)
            weight_list.append(1)
        else:
            weight_list[link_list.index(link)] += 1
    
    source_list = [link[0] for link in link_list]
    target_list = [link[1] for link in link_list]

    # create adjacency matrix for d3graph
    adjmat = vec2adjmat(source_list,target_list,weight_list)
    # initialise
    d3 = d3graph()
    d3.graph(adjmat)
    # export to html file
    rng = np.random.default_rng()
    width = rng.integers(1000,2000)
    height = rng.integers(3000,4000)
    print("(width,height)",width,height)
    filename = os.path.join(staticdir,app.config.ref_graph_html_file)
    d3.show(filepath=filename,showfig=False,show_slider=False,figsize=[width, height])

    # load the html file and remove several unneeded lines
    remove = ['id="saveButton"',"ethicalads","erdogantgithubio"]
    with open(filename,'r', encoding="utf8") as html:
        html_lines = html.readlines()
    for screwit in remove:
        found = -1
        for i,html_line in enumerate(html_lines):
            if screwit in html_line:
                found = i
                break
        if found>=0:
            if "saveButton" in html_line:
                html_lines = html_lines[:(found-1)]+html_lines[(found+2):]
            else:
                html_lines = html_lines[:found]+html_lines[(found+1):]

    # now find specfic lines for settting the height and the width and make them responsive
    found = -1
    for i,line in enumerate(html_lines):
        if "window.addEventListener('DOMContentLoaded', function () {" in line:
            found = i
            break
    new_lines = ["const width = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);\n","const height = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);\n"]
    html_lines = html_lines[:(found+1)]+new_lines+html_lines[(found+1):]
    for i,line in enumerate(html_lines):
        if f"width: {width}," in line:
            html_lines[i] = line.replace(f"width: {width},","width: 0.99*width,")
        if f"height: {height}," in line:
            html_lines[i] = line.replace(f"height: {height},","height: 0.99*height,")
        if "directed: false," in line:
            html_lines[i] = line.replace("directed: false,","directed: true,")

    # Now to the same for the CSS
    found = -1
    for i,line in enumerate(html_lines):
        if '<style type="text/css">' in line:
            found = i
            break
    new_lines = [" body {\n","margin: 0;\n","overflow: hidden;\n","}\n"]
    html_lines = html_lines[:(found+1)]+new_lines+html_lines[(found+1):]

    with open(filename,'w', encoding="utf8") as html:
        html.writelines(html_lines)
    pass

def write_js(app,exc):

    url = f"window.origin.concat(\"/_static/{app.config.ref_graph_html_file}\")"
    js_content = f'document.addEventListener("DOMContentLoaded", function() {{\nvar iframe = document.getElementById("ref_graph");\nif (iframe) {{\niframe.src = {url};\n}}\n}});'
    staticdir = os.path.join(app.builder.outdir, '_static')
    js_file = os.path.join(staticdir,app.config.ref_graph_js_file)
    with open(js_file,'w') as js:
        js.write(js_content)

    pass