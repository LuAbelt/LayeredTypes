import graphlib
import os.path
from warnings import warn

import lark
from pathlib import Path

from compiler.Exceptions import LayerException
from compiler.transformers.RemoveTokens import RemoveTokens
from layers.Layer import Layer
from layers.LayerImplWrapper import LayerImplWrapper

from compiler.transformers.CollectLayers import CollectLayers
from compiler.interpreters.CheckCF import CheckCF
from compiler.transformers.CreateAnnotatedTree import CreateAnnotatedTree as AnnotateTree
from compiler.Interpreters import SimpleInterpreter

class LayeredCompiler:
    def __init__(self, layer_base_dir, implementations_file=None):

        self.layer_base_dir = Path(layer_base_dir)

        if implementations_file is None:
            self.implementations_file = None
        else:
            self.implementations_file = Path(implementations_file)
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

    def typecheck(self, input_file, check_cf=True):
        tree = self.parse(input_file)

        self.__typecheck(tree, check_cf)

        return True

    def __typecheck(self, tree, check_cf=True):
        lv = CollectLayers()
        cf_check = CheckCF(self.interpreter.external_functions_names)

        tree = lv.transform(tree)
        tree = AnnotateTree().transform(tree)

        if check_cf:
            cf_check.visit(tree)

        layer_graph = {}
        self.layers = {}

        implicit_layers = set()

        for layer_id in lv.layers:
            self.layers[layer_id] = LayerImplWrapper(self.layer_base_dir, lv.layers[layer_id])

            required_layers = self.layers[layer_id].depends_on()
            layer_graph[layer_id] = required_layers
            implicit_layers.update(required_layers - set(lv.layers.keys()))

            required_layers = self.layers[layer_id].run_before()
            for layer in required_layers:
                layer_graph[layer].add(layer_id)

            implicit_layers.update(required_layers - set(lv.layers.keys()))

            implied_layers = self.layers[layer_id].run_before()
            implicit_layers.update(implied_layers - set(lv.layers.keys()))
            for implied_layer in implied_layers:
                if implied_layer not in layer_graph:
                    layer_graph[implied_layer] = set()
                layer_graph[implied_layer].add(layer_id)



        while len(implicit_layers) > 0:
            layer_id = implicit_layers.pop()
            if not layer_id in self.layers:
                warn(f"Layer {layer_id} was not loaded during CollectLayers, but is required by at least one other layer. Loading it now.")
                self.layers[layer_id] = LayerImplWrapper(self.layer_base_dir, Layer(layer_id))
                required_layers = self.layers[layer_id].depends_on()
                layer_graph[layer_id] = required_layers
                implicit_layers.update(required_layers - set(self.layers.keys()))

                required_layers = self.layers[layer_id].run_before()
                for layer in required_layers:
                    layer_graph[layer].add(layer_id)
                implicit_layers.update(required_layers - set(lv.layers.keys()))

        # Check for cycles
        try:
            topo_order = [n for n in graphlib.TopologicalSorter(layer_graph).static_order()]
        except graphlib.CycleError as e:
            raise graphlib.CycleError(f"Cycle in layer dependencies: {e.args[0]}")

        # Incrementally typecheck each layer based on their topological order
        for layer_id in topo_order:
            layer_handle = self.layers[layer_id]
            try:
                tree = layer_handle.typecheck(tree)
            except Exception as e:
                raise LayerException(layer_id,e)

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





