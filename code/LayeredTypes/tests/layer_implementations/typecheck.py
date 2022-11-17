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

        def assign(self, tree: lark.Tree):
            identifier = tree.children[0].children[0].value
            if identifier not in self.variable_types:
                raise TypeError(f"{tree.meta.line}:{tree.meta.column}: Type for variable {identifier} is not defined")

            identifier_type = self.variable_types[identifier][-1]

            value_type = self.visit(tree.children[1])

            if not self.__is_convertable(value_type, identifier_type):
                raise TypeError(f"{tree.meta.line}:{tree.meta.column}: Cannot assign value of type {value_type} to variable of type {identifier_type}")

        def ident(self, tree):
            identifier = tree.children[0].value
            if identifier not in self.variable_types:
                raise TypeError(f"{tree.meta.line}:{tree.meta.column}: Type for variable '{identifier}' is not defined")
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

                raise TypeError(f"{tree.meta.line}:{tree.meta.column}: Cannot perform arithmetic operation on types {lhs_type} and {rhs_type}")

            if op in {"==", "!=", "<", ">", "<=", ">="}:
                if self.__is_convertable(lhs_type, rhs_type) or self.__is_convertable(rhs_type, lhs_type):
                    return "bool"

                raise TypeError(f"{tree.meta.line}:{tree.meta.column}: Cannot compare types {lhs_type} and {rhs_type}")

            if op in {"&&", "||"}:
                if lhs_type == "bool" and rhs_type == "bool":
                    return "bool"

                raise TypeError(f"{tree.meta.line}:{tree.meta.column}: Cannot perform logical operation on types {lhs_type} and {rhs_type}")


        def fun_call(self, tree):
            fun_identifier = tree.children[0].value

            if fun_identifier not in self.variable_types:
                raise TypeError(f"{tree.meta.line}:{tree.meta.column}: Type for function {fun_identifier} is not defined")

            expected_arg_types = self.variable_types[fun_identifier][:-1]
            actual_arg_types = [self.visit(child) for child in tree.children[1:]]

            if len(expected_arg_types) != len(actual_arg_types):
                raise TypeError(f"{tree.meta.line}:{tree.meta.column}:"
                                f" Function {fun_identifier} expects {len(expected_arg_types)} "
                                f"arguments, but {len(actual_arg_types)} were given")

            for i in range(len(expected_arg_types)):
                if not self.__is_convertable(actual_arg_types[i],expected_arg_types[i]):
                    raise TypeError(f"{tree.meta.line}:{tree.meta.column}: "
                                    f"Cannot pass argument of type {actual_arg_types[i]}"
                                    f" to function {fun_identifier} expecting argument of"
                                    f" type {expected_arg_types[i]}")

            return_type = self.variable_types[fun_identifier][-1]

            return return_type

        def fun_def(self, tree):
            raise NotImplementedError("Function definitions are not supported by the typechecker")

    for identifier in layer_refinements:
        refinements = layer_refinements[identifier]
        if len(refinements) > 1:
            raise TypeError(f"{tree.meta.line}:{tree.meta.column}: "
                            f"Type for variable {identifier} is defined multiple times")

        if identifier not in annotations:
            annotations[identifier] = dict()

        if "type" in annotations[identifier]:
            raise TypeError(f"{tree.meta.line}:{tree.meta.column}: Type for variable"
                            f" {identifier} was already defined by a previous layer "
                            f"and in the typechecking layer")

        annotations[identifier]["type"] = [t.strip() for t in refinements[0].split("->")]

    typechecker = Typechecker({identifier : annotations[identifier]["type"] for identifier in annotations if "type" in annotations[identifier]})

    typechecker.visit(tree)

    return tree, annotations

def parse_type(type_str : str):
    return None
