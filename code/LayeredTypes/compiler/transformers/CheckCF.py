from warnings import warn

import lark


class CheckCF(lark.visitors.Interpreter):
    def __init__(self, external_functions=None):
        super().__init__()
        self.variables = set()
        self.functions = set()
        self.external_functions = external_functions or set()

    def assign(self, tree):
        # We first check the right hand side of the assignment
        # This is to detect if the identifier is used before it is defined
        self.visit(tree.children[1])

        # Add defined identifier to set
        identifier = tree.children[0].children[0].value
        self.variables.add(identifier)

    def layer(self, tree):
        # We explicitly ignore the layer definitions as they have no effect on the control flow
        pass

    def let_stmt(self, tree):
        identifier = tree.children[0].children[0].value

        if identifier in self.variables:
            meta = tree.children[0].meta
            error = SyntaxError(f"Identifier {identifier} already defined")
            error.lineno = meta.line
            error.offset = meta.column
            error.end_lineno = meta.end_line
            error.end_offset = meta.end_column
            raise error

        # We add the identifier to the set only for the duration of the let construct
        self.variables.add(identifier)

        self.visit(tree.children[2])

        self.variables.discard(identifier)

    def ident(self, tree):
        identifier = tree.children[0].value
        if identifier not in self.variables:
            meta = tree.meta
            error = SyntaxError(f"Identifier {identifier} not defined")
            error.lineno = meta.line
            error.offset = meta.column
            error.end_lineno = meta.end_line
            error.end_offset = meta.end_column
            raise error

    def fun_call(self, tree):
        fun_name = tree.children[0].value

        if fun_name not in self.functions and fun_name not in self.external_functions:
            # Emit a warning if the function is not defined
            meta = tree.meta
            error = SyntaxError(f"Function {fun_name} not defined")
            error.lineno = meta.line
            error.offset = meta.column
            error.end_lineno = meta.end_line
            error.end_offset = meta.end_column
            raise error

        for child in tree.children[1:]:
            self.visit_topdown(child)

    def fun_def(self, tree):
        fun_name = tree.children[0].value

        if fun_name in self.external_functions:
            # Emit a warning if the function is already defined
            warn(f"Function {fun_name} is already defined in python. The local definition will take precedence")

        if fun_name in self.functions:
            meta = tree.meta
            error = SyntaxError(f"Identifier {fun_name} already defined")
            error.lineno = meta.line
            error.offset = meta.column
            error.end_lineno = meta.end_line
            error.end_offset = meta.end_column
            raise error

        arg_names = [arg.value for arg in tree.children[1:-1]]

        # We store the current set of variables and functions to restore it after the function definition
        self.functions.add(fun_name)

        old_variables = self.variables.copy()
        old_functions = self.functions.copy()

        self.variables.clear()
        self.variables.update(arg_names)

        self.visit(tree.children[-1])

        self.variables = old_variables.copy()
        self.functions = old_functions.copy()


        return tree