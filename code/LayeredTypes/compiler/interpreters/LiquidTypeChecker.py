from copy import copy

import lark

from aeon.core.types import t_int, t_bool, t_string, RefinedType
from aeon.typing.context import EmptyContext, VariableBinder
from aeon.typing.entailment import entailment
from aeon.verification.horn import solve
from aeon.verification.sub import sub
from compiler.transformers.CreateAnnotatedTree import AnnotatedTree
from aeon.frontend.parser import mk_parser


class LiquidLayer(lark.visitors.Interpreter):
    def __init__(self):
        self.__types = {}
        self.__fun_types = {}
        self.__ctx = EmptyContext()
        pass

    def _visit_tree(self, tree):
        self.__annotate(tree)
        return super()._visit_tree(tree)

    def __annotate(self, tree):
        if not isinstance(tree, AnnotatedTree):
            tree = AnnotatedTree(tree.data, tree.children, tree.meta)

        for identifier in self.__types:
            tree.add_layer_annotation("liquid", identifier, "type", self.__types[identifier])

        for fun_identifier in self.__fun_types:
            tree.add_layer_annotation("liquid", fun_identifier, "function_type", self.__fun_types[fun_identifier])

        tree.add_layer_annotation("liquid", "contexts", "context", self.__ctx)


    def assign(self, tree: AnnotatedTree):
        lhs_type = self.visit(tree.children[0])
        rhs_type = self.visit(tree.children[1])

        c = sub(rhs_type, lhs_type)

        ctx = tree.get_layer_annotation("liquid", "contexts", "context")

        if not entailment(ctx, c):
            raise Exception("Could not assign value of type " + str(rhs_type) + " to variable of type " + str(lhs_type))

    def ident(self, tree):
        identifier = tree.children[0].value
        id_type = tree.get_layer_annotation("liquid", identifier, "type")

        if id_type is None:
            raise Exception("Could not find type for identifier " + identifier)

        return id_type

    def layer(self, tree):
        identifier = tree.children[0].children[0].value
        layer_id = tree.children[1].children[0].value

        if layer_id != "liquid":
            return

        refinement_str = [x.strip for x in tree.children[2].value.splt("->")]

        try:
            # Special case for functions that take no arguments
            if len(refinement_str) == 2 and len(refinement_str[0]) == 0 :
                refinement_str = refinement_str[1:]

            refinement_types = [mk_parser("type").parse(ref) for ref in refinement_str]
        except Exception as e:
            raise Exception("Could not parse refinement type: " + str(e))

        self.__types[identifier] = refinement_types

        # If this is a variable, add it to the current context
        if len(refinement_str) == 1:
            self.__ctx = VariableBinder(self.__ctx, identifier, refinement_types[0])


    def num(self, tree):
        return t_int

    def true(self, tree):
        return t_bool

    def false(self, tree):
        return t_bool

    def bin_op(self, tree):
        op = tree.children[1].value

        if op in {"+", "-", "*"}:
            # Possible improvement:
            # Use liquid type inference to determine a more precise type
            return t_int

        if op in {"==", "!=", "<", ">", "<=", ">="}:
            # Theoretically, we could use liquid type inference to determine
            # a more precise type
            return t_bool
    def fun_call(self, tree):
        fun_identifier = tree.children[0].value

        expected_arg_types = tree.get_layer_annotation("liquid", fun_identifier, "function_type")

        # Check that the number of arguments is correct
        if len(tree.children[1].children) != len(expected_arg_types) - 1:
            raise Exception("Incorrect number of arguments for function " + fun_identifier)

        context = tree.get_layer_annotation("liquid", "contexts", "context")
        # Check that the types of the arguments are correct
        for i in range(len(tree.children[1].children)):
            arg_type = self.visit(tree.children[1].children[i])

            if not entailment(context, sub(arg_type, expected_arg_types[i])):
                raise Exception("Incorrect type for argument " + str(i) + " of function " + fun_identifier)

            # We need to add the type of the argument to the context
            # As other refinements may reference it
            # Example for a function f that takes two arguments:
            # f :: { x: Int | x > 0 } -> { y: Int | y > x } -> { z: Int | z > y }
            assert type(arg_type) == RefinedType
            context = VariableBinder(context, "arg"+i, arg_type)


        return expected_arg_types[-1]

    def fun_def(self, tree):
        # For a function definition, we need to add the types of the arguments to the context

        # First check if we have a type definition for the function
        fun_identifier = tree.children[0].value
        fun_type = tree.get_layer_annotation("liquid", fun_identifier, "function_type")

        if fun_type is None:
            raise Exception("Could not find type for function " + fun_identifier)

        arg_names = [child.value for child in tree.children[1:-1]]

        if len(arg_names) != len(fun_type) - 1:
            raise Exception("Incorrect number of arguments for function " + fun_identifier)

        # Save the current context
        old_ctx = copy(self.__ctx)
        old_fun_types = copy(self.__fun_types)
        old_types = copy(self.__types)

        # Function definitions cannot access variables from the outer scope
        self.__ctx = EmptyContext()
        self.__types = {}

        # Add the types of the arguments to the context and types dictionary
        for i in range(len(arg_names)):
            self.__ctx = VariableBinder(self.__ctx, arg_names[i], fun_type[i])
            self.__types[arg_names[i]] = [fun_type[i]]

        # Visit the body of the function
        self.visit(tree.children[-1])

        # Restore the old context
        self.__ctx = old_ctx
        self.__fun_types = old_fun_types
        self.__types = old_types


    def let_stmt(self, tree):
        ident = tree.children[0].children[0].value

        type_expected = tree.get_layer_annotation("liquid", ident, "type")

        if type_expected is None:
            raise Exception("Could not find type for identifier " + ident)

        type_actual = self.visit(tree.children[1])


        # Save the current context
        old_ctx = copy(self.__ctx)
        old_fun_types = copy(self.__fun_types)
        old_types = copy(self.__types)

        c = sub(type_actual, type_expected)
        if not entailment(old_ctx, c):
            raise Exception(
                "Could not assign value of type " + str(type_actual) + " to variable of type " + str(type_expected))

        # TODO: Add expected or actual type to context?
        self.__ctx = VariableBinder(self.__ctx, ident, type_expected)

        # Visit the body of the let statement
        self.visit(tree.children[2])
        # Restore the context
        self.__ctx = old_ctx
        self.__fun_types = old_fun_types
        self.__types = old_types



    def custom_expr(self, tree):
        return t_string

