# This is a simple layer that performs some rudimentary typechecking.
# It supports the following types:
# - int
# - short
# - long
# - byte
# - float
# - double
# - bool
# - str
#
# We assume that widening conversions are allowed, but not narrowing conversions.
import lark


def depends_on():
    return set()

def typecheck(tree, annotations: dict, layer_refinements: dict):
    class Typechecker(lark.visitors.Interpreter):
        def __init__(self, variable_types):
            self.variable_types = variable_types
            self.__convertable_types = {
                "int" : {"long"},
                "short" : {"int", "long"},
                "long" : set(),
                "byte" : {"short", "int", "long"},
                "float" : {"double"},
                "double" : set(),
                "bool" : set(),
                "str" : set()
            }

        def __is_convertable(self, t1, t2):
            return t1 == t2 or t2 in self.__convertable_types[t1]

        def __is_num(self, t):
            return t in {"int", "short", "long", "byte", "float", "double"}

        def assign(self, tree):
            identifier = tree.children[0].children[0].value
            if identifier not in self.variable_types:
                raise TypeError("Type for variable {} is not defined".format(identifier))

            identifier_type = self.variable_types[identifier][-1]

            value_type = self.visit(tree.children[1])

            if not self.__is_convertable(value_type, identifier_type):
                raise TypeError("Cannot assign value of type {} to variable of type {}".format(value_type, identifier_type))

        def ident(self, tree):
            identifier = tree.children[0].value
            if identifier not in self.variable_types:
                raise TypeError("Type for variable {} is not defined".format(identifier))
            return self.variable_types[identifier][-1]

        def num(self, tree):
            return "byte"

        def true(self, tree):
            return "bool"

        def false(self, tree):
            return "bool"

        def bin_op(self, tree):
            lhs_type = self.visit(tree.children[0])
            rhs_type = self.visit(tree.children[2])

            op = tree.children[1].value

            if op in {"+", "-", "*"}:
                if self.__is_num(lhs_type) and self.__is_num(rhs_type):
                    if self.__is_convertable(lhs_type, rhs_type):
                        return rhs_type

                    return lhs_type

                raise TypeError("Cannot perform arithmetic operation on types {} and {}".format(lhs_type, rhs_type))

            if op in {"==", "!=", "<", ">", "<=", ">="}:
                if self.__is_convertable(lhs_type, rhs_type) or self.__is_convertable(rhs_type, lhs_type):
                    return "bool"

                raise TypeError("Cannot compare types {} and {}".format(lhs_type, rhs_type))

            if op in {"&&", "||"}:
                if lhs_type == "bool" and rhs_type == "bool":
                    return "bool"

                raise TypeError("Cannot perform logical operation on types {} and {}".format(lhs_type, rhs_type))


        def fun_call(self, tree):
            fun_identifier = tree.children[0].value

            if fun_identifier not in self.variable_types:
                raise TypeError("Type for function {} is not defined".format(fun_identifier))

            expected_arg_types = self.variable_types[fun_identifier][:-1]
            actual_arg_types = [self.visit(child) for child in tree.children[1:]]

            if len(expected_arg_types) != len(actual_arg_types):
                raise TypeError("Function {} expects {} arguments, but {} were given".format(fun_identifier, len(expected_arg_types), len(actual_arg_types)))

            for i in range(len(expected_arg_types)):
                if not self.__is_convertable(actual_arg_types[i],expected_arg_types[i]):
                    raise TypeError("Cannot pass argument of type {} to function {} expecting argument of type {}".format(actual_arg_types[i], fun_identifier, expected_arg_types[i]))

            return_type = self.variable_types[fun_identifier][-1]

            return return_type

        def fun_def(self, tree):
            raise NotImplementedError("Function definitions are not supported by the typechecker")

    for identifier in layer_refinements:
        refinements = layer_refinements[identifier]
        if len(refinements) > 1:
            raise TypeError("Type for variable {} is defined multiple times".format(identifier))

        if identifier not in annotations:
            annotations[identifier] = dict()

        if "type" in annotations[identifier]:
            raise TypeError("Type for variable {} was already defined by a previous layer and in the typechecking layer".format(identifier))

        annotations[identifier]["type"] = [t.strip() for t in refinements[0].split("->")]

    typechecker = Typechecker({identifier : annotations[identifier]["type"] for identifier in annotations if "type" in annotations[identifier]})

    typechecker.visit(tree)

    return tree, annotations

def parse_type(type_str : str):
    return None
