
import lark
from pathlib import Path

from layers.Layer import Layer
from layers.LayerImplWrapper import LayerImplWrapper
from compiler.transformers.CollectLayers import CollectLayers
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

        self.parser = lark.Lark.open("grammar_file.lark", parser= "lalr", debug=True)

    def typecheck(self, input_file):
        tree = self.__parse(input_file)

        self.__typecheck(tree)

        return True

    def __typecheck(self, tree):
        # TODO: Implement proper typechecking
        lv = CollectLayers()

        ReducedTree = lv.transform(tree)

        layer_wrapper = LayerImplWrapper(lv.layers["base"])
        pass

    def __parse(self, input_file):
        with open(input_file) as f:
            tree = self.parser.parse(f.read())

        return tree

    def compile(self, program):
        tree = self.__parse(program)

        if not self.__typecheck(tree):
            raise RuntimeError("Typechecking failed")

        return tree
    def run(self, program):
        tree = self.compile(program)

        interpreter = SimpleInterpreter(self.implementations_file)

        interpreter.run(tree)
        pass



