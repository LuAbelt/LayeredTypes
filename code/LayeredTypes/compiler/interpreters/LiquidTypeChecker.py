from collections import Counter
from copy import copy
import typing as tp

import lark

from aeon.core.liquid import LiquidLiteralInt, LiquidLiteralBool, LiquidVar, liquid_free_vars
from aeon.core.substitutions import substitution_in_type
from aeon.core.terms import Var
from aeon.core.types import t_int, t_bool, t_string, RefinedType
from aeon.frontend.parser import mk_parser
from aeon.typing.context import EmptyContext, VariableBinder, TypingContext
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
    def __init__(self, msg, type_actual, type_expected, context, line, column):
        self.type_actual = type_actual
        self.type_expected = type_expected
        self.context = context
        super().__init__(f"{msg}:\n{type_actual} is not a subtype of {type_expected} (Context: {context})", line, column)
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

class LiquidFunctionDefinitionError(TypecheckException):
    """Exception that will be raised when during liquid typechecking a function definition is invalid.

    Attributes:
        identifier -- the identifier that is undefined
    """
    def __init__(self, fun_name, argument_type, argument_idx, duplicate_var, line, column):
        self.argument_type = argument_type
        self.argument_idx = argument_idx
        self.duplicate_var = duplicate_var
        self.fun_name = fun_name

        super().__init__(f"Function definition for {fun_name}:\rInvalid refinement at index {argument_idx}: {argument_idx}. (References non-unique variable {duplicate_var})", line, column)
        pass

def make_name_unique(name :str, context :TypingContext) -> str:
    """Makes a name unique by appending a number to it.

    Args:
        name (str): The name to make unique
        context (TypingContext): The context in which the name should be unique

    Returns:
        str: The unique name
    """
    if context.type_of(name) is not None:
        p = 1
        while context.type_of(f"{name}_{p}") is not None:
            p += 1
        name = f"{name}_{p}"

    return name


def substitute_refinement_names(fun_types: tp.List[RefinedType]):
    ref_var_names = [var.name for var in fun_types[:-1]]
    ref_var_names_cnt = Counter(ref_var_names)
    # We rename the variables in the refinements of the arguments
    for idx, name in enumerate(ref_var_names):
        fun_types[idx] = substitution_in_type(fun_types[idx], Var(f"$arg{idx}"), name)
        if ref_var_names_cnt[name] == 1:
            for i in range(idx + 1, len(ref_var_names)):
                fun_types[i] = substitution_in_type(fun_types[i], Var(f"$arg{idx}"), name)

    return fun_types

def substitute_argument_names(arg_names: tp.List[str], arg_types: tp.List[RefinedType]):
    for i in range(len(arg_names)):
        ref_name = arg_types[i].name
        for j in range(i + 1, len(arg_names)):
            arg_types[j] = substitution_in_type(arg_types[j], arg_names[i], ref_name)

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

    def ident(self, tree):
        identifier = tree.children[0].value

        # Try to get the type from context if it has already been assigned
        ctx = tree.get_layer_annotation("liquid", "contexts", "context")

        id_type = ctx.type_of(identifier)

        if id_type is None:
            # Type has not been assigned yet, try to get it from the types dictionary
            id_type = tree.get_layer_annotation("liquid", identifier, "type")

        if id_type is None:
            # Type is still undefined, raise an error
            raise LiquidTypeUndefinedError(identifier, tree.meta.line, tree.meta.column)

        return id_type, ctx

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

            refinement_var_counts = Counter([x.name for x in refinement_types])
            for i, ref in enumerate(refinement_types):
                for var in liquid_free_vars(ref.refinement):
                    if var == ref.name:
                        # We ignore the variable that is bound by the refinement
                        continue
                    if refinement_var_counts[var] > 1:
                        raise LiquidFunctionDefinitionError(identifier, ref, i, var, tree.meta.line, tree.meta.column)

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

        if expected_arg_types is None:
            raise LiquidTypeUndefinedError(fun_identifier, tree.meta.line, tree.meta.column)

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
                raise LiquidSubtypeException( f"Error in function call to {fun_identifier}, argument {i+1}",
                                             arg_type,
                                             expected_arg_types[i],
                                             context,
                                             tree.meta.line,
                                             tree.meta.column)

            # We need to add the type of the argument to the context
            # As other refinements may reference it
            # To ensure uniqueness, we rename the variable
            assert type(arg_type) == RefinedType
            original_name = expected_arg_types[i].name
            free_var_name = f"{fun_identifier}_{original_name}"
            free_var_name = make_name_unique(free_var_name, context)

            # We need to rename the variable in all the refinements for the remaining arguments
            # TODO: Differentiate cases where different arguments use the same variable name
            # This is possible as long as the variable is not referenced in another refinement
            for j in range(i+1, len(expected_arg_types)):
                expected_arg_types[j] = substitution_in_type(expected_arg_types[j], Var(free_var_name), original_name)

            context = context.with_var(free_var_name, arg_type)
            self.__ctx = context

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

        substitute_refinement_names(fun_type)

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

        self.__ctx = context.with_var(ident, type_actual)

        # Visit the body of the let statement
        self.visit(tree.children[2])

        # Restore the original context
        self.__ctx = old_ctx
        self.__fun_types = old_fun_types
        self.__types = old_types

    def custom_expr(self, tree):
        return t_string

