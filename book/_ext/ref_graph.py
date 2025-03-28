from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from docutils.parsers.rst import directives
from docutils import nodes
from docutils.nodes import reference
import os
from sphinx.addnodes import number_reference
import ast

FIXED_COLORS = [
    "#6F1D77", # Light Purple
    "#0C2340", # Dark Blue
    "#EC6842", # Orange
    "#0076C2", # Royal Blue
    "#E03C31", # Red
    "#00B8C8", # Turquoise
    "#EF60A3", # Pink
    "#009B77", # Forrest Green
    "#A50034", # Burgundy
]    

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

def setup(app: Sphinx):

    app.add_config_value("ref_graph_temp_file","ref_graph.temp",'env')
    app.add_config_value("ref_graph_html_file","ref_graph.html",'env')
    app.add_config_value("ref_graph_internal_links",True,'env')
    app.add_config_value("ref_graph_toc_links",True,'env')
    app.add_config_value("ref_graph_tag_color",{},'env')
    app.add_config_value("ref_graph_remove_links",[],'env')

    app.add_directive("refgraph", RefGraphDirective)

    app.add_node(ref_graph,
                 html=(visit_ref_graph_node, depart_ref_graph_node),
                 latex=(visit_ref_graph_node, depart_ref_graph_node),
                 text=(visit_ref_graph_node, depart_ref_graph_node))
    
    app.connect('doctree-resolved', process_ref_nodes)
    app.connect('build-finished',write_html)

    app.connect('builder-inited',parse_toc)

    return {'parallel_write_safe': False}

def process_ref_nodes(app: Sphinx, doctree, fromdocname):

    if app.config.ref_graph_internal_links:
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
                    # don't do it if we want to ignore it
                    line = f"{source} -> {target}"
                    if line not in app.config.ref_graph_remove_links:
                        out.write(line+"\n")

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
    ignore_list = []
    tag_list = []
    link_list = []
    weight_list = []
    read_nodes = True
    for lino,line in enumerate(lines):
        if lino==0:
            continue
        
        if line.strip() == "==== links ====":
            read_nodes = False
            continue

        if read_nodes:
            node,ignore,tag = line.split(">")
            node = node.strip()
            ignore = ignore.strip() == 'True'
            tag = tag.strip()
            node_list.append(node)
            ignore_list.append(ignore)
            tag_list.append(tag)
            continue
        else:
            source,target = line.split(" -> ")
            # check if source already in node_list, if not, add (should not happen)
            if source not in node_list:
                node_list.append(source)
                ignore_list.append(False)
                tag_list.append("")
            # check if target already in node_list, if not, add (should not happen)
            if target not in node_list:
                node_list.append(target)
                ignore_list.append(False)
                tag_list.append("")
            # check if link should be ignored, because source should be ignored
            if ignore_list[node_list.index(source)]:
                continue
            # check if link should be ignored, because target should be ignored
            if ignore_list[node_list.index(target)]:
                continue
            link = [source,target]
            if link not in link_list:
                link_list.append(link)
                weight_list.append(1)
            else:
                weight_list[link_list.index(link)] += 1

    # clean up
    node_list_old = node_list.copy()
    tag_list_old = tag_list.copy()
    node_list = []
    tag_list = []
    for i,node in enumerate(node_list_old):
        if not ignore_list[i]:
            node_list.append(node)
            tag_list.append(tag_list_old[i])

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

    # Create three json/dicts for direct input in JS
    node_dicts = []
    for i,node in enumerate(node_list):
        node_dict = {"name":titles[i],
                     "link":"../"+node}
        # now check with tag
        if tag_list[i] != "":
            node_dict = node_dict | {"group": tag_list[i]}
        node_dicts.append(node_dict)
    
    link_dicts = []
    for i,source in enumerate(source_list):
        link_dict = {"source_label" : source,
                     "source" : titles.index(source),
                     "target_label" : target_list[i],
                     "target" : titles.index(target_list[i])}
        link_dicts.append(link_dict)

    color_dict = {}
    unique_tags = []
    for tag in tag_list:
        if tag not in unique_tags:
            if tag != '':
                unique_tags.append(tag)
    next_color = 0
    for tag in unique_tags:
        if tag in app.config.ref_graph_tag_color:
            color_dict[tag] = app.config.ref_graph_tag_color[tag]
        else:
            color_dict[tag] = FIXED_COLORS[next_color]
            next_color = (next_color + 1) % len(FIXED_COLORS)

    import_html = os.path.join(os.path.dirname(__file__), 'static', "ref_graph.html")
    with open(import_html,'r') as html:
        data = html.readlines()
    for i,line in enumerate(data):
        if '<nodes-line>' in line:
            data[i] = "const nodes = "+str(node_dicts)+";"
        if '<links-line>' in line:
            data[i] = "const links = "+str(link_dicts)+";"
        if '<color-line>' in line:
            data[i] = "const groupColors = "+str(color_dict)+";"

    filename = os.path.join(staticdir,app.config.ref_graph_html_file)
    with open(filename,'w') as file:
        file.writelines(data)

    pass

def parse_toc(app:Sphinx):

    # prepare file
    staticdir = os.path.join(app.builder.outdir, '_static')
    if not os.path.exists(staticdir):
        os.makedirs(staticdir)
    filename = os.path.join(staticdir,app.config.ref_graph_temp_file)
    with open(filename,'w',encoding="utf-8") as firstout:
        firstout.write("==== nodes ====\n")

    # load ToC contents
    toc_path = os.path.join(app.srcdir,'_toc.yml')
    with open(toc_path,'r') as toc_file:
        toc_lines = toc_file.readlines()
    
    # parse each line
    node_list = []
    ref_list = []
    for toc_line in toc_lines:
        # strip leading spaces
        toc_line = " ".join(toc_line.split())
        # ignore empty lines
        if len(toc_line)==0:
            continue
        # ignore commented lines
        if toc_line[0] == "#":
            continue
        # ignore no-file lines (except root line)
        if "- file" not in toc_line:
            if "root" not in toc_line:
                continue
            else:
                toc_line.replace('root','- file')
        # extract information
        if "#" not in toc_line:
            # no comment in line
            file = toc_line.split(":",1)[1].strip()
            dict = {}
        else:
            # extract file and comment
            file_and_comment = toc_line.split(":",1)[1].strip()
            file,comment = file_and_comment.split("#",1)
            # ignore if 'ref_graph:' not in comment
            if 'ref_graph:' not in comment:
                dict = {}
                continue
            # take part after 'ref_graph:',
            # take dictionary, assuming no { or } are present in tags
            comment = " ".join(comment[comment.find('ref_graph:')+11:].split())
            start = comment.find("{")
            end = comment.find("}")+1
            dict = ast.literal_eval(comment[start:end])
        # clean up file name and dict values
        file = file.replace(r"'","").replace(r'"',"").replace(".md","").replace(".ipynb","").strip()
        if 'tag' in dict:
            dict['tag'] = dict['tag'].replace(r"'","").replace(r'"',"")
        if 'refs' in dict:
            if not isinstance(dict['refs'],list):
                dict['refs'] = [dict['refs']]
            for i,ref in enumerate(dict['refs']):
                dict['refs'][i] = ref.replace(r"'","").replace(r'"',"").replace(".md","").replace(".ipynb","").strip()
        
        if 'ignore' in dict:
            ignore = dict['ignore']
        else:
            ignore = False
        if 'tag' in dict:
            tag = dict['tag']
        else:
            tag = ''
        node_list.append((file,ignore,tag))
        if 'refs' in dict:
            refs = dict['refs']
        else:
            refs = []
        ref_list.append(refs)

    # store nodes with tags in file
    with open(filename,'a',encoding="utf-8") as lastout:
        for node in node_list:
            lastout.write(f"{node[0]}.html > {node[1]} > {node[2]}\n")
        lastout.write("==== links ====\n")

    if app.config.ref_graph_toc_links:
        # store links
        with open(filename,'a',encoding="utf-8") as lastout:
            for i,node in  enumerate(node_list):
                for ref in ref_list[i]:
                    lastout.write(f"{node[0]}.html -> {ref}.html\n")
    
    pass