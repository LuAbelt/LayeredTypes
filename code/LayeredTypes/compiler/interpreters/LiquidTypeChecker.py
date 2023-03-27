from collections import Counter
from copy import copy, deepcopy
import typing as tp

import lark

from aeon.core.liquid import LiquidVar, liquid_free_vars, LiquidApp
from aeon.core.substitutions import substitution_in_type, substitution_in_liquid
from aeon.core.terms import Var
from aeon.core.types import t_int, t_bool, t_string, RefinedType
from aeon.frontend.parser import mk_parser
from aeon.typing.context import EmptyContext, VariableBinder, TypingContext
from aeon.typing.entailment import entailment
from aeon.verification.sub import sub
from aeon.verification.vcs import Conjunction
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
        fun_types[idx].name = f"$arg{idx}"
        fun_types[idx].refinement = substitution_in_liquid(fun_types[idx].refinement, LiquidVar(f"$arg{idx}"), name)
        if ref_var_names_cnt[name] == 1:
            for i in range(idx + 1, len(ref_var_names)):
                fun_types[i].refinement = substitution_in_liquid(fun_types[i].refinement, LiquidVar(f"$arg{idx}"), name)

def substitute_argument_names(arg_names: tp.List[str], arg_types: tp.List[RefinedType]):
    for i in range(len(arg_names)):
        ref_name = arg_types[i].name
        for j in range(i + 1, len(arg_names)):
            arg_types[j].refinement = substitution_in_liquid(arg_types[j].refinement, LiquidVar(arg_names[i]), ref_name)


def rename_variable(context, original_name, fun_identifier, all_arg_names, remaining_args):
    free_var_name = f"{fun_identifier}_{original_name}"
    free_var_name = make_name_unique(free_var_name, context)

    if all_arg_names.count(original_name) == 1:
        for i in range(len(remaining_args)):
            remaining_args[i] = substitution_in_type(remaining_args[i], Var(free_var_name), original_name)
    return free_var_name, remaining_args

def rename_in_context(context: TypingContext, original_name, new_name):
    if not isinstance(context, VariableBinder):
        return

    if context.name == original_name:
        context.name = new_name


    assert isinstance(context.type, RefinedType)
    context.type.refinement = substitution_in_liquid(context.type.refinement, LiquidVar(new_name), original_name)

    rename_in_context(context.prev, original_name, new_name)
def combine_contexts(original_context: TypingContext, additional_context: TypingContext, refined_type: RefinedType):
    copy_context = deepcopy(additional_context)

    def fresh_in_both(context_1: TypingContext, context_2: TypingContext):
        original_name = context_1.name
        fresh_name = original_name

        while context_1.type_of(fresh_name) or context_2.type_of(fresh_name):

            if context_1.type_of(fresh_name):
                fresh_name = make_name_unique(fresh_name, context_1)

            if context_2.type_of(fresh_name):
                fresh_name = make_name_unique(fresh_name, context_2)

        return original_name, fresh_name

    def combine_recursive(original_context: TypingContext, additional_context: TypingContext):
        if isinstance(additional_context, EmptyContext):
            return original_context, []

        # Start with the recursive call, since we want to rename the variables in the copy context
        original_context, renamings = combine_recursive(original_context, additional_context.prev)

        if isinstance(additional_context, VariableBinder):
            original_name, fresh_name = fresh_in_both(additional_context, original_context)

            additional_context.name = fresh_name
            additional_context.type.refinement = substitution_in_liquid(additional_context.type.refinement, LiquidVar(fresh_name), original_name)

            for original_name, fresh_name in renamings:
                additional_context.type.refinement = substitution_in_liquid(additional_context.type.refinement, LiquidVar(fresh_name), original_name)

            original_context = original_context.with_var(fresh_name, additional_context.type)
            renamings.append((original_name, fresh_name))

        return original_context, renamings

    original_context, _ = combine_recursive(original_context, copy_context)

    return original_context

class LiquidLayer(lark.visitors.Interpreter):
    def __init__(self, layer_identifier: str= "liquid", additional_contexts: tp.Set[str] = set()):
        self.__types = {}
        self.__fun_types = {}
        self.__ctx = EmptyContext()
        self.__layer_identifier = layer_identifier
        self.__layer_dependencies = additional_contexts
        pass

    def visit(self, tree):
        assert isinstance(tree, AnnotatedTree)

        return super().visit(tree)
    def _visit_tree(self, tree: AnnotatedTree):
        assert isinstance(tree, AnnotatedTree)
        self.__annotate(tree)

        visit_result = super()._visit_tree(tree)

        # Not every node returns a value
        # Additionally blocks return a list of values
        # These are irrelevant for the liquid layer
        if visit_result is None or isinstance(visit_result, list):
            return visit_result

        refined_type, ctx = visit_result
        
        # We want to support dependencies on previous layers
        for layer in self.__layer_dependencies:
            other_type = tree.get_layer_annotation(layer, "liquid", "type")
            
            if other_type is None:
                continue
                
            other_ctx = tree.get_layer_annotation(layer, "liquid", "context")

            # We combine the contexts
            ctx = combine_contexts(ctx, other_ctx, refined_type)

            # In the end we combine the refined predicate with the other predicate
            refined_type.refinement = LiquidApp("&&",[refined_type.refinement, other_type.refinement])
        
        # We add a layer annotation to the tree that can be used by other liquid layers
        tree.add_layer_annotation(self.__layer_identifier, "liquid", "type", refined_type)
        tree.add_layer_annotation(self.__layer_identifier, "liquid", "context", ctx)

        return refined_type, ctx

    def __annotate(self, tree):
        assert isinstance(tree, AnnotatedTree)

        for identifier in self.__types:
            tree.add_layer_annotation(self.__layer_identifier, identifier, "type", self.__types[identifier])

        for fun_identifier in self.__fun_types:
            tree.add_layer_annotation(self.__layer_identifier, fun_identifier, "function_type", self.__fun_types[fun_identifier])

        tree.add_layer_annotation(self.__layer_identifier, "liquid", "context", self.__ctx)


    def assign(self, tree: AnnotatedTree):
        raise FeatureNotSupportedError("Assignments are not supported in the liquid layer. Only let bindings are supported.", tree.meta.line, tree.meta.column)

    def ident(self, tree):
        identifier = tree.children[0].value

        # Try to get the type from context if it has already been assigned
        ctx = tree.get_layer_annotation(self.__layer_identifier, "liquid", "context")

        id_type = ctx.type_of(identifier)

        if id_type is None:
            # Type has not been assigned yet, try to get it from the types dictionary
            id_type = tree.get_layer_annotation(self.__layer_identifier, identifier, "type")

        if id_type is None:
            # Type is still undefined, raise an error
            raise LiquidTypeUndefinedError(identifier, tree.meta.line, tree.meta.column)

        return id_type, ctx

    def layer(self, tree):
        identifier = tree.children[0].children[0].value
        layer_id = tree.children[1].children[0].value

        if layer_id != self.__layer_identifier:
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
        return mk_parser("type").parse("{v:Int | v == "+tree.children[0].value+" }"), tree.get_layer_annotation(self.__layer_identifier, "liquid", "context")

    def true(self, tree):
        return mk_parser("type").parse("{v:Bool | v }")\
            , tree.get_layer_annotation(self.__layer_identifier, "liquid", "context")

    def false(self, tree):
        return mk_parser("type").parse("{v:Bool | v }")\
               , tree.get_layer_annotation(self.__layer_identifier, "liquid", "context")

    def bin_op(self, tree):
        op = tree.children[1].value

        lhs_type, ctx = self.visit(tree.children[0])

        lhs_name = make_name_unique("bin_op_lhs", ctx)
        self.__ctx = ctx.with_var(lhs_name, lhs_type)

        rhs_type, ctx = self.visit(tree.children[2])

        rhs_name = make_name_unique("bin_op_rhs", ctx)
        ctx = ctx.with_var(rhs_name, rhs_type)
        self.__ctx = ctx

        # Limitation: We only support integer operations
        if not (lhs_type.type == t_int and rhs_type.type == t_int):
            raise TypecheckException("Expected both operands to be integers", tree.meta.line, tree.meta.column)
        name = make_name_unique("bin_op_result", ctx)

        if op in {"+", "-", "*"}:
            return_base_type = "Int"

        if op in {"==", "!=", "<", ">", "<=", ">="}:
            return_base_type = "Bool"

        return mk_parser("type").parse(f"{{ {name}:{return_base_type} | {name} == ( {lhs_name} {op} {rhs_name} ) }}"), ctx
    def fun_call(self, tree):
        fun_identifier = tree.children[0].value

        expected_arg_types = tree.get_layer_annotation(self.__layer_identifier, fun_identifier, "function_type")

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

        context = tree.get_layer_annotation(self.__layer_identifier, "liquid", "context")
        all_arg_names = [x.name for x in expected_arg_types]
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
            free_var_name, expected_arg_types[i+1:] = rename_variable(context, original_name, fun_identifier,
                                                                      all_arg_names , expected_arg_types[i+1:])

            context = context.with_var(free_var_name, arg_type)
            self.__ctx = context

        return expected_arg_types[-1], context

    def fun_def(self, tree):
        # For a function definition, we need to add the types of the arguments to the context

        # First check if we have a type definition for the function
        fun_identifier = tree.children[0].value
        # We want to explicitly copy the function type, as we will modify it
        # If we wouldn't copy it this would have implications when calling the function
        fun_type = deepcopy(tree.get_layer_annotation(self.__layer_identifier, fun_identifier, "function_type"))

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
        substitute_argument_names(arg_names, fun_type)

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

        type_expected = tree.get_layer_annotation(self.__layer_identifier, ident, "type")

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
        return t_string, self.__ctx

