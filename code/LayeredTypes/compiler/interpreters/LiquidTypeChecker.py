from copy import copy

import lark

from aeon.core.liquid import LiquidLiteralInt, LiquidLiteralBool, LiquidVar
from aeon.core.substitutions import substitution_in_type
from aeon.core.terms import Var
from aeon.core.types import t_int, t_bool, t_string, RefinedType
from aeon.frontend.parser import mk_parser
from aeon.typing.context import EmptyContext, VariableBinder
from aeon.typing.entailment import entailment
from aeon.verification.sub import sub
from compiler.Exceptions import TypecheckException, WrongArgumentCountException, FeatureNotSupportedError
from compiler.transformers.CreateAnnotatedTree import AnnotatedTree, make_annotated_tree

class LiquidSubtypeException(TypecheckException):
    """Exception that will be raised when during liquid typechecking a subtype check fails.

    Attributes:
        left_type -- the left type of the subtype check
        right_type -- the right type of the subtype check
        context -- the context in which the subtype check failed
    """
    def __init__(self, msg, left_type, right_type, context, line, column):
        self.left_type = left_type
        self.right_type = right_type
        self.context = context
        super().__init__(f"{msg}:\n{left_type} is not a subtype of {right_type} (Context: {context})", line, column)
        pass

class LiquidTypeUndefinedError(TypecheckException):
    """Exception that will be raised when during liquid typechecking a type is undefined.

    Attributes:
        identifier -- the identifier that is undefined
    """
    def __init__(self, identifier, line, column):
        self.identifier = identifier
        super().__init__(f"Type of identifier {identifier} is undefined", line, column)
        pass

class LiquidLayer(lark.visitors.Interpreter):
    def __init__(self):
        self.__types = {}
        self.__fun_types = {}
        self.__ctx = EmptyContext()
        pass

    def visit(self, tree):
        if not isinstance(tree, AnnotatedTree):
            tree = make_annotated_tree(tree)

        return super().visit(tree)
    def _visit_tree(self, tree):
        self.__annotate(tree)
        return super()._visit_tree(tree)

    def __annotate(self, tree):

        for identifier in self.__types:
            tree.add_layer_annotation("liquid", identifier, "type", self.__types[identifier])

        for fun_identifier in self.__fun_types:
            tree.add_layer_annotation("liquid", fun_identifier, "function_type", self.__fun_types[fun_identifier])

        tree.add_layer_annotation("liquid", "contexts", "context", self.__ctx)


    def assign(self, tree: AnnotatedTree):
        raise FeatureNotSupportedError("Assignments are not supported in the liquid layer. Only let bindings are supported.", tree.meta.line, tree.meta.column)

        lhs_type = self.visit(tree.children[0])
        rhs_type, rhs_ctx = self.visit(tree.children[1])

        c = sub(rhs_type, lhs_type)

        ctx = tree.get_layer_annotation("liquid", "contexts", "context")

        if rhs_ctx:
            ctx = rhs_ctx

        if not entailment(ctx, c):
            raise Exception("Could not assign value of type " + str(rhs_type) + " to variable of type " + str(lhs_type))

        # Update the context and types
        ctx = VariableBinder(ctx, tree.children[0].children[0].value, rhs_type)
        self.__ctx = ctx
        self.__types[tree.children[0].children[0].value] = rhs_type

    def ident(self, tree):
        identifier = tree.children[0].value
        id_type = tree.get_layer_annotation("liquid", identifier, "type")

        if id_type is None:
            raise LiquidTypeUndefinedError(identifier, tree.meta.line, tree.meta.column)

        return id_type, tree.get_layer_annotation("liquid", "contexts", "context")

    def layer(self, tree):
        identifier = tree.children[0].children[0].value
        layer_id = tree.children[1].children[0].value

        if layer_id != "liquid":
            return

        refinement_str = [x.strip() for x in tree.children[2].value.split("->")]

        is_fn = len(refinement_str) > 1
        try:
            # Special case for functions that take no arguments
            if len(refinement_str) == 2 and len(refinement_str[0]) == 0 :
                refinement_str = refinement_str[1:]

            refinement_types = [mk_parser("type").parse(ref) for ref in refinement_str]
        except Exception as e:
            raise TypecheckException("Could not parse refinement type: " + str(e), tree.meta.line, tree.meta.column)

        if is_fn:
            self.__fun_types[identifier] = refinement_types
        else:
            self.__types[identifier] = refinement_types[0]



    def num(self, tree):
        return mk_parser("type").parse("{v:Int | v == "+tree.children[0].value+" }"), tree.get_layer_annotation("liquid", "contexts", "context")

    def true(self, tree):
        return mk_parser("type").parse("{v:Bool | v }")\
            , tree.get_layer_annotation("liquid", "contexts", "context")

    def false(self, tree):
        return mk_parser("type").parse("{v:Bool | v }")\
               , tree.get_layer_annotation("liquid", "contexts", "context")

    def bin_op(self, tree):
        op = tree.children[1].value

        if op in {"+", "-", "*"}:
            # Possible improvement:
            # Use liquid type inference to determine a more precise type, like
            # Where we need to ensure that left and right have the same base type
            # {v:Base | v == left + right}
            return t_int, tree.get_layer_annotation("liquid", "contexts", "context")

        if op in {"==", "!=", "<", ">", "<=", ">="}:
            # Theoretically, we could use liquid type inference to determine
            # a more precise type
            return t_bool, tree.get_layer_annotation("liquid", "contexts", "context")
    def fun_call(self, tree):
        fun_identifier = tree.children[0].value

        expected_arg_types = tree.get_layer_annotation("liquid", fun_identifier, "function_type")
        actual_num_args = len(tree.children) - 1

        # Check that the number of arguments is correct
        if actual_num_args != len(expected_arg_types) - 1:
            raise WrongArgumentCountException(fun_identifier,
                                              len(expected_arg_types) - 1,
                                              actual_num_args,
                                              tree.meta.line,
                                              tree.meta.column)

        context = tree.get_layer_annotation("liquid", "contexts", "context")
        # Check that the types of the arguments are correct
        for i in range(actual_num_args):
            arg_type, context = self.visit(tree.children[i+1])
            c = sub(arg_type, expected_arg_types[i])

            if not entailment(context, c):
                raise LiquidSubtypeException(arg_type, expected_arg_types[i], tree.meta.line, tree.meta.column)

            # We need to add the type of the argument to the context
            # As other refinements may reference it
            # To ensure uniqueness, we rename the variable
            assert type(arg_type) == RefinedType
            original_name = expected_arg_types[i].name
            free_var_name = f"{fun_identifier}_{original_name}"
            if context.type_of(free_var_name) is not None:
                p = 1
                while context.type_of(f"{free_var_name}_{p}") is not None:
                    p += 1
                free_var_name = f"{free_var_name}_{p}"

            # We need to rename the variable in all the refinements for the remaining arguments
            for j in range(i+1, len(expected_arg_types)):
                expected_arg_types[j] = substitution_in_type(expected_arg_types[j], Var(free_var_name), original_name)

            context = context.with_var(free_var_name, arg_type)

        return expected_arg_types[-1], context

    def fun_def(self, tree):
        # For a function definition, we need to add the types of the arguments to the context

        # First check if we have a type definition for the function
        fun_identifier = tree.children[0].value
        fun_type = tree.get_layer_annotation("liquid", fun_identifier, "function_type")

        if fun_type is None:
            raise LiquidTypeUndefinedError(fun_identifier, tree.meta.line, tree.meta.column)

        arg_names = [child.value for child in tree.children[1:-1]]

        if len(arg_names) != len(fun_type) - 1:
            raise WrongArgumentCountException(fun_identifier,
                                              len(fun_type) - 1,
                                              len(arg_names),
                                              tree.meta.line,
                                              tree.meta.column)

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
            self.__types[arg_names[i]] = fun_type[i]

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
            raise LiquidTypeUndefinedError(ident, tree.meta.line, tree.meta.column)

        type_actual, context = self.visit(tree.children[1])


        # Save the current context
        old_ctx = copy(self.__ctx)
        old_fun_types = copy(self.__fun_types)
        old_types = copy(self.__types)

        c = sub(type_actual, type_expected)
        if not entailment(context, c):
            raise LiquidSubtypeException(f"Error during assigning identifier '{ident}' in let statement",
                                         type_actual,
                                         type_expected,
                                         context,
                                         tree.meta.line,
                                         tree.meta.column)

        # TODO: Add expected or actual type to context?
        self.__ctx = context.with_var(ident, type_actual)

        # Visit the body of the let statement
        self.visit(tree.children[2])

        # Restore the original context
        self.__ctx = old_ctx
        self.__fun_types = old_fun_types
        self.__types = old_types



    def custom_expr(self, tree):
        return t_string

