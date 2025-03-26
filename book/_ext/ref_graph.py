from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from sphinx.util.docutils import SphinxRole
from docutils.parsers.rst import directives
from docutils import nodes
from docutils.nodes import reference
import os
import numpy as np
from sphinx.addnodes import number_reference

FIXED_COLORS = {
    "#0C2340":0, # Donkerblauw > light+dark prima
    "#00B8C8":0, # Turkoois > light+dark prima
    "#0076C2":0, # Koningsblauw > light+dark prima
    "#6F1D77":0, # Paars > light+dark prima
    "#EF60A3":0, # Roze > light+dark prima
    "#A50034":0, # Bordeaux > light+dark prima
    "#E03C31":0, # Rood > light+dark prima
    "#EC6842":0, # Oranje > light+dark prima
    "#009B77":0 # Bosgroen > light+dark prima
}

class RefGraphDirective(SphinxDirective):
    has_content = False
    required_arguments = 0
    optional_arguments = 0
    option_spec = {
        'class': directives.class_option
    }

    def run(self) -> list[nodes.Node]:
        graph_node = ref_graph()
        classes = self.options.get("class")
        if isinstance(classes,list):
            classes = "ref_graph "+" ".join(classes)
        elif classes is None:
            classes = "ref_graph"
        doc = self.env.docname
        url = f"_static/{self.env.config.ref_graph_html_file}"
        for i in range(doc.count("/")):
            url = "../"+url
        html = f'<iframe class="{classes}" id="ref_graph" src="{url}" style="width: 100%; aspect-ratio: 1 / 1; border: none; border-radius: 8px;"></iframe>'
        
        html_node = nodes.raw(None, html, format="html")
        graph_node.insert(0,html_node)

        return [graph_node]
    
class ref_graph(nodes.Admonition, nodes.Element):
    pass

def visit_ref_graph_node(self, node):
    pass

def depart_ref_graph_node(self, node):
    pass

class HiddenReferences(SphinxDirective):
    has_content = True
    required_arguments = 0
    optional_arguments = 0

    def run(self) -> list[nodes.Node]:
        
        html_start = '<span hidden>'
        html_end = '</span>'
        node_0 = nodes.raw(None, html_start, format="html")
        node_1 = nodes.raw(None, html_end, format="html")
        nodelist = [node_0] + self.parse_content_to_nodes() + [node_1]
        
        return nodelist
    
def setup(app: Sphinx):

    app.add_config_value("ref_graph_temp_file","ref_graph.temp",'env')
    app.add_config_value("ref_graph_html_file","ref_graph.html",'env')
    app.add_config_value("ref_graph_js_file","ref_graph.js",'env')

    app.add_directive("refgraph", RefGraphDirective)
    app.add_directive("hiddenrefs",HiddenReferences)

    app.add_node(ref_graph,
                 html=(visit_ref_graph_node, depart_ref_graph_node),
                 latex=(visit_ref_graph_node, depart_ref_graph_node),
                 text=(visit_ref_graph_node, depart_ref_graph_node))
    
    app.connect('doctree-resolved', process_ref_nodes)
    app.connect('build-finished',write_html)

    return {'parallel_write_safe': False}

def process_ref_nodes(app, doctree, fromdocname):
    # Collection of all references and create the information for the graph 
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

def write_html(app: Sphinx,exc):

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

    # try to extract (first) h1 header from html file
    titles = []
    for node in node_list:
        html_file = os.path.join(app.builder.outdir, node)
        with open(html_file,'r',encoding='utf-8') as html:
            lines = html.readlines()
        for line in lines:
            if "<h1" in line:
                title = line[line.find("<h1")+3:]
                title = title[title.find(">")+1:]
                title = title[:title.find("<")]
                title = title.replace("\\vect{x}","x")
                titles.append(title)
                break

    source_string = "?".join(source_list)
    target_string = "?".join(target_list)
    for i,node in enumerate(node_list):
        source_string = source_string.replace(node,titles[i])
        target_string = target_string.replace(node,titles[i])
    source_list = source_string.split("?")
    target_list = target_string.split("?")

    # Create two json/dicts for direct input in JS
    node_dicts = []
    for i,node in enumerate(node_list):
        if i<3:
            node_dict = {"name":titles[i],
                         "group": "First-tag", # adapt with tags in future, make dashes
                         "link":"../"+node}
        elif i<7:
            node_dict = {"name":titles[i],
                         "group": "Second-tag", # adapt with tags in future, no space, make dashes
                         "link":"../"+node}
        else:
            node_dict = {"name":titles[i],
                         "link":"../"+node}
        node_dicts.append(node_dict)
    
    print("const nodes = ",node_dicts,";")

    link_dicts = []
    for i,source in enumerate(source_list):
        link_dict = {"source_label" : source,
                     "source" : titles.index(source),
                     "target_label" : target_list[i],
                     "target" : titles.index(target_list[i])}
        link_dicts.append(link_dict)
    print("const links = ",link_dicts,";")

    import_html = os.path.join(os.path.dirname(__file__), 'static', "ref_graph.html")
    with open(import_html,'r') as html:
        data = html.readlines()
    for i,line in enumerate(data):
        if '<nodes-line>' in line:
            data[i] = "const nodes = "+str(node_dicts)+";"
        if '<links-line>' in line:
            data[i] = "const links = "+str(link_dicts)+";"

    filename = os.path.join(staticdir,app.config.ref_graph_html_file)
    with open(filename,'w') as file:
        file.writelines(data)

    pass