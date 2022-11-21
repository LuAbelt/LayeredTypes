import graphlib
import os.path
from warnings import warn

import lark
from pathlib import Path


from compiler.transformers.RemoveTokens import RemoveTokens
from layers.Layer import Layer
from layers.LayerImplWrapper import LayerImplWrapper

from compiler.transformers.CollectLayers import CollectLayers
from compiler.transformers.CheckCF import CheckCF
from compiler.transformers.CreateAnnotatedTree import CreateAnnotatedTree as AnnotateTree
from compiler.Interpreters import SimpleInterpreter

class LayeredCompiler:
    def __init__(self
                 , implementations_file
                 , layer_base_dir):

        self.implementations_file = Path(implementations_file)
        self.layer_base_dir = Path(layer_base_dir)

        if not self.implementations_file.is_file():
            raise FileNotFoundError(f"Could not find implementations file at {self.implementations_file}")

        if not self.layer_base_dir.is_dir():
            raise FileNotFoundError(f"Could not find layer base directory at {self.layer_base_dir}")

        # Build path for grammar file
        grammar_file = os.path.dirname(os.path.realpath(__file__)) + "/grammar_file.lark"
        self.parser = lark.Lark.open(grammar_file
                                     , parser= "lalr"
                                     , debug=True
                                     , propagate_positions=True
                                     , transformer=RemoveTokens(["newline"]))
        self.layers = dict()
        self.interpreter = SimpleInterpreter(self.implementations_file)

    def typecheck(self, input_file):
        tree = self.parse(input_file)

        self.__typecheck(tree)

        return True

    def __typecheck(self, tree):
        lv = CollectLayers()
        cf_check = CheckCF(self.interpreter.external_functions_names)

        tree = lv.transform(tree)
        tree = AnnotateTree().transform(tree)
        cf_check.visit(tree)

        layer_graph = {}
        self.layers = {}

        implicit_layers = set()

        for layer_id in lv.layers:
            self.layers[layer_id] = LayerImplWrapper(self.layer_base_dir, lv.layers[layer_id])
            required_layers = self.layers[layer_id].depends_on()
            implicit_layers.update(required_layers - set(lv.layers.keys()))
            layer_graph[layer_id] = required_layers

        while len(implicit_layers) > 0:
            layer_id = implicit_layers.pop()
            if not layer_id in self.layers:
                warn(f"Layer {layer_id} was not loaded during CollectLayers, but is required by at least one other layer. Loading it now.")
                self.layers[layer_id] = LayerImplWrapper(self.layer_base_dir, Layer(layer_id))
                required_layers = self.layers[layer_id].depends_on()
                implicit_layers.update(required_layers - set(self.layers.keys()))
                layer_graph[layer_id] = required_layers

        # Check for cycles
        try:
            topo_order = [n for n in graphlib.TopologicalSorter(layer_graph).static_order()]
        except graphlib.CycleError as e:
            raise graphlib.CycleError(f"Cycle in layer dependencies: {e.args[0]}")

        # Incrementally typecheck each layer based on their topological order
        for layer_id in topo_order:
            layer_handle = self.layers[layer_id]
            tree = layer_handle.typecheck(tree)

        return tree

    def parse(self, input_file):
        with open(os.path.abspath(input_file)) as f:
            tree = self.parser.parse(f.read())

        Remover = RemoveTokens(["newline"])
        tree = Remover.transform(tree)

        return tree

    def compile(self, program):
        tree = self.parse(program)

        if not self.__typecheck(tree):
            raise RuntimeError("Typechecking failed")

        return tree
    def run(self, program):
        tree = self.compile(program)

        return self.interpreter.run(tree)





