import lark

from aeon.core.types import t_int, t_bool, t_string
from aeon.verification.horn import solve
from aeon.verification.sub import sub
from compiler.transformers.CreateAnnotatedTree import AnnotatedTree
from aeon.frontend.parser import mk_parser


class LiquidTypechecker(lark.visitors.Interpreter):
    def __init__(self):
        self.__types = {}
        pass

    def _visit_tree(self, tree):
        self.__annotate_states(tree)
        return super()._visit_tree(tree)

    def __annotate_states(self, tree):
        if not isinstance(tree, AnnotatedTree):
            tree = AnnotatedTree(tree.data, tree.children, tree.meta)

        for identifier in self.__states:
            tree.add_layer_annotation("liquid", identifier, "TODO", self.__states[identifier])

        for fun_identifier in self.__function_states:
            tree.add_layer_annotation("liquid", fun_identifier, "type",
                                      self.__function_states[fun_identifier])

    def assign(self, tree: AnnotatedTree):
        lhs_type = self.visit(tree.children[0])
        rhs_type = self.visit(tree.children[1])

        c = sub(rhs_type, lhs_type)

        if not solve(c):
            raise Exception("Type error")

    def ident(self, tree):
        pass

    def layer(self, tree):
        identifier = tree.children[0].children[0].value
        layer_id = tree.children[1].children[0].value

        if layer_id != "liquid":
            return

        refinement_str = tree.children[2].value

        parser = mk_parser("type")

        refinement = parser.parse(refinement_str)
        self.__types[identifier] = refinement

    def num(self, tree):
        return t_int

    def true(self, tree):
        return t_bool

    def false(self, tree):
        return t_bool

    def bin_op(self, tree):
        pass
    def fun_call(self, tree):
        fun_identifier = tree.children[0].value

    def let_stmt(self, tree):
        identifier = tree.children[0].children[0].value

    def if_stmt(self, tree):
        pass

    def custom_expr(self, tree):
        return t_string

