import lark

from compiler.Exceptions import TypecheckException, WrongArgumentCountException
from compiler.transformers.CreateAnnotatedTree import AnnotatedTree


def depends_on():
    return set()

def typecheck(tree):
    class TypeAnnotator(lark.visitors.Interpreter):
        def __init__(self):
            self.variable_types = dict()
            self.function_types = dict()

        def __annotate_types(self, tree):
            if not isinstance(tree, AnnotatedTree):
                tree = AnnotatedTree(tree.data,tree.children,tree.meta)

            for var_type in self.variable_types:
                tree.add_layer_annotation("types",var_type,"type",self.variable_types[var_type])

            for fun_type in self.function_types:
                tree.add_layer_annotation("types",fun_type,"fun_type",self.function_types[fun_type])

        def layer(self, tree):
            self.__annotate_types(tree)

            identifier = tree.children[0].children[0].value
            layer_name = tree.children[1].children[0].value

            if layer_name != "types":
                return tree

            type_str = tree.children[2].value

            annotated_type = [t.strip() for t in type_str.split("->")]

            dict_key = "type"

            if len(annotated_type) > 1:
                dict_key = "fun_type"
                # Special handling for functions without arguments
                if annotated_type[0] == '':
                    annotated_type = annotated_type[1:]
                self.function_types[identifier] = annotated_type
            else:
                self.variable_types[identifier] = annotated_type

            if tree.get_layer_annotation(layer_name,identifier,dict_key) is not None:
                raise TypecheckException(f"Type for identifier"
                                f" {identifier} was already defined previously", tree.meta.line, tree.meta.column)

        def fun_def(self, tree):
            self.__annotate_types(tree)

            fun_identifier = tree.children[0].value

            fun_type = tree.get_layer_annotation("types",fun_identifier,"fun_type")

            if fun_type is None:
                raise TypecheckException(f" Function {fun_identifier} has no defined type.", tree.meta.line, tree.meta.column)

            expected_arg_types = fun_type[:-1]
            arg_names = [child.value for child in tree.children[1:-1]]

            if len(expected_arg_types) != len(arg_names):
                raise WrongArgumentCountException(fun_identifier,len(expected_arg_types),len(arg_names), tree.meta.line, tree.meta.column)

            # Store the old variable types as local variables may shadow global variables
            old_frame = self.variable_types.copy()
            old_function_frame = self.function_types.copy()

            self.variable_types.clear()
            for i in range(len(expected_arg_types)):
                self.variable_types[arg_names[i]] = [expected_arg_types[i]]

            self.visit(tree.children[-1])

            self.variable_types = old_frame.copy()
            self.function_types = old_function_frame.copy()

        def __default__(self, tree):
            self.__annotate_types(tree)
            return super().__default__(tree)

    annotator = TypeAnnotator()
    annotator.visit(tree)

    return tree

def parse_type(type_str):
    return type_str