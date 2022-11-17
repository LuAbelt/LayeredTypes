from warnings import warn

import lark


class CheckCF(lark.visitors.Interpreter):
    def __init__(self):
        super().__init__()
        self.identifiers = set()

    def assign(self, tree):
        # We first check the right hand side of the assignment
        # This is to detect if the identifier is used before it is defined
        self.visit(tree.children[1])

        # Add defined identifier to set
        identifier = tree.children[0].children[0].value
        self.identifiers.add(identifier)

    def layer(self, tree):
        # We explicitly ignore the layer definitions as they have no effect on the control flow
        pass

    def let_stmt(self, tree):
        identifier = tree.children[0].children[0].value

        if identifier in self.identifiers:
            meta = tree.children[0].meta
            error = SyntaxError(f"Identifier {identifier} already defined")
            error.lineno = meta.line
            error.offset = meta.column
            error.end_lineno = meta.end_line
            error.end_offset = meta.end_column
            raise error

        # We add the identifier to the set only for the duration of the let construct
        self.identifiers.add(identifier)

        self.visit(tree.children[2])

        self.identifiers.discard(identifier)

    def ident(self, tree):
        identifier = tree.children[0].value
        if identifier not in self.identifiers:
            meta = tree.meta
            error = SyntaxError(f"Identifier {identifier} not defined")
            error.lineno = meta.line
            error.offset = meta.column
            error.end_lineno = meta.end_line
            error.end_offset = meta.end_column
            raise error

    def fun_call(self, tree):
        fun_name = tree.children[0].value

        if fun_name not in self.identifiers:
            # Emit a warning if the function is not defined
            warn(f"Function {fun_name} not defined in this scope. It needs to be defined in Python", RuntimeWarning)

        for child in tree.children[1:]:
            self.visit_topdown(child)

    def fun_def(self, tree):
        fun_name = tree.children[0].value

        if fun_name in self.identifiers:
            raise RuntimeError(f"Identifier {fun_name} already defined")

        arg_names = [arg.value for arg in tree.children[1:-1]]

        # We add the the argument names to the set only for the duration of the function definition
        self.identifiers.add(fun_name)
        self.identifiers.update(arg_names)

        self.visit(tree.children[-1])

        self.identifiers.difference_update(arg_names)
        # After definition, we keep the function name in the set as it can be used as a function

        return tree