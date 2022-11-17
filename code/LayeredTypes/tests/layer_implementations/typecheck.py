import lark

from compiler.transformers.CreateAnnotatedTree import AnnotatedTree


def depends_on():
    return set()

def typecheck(tree):
    class Typechecker(lark.visitors.Interpreter):
        def __init__(self):
            self.variable_types = dict()
            self.function_types = dict()
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

        def __annotate_types(self, tree):
            if not isinstance(tree, AnnotatedTree):
                return

            for var_type in self.variable_types:
                if var_type not in tree.annotations:
                    tree.annotations[var_type] = dict()

                tree.annotations[var_type]["type"] = self.variable_types[var_type]

            for fun_type in self.function_types:
                if fun_type not in tree.annotations:
                    tree.annotations[fun_type] = dict()

                tree.annotations[fun_type]["fun_type"] = self.function_types[fun_type]

        def layer(self, tree):
            self.__annotate_types(tree)

            identifier = tree.children[0].children[0].value
            layer_name = tree.children[1].children[0].value

            if layer_name != "typecheck":
                return

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

            if identifier not in tree.annotations:
                tree.annotations[identifier] = dict()

            if dict_key in tree.annotations[identifier]:
                raise TypeError(f"Type for identifier"
                                f" {identifier} was already defined previously")

            tree.annotations[identifier][dict_key] = annotated_type


        def assign(self, tree: AnnotatedTree):
            self.__annotate_types(tree)

            identifier = tree.children[0].children[0].value
            if identifier not in self.variable_types:
                raise TypeError(f"{tree.meta.line}:{tree.meta.column}: Type for variable {identifier} is not defined")

            identifier_type = self.variable_types[identifier][-1]

            value_type = self.visit(tree.children[1])

            if not self.__is_convertable(value_type, identifier_type):
                raise TypeError(f"{tree.meta.line}:{tree.meta.column}: Cannot assign value of type {value_type} to variable of type {identifier_type}")

        def ident(self, tree):
            self.__annotate_types(tree)

            # We do not need to look up the type in the annotations, because they are equal to the variable_types
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
            self.__annotate_types(tree)

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
            self.__annotate_types(tree)

            fun_identifier = tree.children[0].value

            if fun_identifier not in tree.annotations:
                raise TypeError(f"{tree.meta.line}:{tree.meta.column}: Type for function {fun_identifier} is not defined")

            if "fun_type" not in tree.annotations[fun_identifier]:
                raise TypeError(f"{tree.meta.line}:{tree.meta.column}: Type for function {fun_identifier} is not defined")

            expected_arg_types = tree.annotations[fun_identifier]["fun_type"][:-1]
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

            return_type = tree.annotations[fun_identifier]["fun_type"][-1]

            return return_type

        def let_stmt(self, tree):
            self.__annotate_types(tree)

            identifier = tree.children[0].children[0].value

            old_type = None
            if identifier in self.variable_types:
                old_type = self.variable_types[identifier]

            self.variable_types[identifier] = self.visit(tree.children[1])

            self.visit(tree.children[2])

            if old_type is not None:
                self.variable_types[identifier] = old_type
                tree.annotations[identifier]["type"] = old_type
        def fun_def(self, tree):
            self.__annotate_types(tree)

            fun_identifier = tree.children[0].value

            if fun_identifier not in tree.annotations:
                raise TypeError(f"{tree.meta.line}:{tree.meta.column}: Type for function {fun_identifier} is not defined")

            if "fun_type" not in tree.annotations[fun_identifier]:
                raise TypeError(f"{tree.meta.line}:{tree.meta.column}: Type for function {fun_identifier} is not defined")

            expected_arg_types = tree.annotations[fun_identifier]["fun_type"][:-1]
            arg_names = [child.value for child in tree.children[1:-1]]

            if len(expected_arg_types) != len(arg_names):
                raise TypeError(f"{tree.meta.line}:{tree.meta.column}:"
                                f" Function {fun_identifier} expects {len(expected_arg_types)} "
                                f"arguments, but {len(arg_names)} were given")

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

            self.visit_children(tree)

            return tree

    typechecker = Typechecker()

    typechecker.visit(tree)

    return tree

def parse_type(type_str : str):
    return None
