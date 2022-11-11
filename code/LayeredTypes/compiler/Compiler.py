import graphlib
import os.path

import lark
from pathlib import Path

from compiler.transformers.RemoveTokens import RemoveTokens
from layers.LayerImplWrapper import LayerImplWrapper
from compiler.transformers.CollectLayers import CollectLayers
from compiler.transformers.CheckCF import CheckCF
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

    def typecheck(self, input_file):
        tree = self.parse(input_file)

        self.__typecheck(tree)

        return True

    def __typecheck(self, tree):
        lv = CollectLayers()
        cf_check = CheckCF()

        reducedTree = lv.transform(tree)
        cf_check.visit(reducedTree)

        layer_graph = {}
        layers = {}
        for layer_id in lv.layers:
            layers[layer_id] = LayerImplWrapper(self.layer_base_dir, lv.layers[layer_id])
            layer_graph[layer_id] = layers[layer_id].depends_on()

        # Check for cycles
        try:
            topo_order = graphlib.TopologicalSorter(layer_graph).static_order()
        except graphlib.CycleError as e:
            raise RuntimeError(f"Cycle in layer dependencies: {e.args[0]}")

        # Incrementally typecheck each layer based on their topological order
        for layer_id in topo_order:
            layers[layer_id].typecheck()

        return reducedTree

    def parse(self, input_file):
        with open(input_file) as f:
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

        interpreter = SimpleInterpreter(self.implementations_file)

        return interpreter.run(tree)



