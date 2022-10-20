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

class LayerVisitor(lark.Visitor):
    def __init__(self):
        self.layers = dict()


    def layer(self, tree):
        ident = tree.children[0].value
        layer_ident = tree.children[1].value
        refinement = tree.children[2].value

        if not layer_ident in self.layers.keys():
            self.layers[layer_ident] = Layer(layer_ident)
        print("Processing layer {} for identifier {} with rule '{}'".format(layer_ident, ident, refinement))
        self.layers[layer_ident].add_refinement(ident,refinement)
        pass

Parser = lark.Lark.open("grammar_file.lark", parser= "lalr", debug=True)

with open("../test/test_code/factorial.fl") as f:
    # print(f.read())
    Tree = Parser.parse(f.read())

lv = LayerVisitor()
lv.visit(Tree)

print(lv.layers)