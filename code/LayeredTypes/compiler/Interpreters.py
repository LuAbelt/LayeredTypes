import importlib
from collections import namedtuple
import lark
from pathlib import Path
import sys

FunctionDefinition = namedtuple("FunctionDefinition", ["name", "args", "body"])

class SimpleInterpreter(lark.visitors.Interpreter):
    def __init__(self, implementation_file = "implementations"):
        # Variables and functions are stored in dictionaries for access by our interpreter
        self.variables = dict()
        self.functions = dict()

        impl_path = Path(implementation_file)
        if not impl_path.is_file():
            raise FileNotFoundError(f"No implementation file (tried to load file '{implementation_file}') found")

        module_name = "implementations"
        spec = importlib.util.spec_from_file_location(module_name, impl_path)
        self.external_functions = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = self.external_functions
        spec.loader.exec_module(self.external_functions)

        self.external_functions_names = [name for name in dir(self.external_functions) if callable(getattr(self.external_functions, name))]

        super().__init__()

    def run(self, tree):
        # Empty variable and function context before running a new program
        self.variables = dict()
        self.functions = dict()

        # Return the value of the last expression in the program
        return self.visit(tree)[-1]
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

        if len(tree.children) > 2:
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

        fun_args = [self.visit(child) for child in tree.children[1:]]

        if not fun_id in self.functions.keys():
            if getattr(self.external_functions, fun_id, None):
                return getattr(self.external_functions, fun_id)(*fun_args)
            raise RuntimeError(f"Function '{fun_id}' not defined")

        fun_def = self.functions[fun_id]
        arg_identifiers = fun_def.args


        old_variables = self.variables.copy()
        # It might happen that a function definition is nested in another function definition
        # In this case, we need to make sure that after the function call, this function definition is not accessible anymore
        old_functions = self.functions.copy()

        self.variables.clear()

        for arg_ident,fun_arg in zip(arg_identifiers, fun_args):
            self.variables[arg_ident] = fun_arg

        # Add the function argument to the variable context

        result = self.visit(fun_def.body)

        # Restore old variable context
        self.variables = old_variables.copy()
        self.functions = old_functions.copy()

        return result
    def fun_def(self, tree):
        fun_id = tree.children[0].value

        arg_identifiers = [child.value for child in tree.children[1:-1]]

        fun_body = tree.children[-1]

        if fun_id in self.functions.keys():
            raise RuntimeError(f"Function '{fun_id}' already defined")

        self.functions[fun_id] = FunctionDefinition(fun_id, arg_identifiers, fun_body)

    def block(self, tree):
        result = None
        for child in tree.children:
            result = self.visit(child)

        return result
    def ident(self, tree):
        identifier = tree.children[0].value

        if not identifier in self.variables.keys():
            raise RuntimeError(f"Identifier '{identifier}' not defined")

        return self.variables[identifier]

    def custom_expr(self, tree):
        expr_str = tree.children[0].value
        print("Custom expression: {}".format(expr_str))

    def layer(self, tree):
        pass
