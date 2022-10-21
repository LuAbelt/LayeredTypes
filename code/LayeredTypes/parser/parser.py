from importlib import import_module
import lark

class Layer:
    def __init__(self,
                 layer_ident : str):
        self.name = layer_ident
        self.refinements = dict()

    def add_refinement(self,
                       identifier,
                       refinement_str):
        if not identifier in self.refinements.keys():
            self.refinements[identifier] = []
        self.refinements[identifier].append(refinement_str)

    def __str__(self):

        res = "{}:\n".format(self.name)
        for ident in self.refinements:
            refinements = self.refinements[ident]
            res += "\t{}\n".format(ident)

            for refinement in refinements:
                res += "\t\t{}\n".format(refinement)

        return res

class LayerImplWrapper:
    def __init__(self,
                 layer: Layer):
        self.layer = layer
        try:
            self.module = import_module("layers.{}".format(layer.name))
        except ModuleNotFoundError as e:
            raise FileNotFoundError(f"No implementation file (tried to load file './layers/{layer.name}.py') found for layer '{layer.name}'")
        self.depends_on = getattr(self.module, "depends_on")
        self.typecheck = getattr(self.module, "typecheck")
        self.parse_type = getattr(self.module, "parse_type")

class CollectLayers(lark.Transformer):
    def __init__(self):
        super().__init__()
        self.layers = dict()


    def layer(self, tree):
        ident = tree[0].value
        layer_ident = tree[1].value
        refinement = tree[2].value

        if not layer_ident in self.layers.keys():
            self.layers[layer_ident] = Layer(layer_ident)
        print("Processing layer {} for identifier {} with rule '{}'".format(layer_ident, ident, refinement))
        self.layers[layer_ident].add_refinement(ident,refinement)
        return lark.Discard

Parser = lark.Lark.open("grammar_file.lark", parser= "lalr", debug=True)

with open("../test/test_code/factorial.fl") as f:
    # print(f.read())
    Tree = Parser.parse(f.read())

lv = CollectLayers()
ReducedTree = lv.transform(Tree)


layer = LayerImplWrapper(lv.layers["base"])

layer.depends_on()
