import lark

from compiler.transformers.CreateAnnotatedTree import AnnotatedTree
from layers.Layer import Layer


class CollectLayers(lark.Transformer):
    def __init__(self):
        super().__init__()
        self.layers = dict()

    layers = dict()

    def __default__(self, data: str, tree, meta):
        if data != "layer":
            return lark.Tree(data, tree, meta)

        ident = tree[0].children[0].value
        layer_ident = tree[1].children[0].value
        refinement = tree[2].value

        if not layer_ident in self.layers.keys():
            self.layers[layer_ident] = Layer(layer_ident)
        # print("Collecting layer {} for identifier {} with rule '{}'".format(layer_ident, ident, refinement))
        self.layers[layer_ident].add_refinement(ident, refinement)
        return AnnotatedTree(data, tree, meta)
