from sphinx.application import Sphinx
from sphinx_proof.proof_type import DefinitionDirective
import re
from docutils import nodes

class IndexedDefinitionDirective(DefinitionDirective):

    def run(self):
        # for each line in content, identify text between ** and ** annd make sure an index is created
        # for each line in content, identify text between __ and __ annd make sure an index is created
        stuff_to_index = set()
        for lino,line in enumerate(self.content):
            results = re.findall(r'\*\*(.*?)\*\*', line)
            if len(results)>0:
                for res in results:
                    stuff_to_index.add(res)
            results = re.findall(r'__(.*?)__', line)
            if len(results)>0:
                for res in results:
                    stuff_to_index.add(res)
        indexes = ""
        if len(stuff_to_index)>0:
            for index in stuff_to_index:
                indexes += f"{{index}}`{index}` "
        start_node = [nodes.raw(None, "<div style=\"overflow:hidden;height:0px;margin:calc(var(--bs-body-font-size)*-1);\">", format="html")]
        end_node = [nodes.raw(None, "</div>", format="html")]
        parsed_indexes = self.parse_text_to_nodes(indexes)
        node_list = start_node + parsed_indexes + end_node + DefinitionDirective.run(self)
        return node_list

def setup(app: Sphinx):

    app.setup_extension('sphinx_proof')

    app.add_directive_to_domain('prf','definition',IndexedDefinitionDirective,override=True)

    return {}