import lark
import igraph

from compiler.Exceptions import TypecheckException, WrongArgumentCountException
from compiler.transformers.CreateAnnotatedTree import AnnotatedTree


def depends_on():
    return {"types"}

def typecheck(tree):
    class Typechecker(lark.visitors.Interpreter):
        def __init__(self):
            self.__subtype_graph = igraph.Graph(2, directed=True)
            self.__type_ids = {"__num":0,"__logical":1}

        def __add_type_to_graph(self, t):
            if t not in self.__type_ids:
                self.__type_ids[t] = len(self.__type_ids)
                self.__subtype_graph.add_vertex(1)

        def __add_subtype(self, t1, t2):
            if t1 not in self.__type_ids or t2 not in self.__type_ids:
                return

            if self.__subtype_graph.are_connected(self.__type_ids[t1], self.__type_ids[t2]):
                return

            self.__subtype_graph.add_edge(self.__type_ids[t1], self.__type_ids[t2])

        def __is_convertable(self, t1, t2):
            if t1 == t2:
                return True

            # Special handling for assignment of num literals
            if t1 == "__num":
                return self.__is_convertable(t2, "__num")

            # Special handling for assignment of logical literals
            if t1 == "__logical":
                return self.__is_convertable(t2, "__logical")

            if t1 not in self.__type_ids or t2 not in self.__type_ids:
                return False

            d = self.__subtype_graph.distances(self.__type_ids[t1], self.__type_ids[t2])
            return d != [[float("inf")]]

        def __is_num(self, t):
            if t not in self.__type_ids:
                return False
            return self.__is_convertable(t, "__num")


        def assign(self, tree: AnnotatedTree):
            identifier = tree.children[0].children[0].value

            identifier_type = tree.get_layer_annotation("types",identifier, "type")

            if identifier_type is None:
                raise TypecheckException(f"No type defined for '{identifier}'.", tree.meta.line, tree.meta.column)

            identifier_type = identifier_type[-1]

            value_type = self.visit(tree.children[1])

            if not self.__is_convertable(value_type, identifier_type):
                raise TypecheckException(f"Cannot assign value of type {value_type} to variable of type {identifier_type}", tree.meta.line, tree.meta.column)

        def ident(self, tree):
            # We do not need to look up the type in the annotations, because they are equal to the variable_types
            identifier = tree.children[0].value

            variable_types = tree.get_layer_annotation("types",identifier, "type")

            if variable_types is None:
                raise TypecheckException(f"Type for variable '{identifier}' is not defined", tree.meta.line, tree.meta.column)

            return variable_types[-1]

        def layer(self, tree):
            argument = tree.children[0].children[0].value
            layer_id = tree.children[1].children[0].value

            if layer_id != "typecheck":
                return

            typecheck_str = tree.children[2].value

            if argument == "numTypes":
                types = typecheck_str.split()

                for t in types:
                    self.__add_type_to_graph(t)
                    self.__add_subtype(t, "__num")

            if argument == "logicalTypes":
                types = typecheck_str.split()

                for t in types:
                    self.__add_type_to_graph(t)
                    self.__add_subtype(t, "__logical")

            if argument == "subtype":
                subtypes = [t.strip() for t in typecheck_str.split("<:")]

                if len(subtypes) < 2:
                    raise TypecheckException(f"Invalid subtyping definition", tree.meta.line, tree.meta.column)

                self.__add_type_to_graph(subtypes[0])
                for i in range(1, len(subtypes)):
                    self.__add_type_to_graph(subtypes[i])
                    self.__add_subtype(subtypes[i-1], subtypes[i])
                pass

        def num(self, tree):
            return "__num"

        def true(self, tree):
            return "__logical"

        def false(self, tree):
            return "__logical"

        def bin_op(self, tree):
            lhs_type = self.visit(tree.children[0])
            rhs_type = self.visit(tree.children[2])

            op = tree.children[1].value

            if op in {"+", "-", "*"}:
                if self.__is_num(lhs_type) and self.__is_num(rhs_type):
                    if self.__is_convertable(lhs_type, rhs_type):
                        return rhs_type

                    return lhs_type

                raise TypecheckException(f"Cannot perform arithmetic operation on types {lhs_type} and {rhs_type}", tree.meta.line, tree.meta.column)

            if op in {"==", "!=", "<", ">", "<=", ">="}:
                if self.__is_convertable(lhs_type, rhs_type) or self.__is_convertable(rhs_type, lhs_type):
                    return "__logical"

                raise TypecheckException(f"Cannot compare types {lhs_type} and {rhs_type}", tree.meta.line, tree.meta.column)

            if op in {"&&", "||"}:
                if self.__is_convertable(lhs_type, "__logical") and self.__is_convertable(rhs_type, "__logical"):
                    return "__logical"

                raise TypecheckException(f"Cannot perform logical operation on types {lhs_type} and {rhs_type}", tree.meta.line, tree.meta.column)

        def fun_call(self, tree):
            fun_identifier = tree.children[0].value

            fun_types = tree.get_layer_annotation("types",fun_identifier,"fun_type")

            if fun_types is None:
                raise TypecheckException(f"Type for function {fun_identifier} is not defined", tree.meta.line, tree.meta.column)

            expected_arg_types = fun_types[:-1]
            actual_arg_types = [self.visit(child) for child in tree.children[1:]]

            if len(expected_arg_types) != len(actual_arg_types):
                raise WrongArgumentCountException(fun_identifier, len(expected_arg_types), len(actual_arg_types) , tree.meta.line, tree.meta.column)

            for i in range(len(expected_arg_types)):
                if not self.__is_convertable(actual_arg_types[i],expected_arg_types[i]):
                    raise TypecheckException(f"Cannot pass argument of type {actual_arg_types[i]}"
                                    f" to function {fun_identifier} expecting argument of"
                                    f" type {expected_arg_types[i]}", tree.meta.line, tree.meta.column)

            return_type = fun_types[-1]

            return return_type

        def let_stmt(self, tree):
            identifier = tree.children[0].children[0].value

            variable_types = tree.get_layer_annotation("types",identifier,"type")

            if variable_types is None:
                raise TypecheckException(f"Type for variable {identifier} is not defined", tree.meta.line, tree.meta.column)

            value_type = self.visit(tree.children[1])

            identifier_type = variable_types[-1]

            if not self.__is_convertable(value_type, identifier_type):
                raise TypecheckException(f"Cannot assign value of type {value_type} to variable of type {identifier_type}", tree.meta.line, tree.meta.column)

            self.visit(tree.children[2])

        def if_stmt(self, tree):
            condition_type = self.visit(tree.children[0])

            if not self.__is_convertable(condition_type, "__logical"):
                raise TypecheckException(f"Condition of if statement must be of type bool", tree.meta.line, tree.meta.column)

            self.visit(tree.children[1])

            if len(tree.children) > 2:
                self.visit(tree.children[2])

        def custom_expr(self, tree):
            # Temporary workaround until proper custom expression support is added
            return "string"

    typechecker = Typechecker()

    typechecker.visit(tree)

    return tree

def parse_type(type_str : str):
    return None
