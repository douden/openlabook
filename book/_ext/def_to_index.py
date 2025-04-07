from sphinx.application import Sphinx
from sphinx_proof.proof_type import DefinitionDirective
import re
from docutils import nodes

class OldDefinitionDirective(DefinitionDirective):
    
    def run(self):
        self.name = 'prf:definition'
        return DefinitionDirective.run(self)

class IndexedDefinitionDirective(DefinitionDirective):

    def run(self):        

        # first the normal parse:
        def_nodes = DefinitionDirective.run(self)
        # get the classes and do no index stuff if told so.
        classes = self.options.get('class')
        if classes is not None:
            if "noindex" in classes:
                return def_nodes
        # now find all strong and emphasis node
        stuff_to_index = set()
        for def_node in def_nodes[0][1]: # skip the title
            for typ in self.env.config.sphinx_proof_indexed_nodes:
                cls = eval("nodes."+typ)
                typ_nodes = def_node.findall(cls)
                for node in typ_nodes:
                    node_string = node.__str__()
                    node_string = node_string.replace(f"<{typ}>","")
                    node_string = node_string.replace(f"</{typ}>","")
                    node_string = node_string.replace("<math>","$")
                    node_string = node_string.replace("</math>","$")
                    # check if the index should be skipped
                    skip_index = False
                    for regexp in self.env.config.sphinx_proof_skip_indices:
                        if re.search(regexp,node_string):
                            skip_index = True
                            break
                    if not skip_index:
                        # check for weird references
                        if "classes" not in node_string:
                            stuff_to_index.add(node_string)
                        elif "xref" not in node_string:
                            stuff_to_index.add(node_string)

        indexes = ""
        if len(stuff_to_index)>0:
            for index in stuff_to_index:
                indexes += f"{{index}}`{index}` "
        start_node = [nodes.raw(None, "<div style=\"overflow:hidden;height:0px;margin:calc(var(--bs-body-font-size)*-0.5);\">", format="html")]
        end_node = [nodes.raw(None, "</div>", format="html")]
        parsed_indexes = self.parse_text_to_nodes(indexes)
        node_list = start_node + parsed_indexes + end_node + def_nodes

        return node_list

def setup(app: Sphinx):

    app.add_config_value('sphinx_proof_indexed_nodes',['strong','emphasis'],'env')
    app.add_config_value('sphinx_proof_skip_indices',[],'env')

    app.setup_extension('sphinx_proof')

    app.add_directive_to_domain('prf','definition',IndexedDefinitionDirective,override=True)

    return {}