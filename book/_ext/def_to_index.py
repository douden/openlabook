from sphinx.application import Sphinx
from sphinx_proof.proof_type import DefinitionDirective
import re
from docutils import nodes

SUPPORTED_NODES = ['strong','emphasis','literal']
DEFAULT_NODES = ['strong','emphasis']
CAPITAL_WORDS = list({'Cartesian','Markov','Euler','Neumann','Newton','Gauss','Lagrange','Hilbert','Frobenius','Navier','Stokes','Laplace','Cauchy','Erdős','Ramanujan',
                      'Kolmogorov','Darcy','Archimedes','Chebychev','Castigliano','Taylor','Maclaurin','Macaulay','Mohr','Jensens','Muller','Breslau','Bernoulli',
                      'Maxwell','Einstein','Froud','Reynolds','Betti','Rayleigh','Ohm','Volt','Ampère','Tesla','Curie','Turing','Murphy','Avogrado','Planck'})

class IndexedDefinitionDirective(DefinitionDirective):

    def run(self):        

        # first the normal parse:
        def_nodes = DefinitionDirective.run(self)
        # get the classes and do no index stuff if told so.
        classes = self.options.get('class')
        if classes is not None:
            if "skipindexing" in classes:
                return def_nodes
        # now find all strong and emphasis node
        stuff_to_index = set()
        # find out if a title has been set (and has to be indexed)
        if self.env.config.sphinx_indexed_defs_index_titles:
            if len(self.arguments) != 0:
                title = self.arguments[0]
                if self.env.config.sphinx_indexed_defs_lowercase_indices:
                    new_string = title.lower()
                    new_math = re.findall(r"\$(.*?)\$", new_string)
                    old_math = re.findall(r"\$(.*?)\$", title)
                    for eeeee,mathe in enumerate(new_math):
                        new_string = new_string.replace(f"${mathe}$",f"${old_math[eeeee]}$")
                    for word in self.env.config.sphinx_indexed_defs_capital_words:
                        new_string = new_string.replace(f"{word.lower()}",f"{word}")
                    title = new_string
                stuff_to_index.add(title)
        for typ in self.env.config.sphinx_indexed_defs_indexed_nodes:
            assert typ in SUPPORTED_NODES, f"the node {typ} is not supported"
            list_of_nodes = def_nodes[0][1]
            for def_node in list_of_nodes:
                cls = eval("nodes."+typ)
                typ_nodes = def_node.findall(cls)
                for node in typ_nodes:
                    node_string = node.__str__()
                    node_string = node_string.replace(f"<{typ}>","")
                    node_string = node_string.replace(f"</{typ}>","")
                    node_string = node_string.replace(f"<{typ}/>","")
                    node_string = node_string.replace("<math>","$")
                    node_string = node_string.replace("</math>","$")
                    if self.env.config.sphinx_indexed_defs_lowercase_indices:
                        new_string = node_string.lower()
                        new_math = re.findall(r"\$(.*?)\$", new_string)
                        old_math = re.findall(r"\$(.*?)\$", node_string)
                        for eeeee,mathe in enumerate(new_math):
                            new_string = new_string.replace(f"${mathe}$",f"${old_math[eeeee]}$")
                        for word in self.env.config.sphinx_indexed_defs_capital_words:
                            new_string = new_string.replace(f"{word.lower()}",f"{word}")
                        node_string = new_string

                    # check if the index should be skipped
                    skip_index = False
                    if node_string == "":
                        continue
                    for regexp in self.env.config.sphinx_indexed_defs_skip_indices:
                        if re.search(regexp,node_string):
                            skip_index = True
                            break
                    if skip_index:
                        continue
                    # check for weird references
                    if "classes" not in node_string:
                        stuff_to_index.add(node_string)
                    elif "xref" not in node_string:
                        stuff_to_index.add(node_string)

        indexes = ""
        if len(stuff_to_index)>0:
            for index in stuff_to_index:
                indexes += f"{{index}}`{index}`"
        start_node = [nodes.raw(None, "<div style=\"overflow:hidden;height:0px;margin:calc(var(--bs-body-font-size)*-0.5);\">", format="html")]
        end_node = [nodes.raw(None, "</div>", format="html")]
        parsed_indexes = self.parse_text_to_nodes(indexes)
        node_list = start_node + parsed_indexes + end_node + def_nodes

        return node_list

def setup(app: Sphinx):

    app.add_config_value('sphinx_indexed_defs_indexed_nodes',DEFAULT_NODES,'env')
    app.add_config_value('sphinx_indexed_defs_skip_indices',[],'env')
    app.add_config_value('sphinx_indexed_defs_lowercase_indices',True,'env')
    app.add_config_value('sphinx_indexed_defs_index_titles',True,'env')
    app.add_config_value('sphinx_indexed_defs_capital_words',[],'env')

    app.connect('config-inited',parse_config)

    app.setup_extension('sphinx_proof')

    app.add_directive_to_domain('prf','definition',IndexedDefinitionDirective,override=True)

    return {}

def parse_config(app:Sphinx,config):
    
    capital_words = app.config.sphinx_indexed_defs_capital_words + CAPITAL_WORDS
    app.config.sphinx_indexed_defs_capital_words = list(set(capital_words))

    pass