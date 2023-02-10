import lark

from compiler.transformers.CreateAnnotatedTree import AnnotatedTree



class LiquidTypechecker(lark.visitors.Interpreter):
    def __init__(self):
        pass

    def __default__(self, tree):
        self.visit_children(tree)
        # TODO: Default return value?

    def _visit_tree(self, tree):
        self.__annotate_states(tree)
        return super()._visit_tree(tree)

    def __annotate_states(self, tree):
        if not isinstance(tree, AnnotatedTree):
            tree = AnnotatedTree(tree.data, tree.children, tree.meta)

        for identifier in self.__states:
            tree.add_layer_annotation("liquid", identifier, "TODO", self.__states[identifier])

        for fun_identifier in self.__function_states:
            tree.add_layer_annotation("liquid", fun_identifier, "TODO",
                                      self.__function_states[fun_identifier])

    def assign(self, tree: AnnotatedTree):
        pass

    def ident(self, tree):
        pass

    def layer(self, tree):
        identifier = tree.children[0].children[0].value
        layer_id = tree.children[1].children[0].value

        if layer_id != "liquid":
            return

        refinement_str = tree.children[2].value



    def num(self, tree):
        pass

    def true(self, tree):
        pass

    def false(self, tree):
        pass

    def bin_op(self, tree):
        pass
    def fun_call(self, tree):
        fun_identifier = tree.children[0].value

    def let_stmt(self, tree):
        identifier = tree.children[0].children[0].value

    def if_stmt(self, tree):
        pass

    def custom_expr(self, tree):
        # Temporary workaround until proper custom expression support is added
        return "string"

