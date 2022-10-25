import lark
from layers.Layer import Layer

class CollectLayers(lark.Transformer):
    def __init__(self):
        super().__init__()
        self.layers = dict()


    def layer(self, tree):
        ident = tree[0].children[0].value
        layer_ident = tree[1].children[0].value
        refinement = tree[2].value

        if not layer_ident in self.layers.keys():
            self.layers[layer_ident] = Layer(layer_ident)
        print("Processing layer {} for identifier {} with rule '{}'".format(layer_ident, ident, refinement))
        self.layers[layer_ident].add_refinement(ident,refinement)
        return lark.Discard
