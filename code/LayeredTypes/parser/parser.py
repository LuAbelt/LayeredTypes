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
        ident = tree[0].children[0].value
        layer_ident = tree[1].children[0].value
        refinement = tree[2].value

        if not layer_ident in self.layers.keys():
            self.layers[layer_ident] = Layer(layer_ident)
        print("Processing layer {} for identifier {} with rule '{}'".format(layer_ident, ident, refinement))
        self.layers[layer_ident].add_refinement(ident,refinement)
        return lark.Discard

class SimpleInterpreter(lark.visitors.Interpreter):
    def __init__(self, implementation_file = "implementations"):
        # Variables and functions are stored in dictionaries for access by our interpreter
        self.variables = dict()
        self.functions = dict()
        self.external_functions = import_module(implementation_file)
        super().__init__()

    def run(self, tree):
        # Empty variable and function context before running a new program
        self.variables = dict()
        self.functions = dict()

        self.visit(tree)
    def num(self, tree):
        return int(tree.children[0])

    def true(self, tree):
        return True

    def false(self, tree):
        return False

    def assign(self, tree):
        identifier = tree.children[0].children[0].value
        value = self.visit(tree.children[1])

        self.variables[identifier] = value
    def if_stmt(self, tree):

        condition = self.visit(tree.children[0])

        if condition:
            return self.visit(tree.children[1])

        return self.visit(tree.children[2])

    def let_stmt(self, tree):

        identifier = tree.children[0].children[0].value
        value = self.visit(tree.children[1])

        # Store the current value of ident and restore it after the let construct
        restore_val = False
        old_val = None
        if identifier in self.variables.keys():
            old_val = self.variables[identifier]
            restore_val = True

        self.variables[identifier] = value

        result = self.visit(tree.children[2])

        self.variables.pop(identifier)

        if restore_val:
            self.variables[identifier] = old_val

        return result

    def bin_op(self, tree):
        lhs = self.visit(tree.children[0])
        rhs = self.visit(tree.children[2])

        op = tree.children[1].value

        if op == "+":
            return lhs + rhs

        if op == "-":
            return lhs-rhs

        if op == "*":
            return lhs*rhs

        if op == "==":
            return lhs == rhs

        if op == "!=":
            return lhs != rhs

        if op == "<":
            return lhs < rhs

        if op == ">":
            return lhs > rhs

        if op == "<=":
            return lhs <= rhs

        if op == ">=":
            return lhs >= rhs

        raise RuntimeError(f"Unknown operator '{op}'")


    def fun_call(self, tree):
        fun_id = tree.children[0].value
        fun_arg = self.visit(tree.children[1])

        if not fun_id in self.functions.keys():
            if getattr(self.external_functions, fun_id, None):
                return getattr(self.external_functions, fun_id)(fun_arg)
            raise RuntimeError(f"Function '{fun_id}' not defined")

        fun_def = self.functions[fun_id]
        arg_ident = fun_def[0]

        # In order to allow recursive functions we might need to restore the old value of the argument
        restore_val = False
        old_val = None
        if arg_ident in self.variables.keys():
            old_val = self.variables[arg_ident]
            restore_val = True

        # Add the function argument to the variable context
        self.variables[arg_ident] = fun_arg

        result = self.visit(fun_def[1])

        # Remove the function argument from the variable context
        self.variables.pop(arg_ident)

        if restore_val:
            self.variables[arg_ident] = old_val

        return result
    def fun_def(self, tree):

        fun_id = tree.children[0].value
        arg_ident = tree.children[1].value
        fun_def = tree.children[2]

        if fun_id in self.functions.keys():
            raise RuntimeError(f"Function '{fun_id}' already defined")

        self.functions[fun_id] = (arg_ident, fun_def)
        pass

    def ident(self, tree):
        identifier = tree.children[0].value

        if not identifier in self.variables.keys():
            raise RuntimeError(f"Identifier '{identifier}' not defined")

        return self.variables[identifier]


Parser = lark.Lark.open("grammar_file.lark", parser= "lalr", debug=True)

with open("../test/test_code/factorial.fl") as f:
    Tree = Parser.parse(f.read())

lv = CollectLayers()

ReducedTree = lv.transform(Tree)

layer_wrapper = LayerImplWrapper(lv.layers["base"])

SimpleInterpreter().run(ReducedTree)
