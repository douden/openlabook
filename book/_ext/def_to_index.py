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
        # now find all strong and emphasis node
        stuff_to_index = set()
        for def_node in def_nodes[0][1]: # skip the title
            for typ in self.env.config.sphinx_proof_index:
                cls = eval("nodes."+typ)
                typ_nodes = def_node.findall(cls)
                for node in typ_nodes:
                    node_string = node.__str__()
                    node_string = node_string.replace(f"<{typ}>","")
                    node_string = node_string.replace(f"</{typ}>","")
                    node_string = node_string.replace("<math>","$")
                    node_string = node_string.replace("</math>","$")
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
        node_list = start_node + parsed_indexes + end_node + DefinitionDirective.run(self)

        # if self.env.docname == "Chapter1/Vectors":
        #     for node in node_list:
        #         emph_nodes = node.findall(nodes.emphasis)
        #         for emph_node in emph_nodes:
        #             print(emph_node.pformat())

        return node_list

def setup(app: Sphinx):

    app.add_config_value('sphinx_proof_index',['strong','emphasis'],'env')

    app.setup_extension('sphinx_proof')

    app.add_directive_to_domain('prf','definition',IndexedDefinitionDirective,override=True)
    app.add_directive_to_domain('prf','olddefinition',OldDefinitionDirective)

    return {}