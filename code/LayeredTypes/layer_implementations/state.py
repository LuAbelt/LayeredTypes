import re
from collections import defaultdict
from copy import copy

import lark.visitors

from compiler.Exceptions import TypecheckException, WrongArgumentCountException
from compiler.transformers.CreateAnnotatedTree import AnnotatedTree


class ArgumentState:

    def __init__(self, state: str):
        self.required_states = set()
        self.state_transitions = set()

        STATES_REGEX = r"\{([a-zA-Z\s\d]*(=>[a-zA-Z\s\d]*)?(,[a-zA-Z\s\d]*(=>[a-zA-Z\s\d]*)?)*)\}"
        if not re.match(STATES_REGEX, state):
            raise ValueError(f"Invalid state definition {state}")

        state_parts = re.match(STATES_REGEX, state).group(1).split(",")

        for part in state_parts:
            if "=>" in part:
                before, after = [p.strip() for p in part.split("=>")]
                self.add_state_transition(before, after)
            else:
                self.required_states.add(part.strip()) if part.strip() else None

    def __copy__(self):
        new = ArgumentState("{}")
        new.required_states = self.required_states.copy()
        new.state_transitions = self.state_transitions.copy()
        return new
    def add_required_state(self, state):
        self.required_states.add(state)

    def add_state_transition(self, before, after):
        self.state_transitions.add((before, after))
        self.required_states.add(before) if before else None

    def check_required_states(self, states):
        return self.required_states.issubset(states)

    def apply_state_transitions(self, states):
        # We want to apply all transitions simultaneously
        states_to_remove = set()
        states_to_add = set()

        for before, after in self.state_transitions:
            if before in states or not before:
                states_to_remove.add(before) if before else None
                states_to_add.add(after) if after else None

        states.difference_update(states_to_remove)
        states.update(states_to_add)

class StateError(TypecheckException):
    def __init__(self, msg, line, column):
        super().__init__(msg, line, column)
class StateLayer(lark.visitors.Interpreter):
    def __init__(self):
        self.__states = defaultdict(set)
        self.__function_states = dict()

    def __annotate_states(self, tree):
        if not isinstance(tree, AnnotatedTree):
            tree = AnnotatedTree(tree.data, tree.children, tree.meta)

        for identifier in self.__states:
            tree.add_layer_annotation("state", identifier, "state", self.__states[identifier])

        for fun_identifier in self.__function_states:
            tree.add_layer_annotation("state",fun_identifier, "function_state",self.__function_states[fun_identifier])

    def layer(self, tree):
        identifier = tree.children[0].children[0].value
        layer_name = tree.children[1].children[0].value

        if layer_name != "state":
            return tree

        states = [t.strip() for t in tree.children[2].value.split("->")]

        if len(states) == 1:
            # State definition for a identifier
            # That case can be used to check that a variable has a specific state or manually define a transition
            arg_state = ArgumentState(states[0])
            state = tree.get_layer_annotation("state",identifier,"state")
            if state is None:
                state = set()
            if not arg_state.check_required_states(state):
                raise StateError(
                    f"Identifier {identifier} does not have the required state.", tree.meta.line, tree.meta.column)
            state = copy(state)
            arg_state.apply_state_transitions(state)
            self.__states[identifier] = state

        else:
            # This is a definition for a function
            # Special handling for functions without arguments:
            if len(states) == 2 and states[0] == "":
                states = states[1:]
            self.__function_states[identifier] = [ArgumentState(s) for s in states]

    def fun_call(self, tree):
        fun_identifier = tree.children[0].value

        if fun_identifier not in self.__function_states:
            return set()

        # Check that the number of arguments matches
        if len(tree.children[1:]) != len(self.__function_states[fun_identifier]) - 1:
            raise WrongArgumentCountException(fun_identifier, len(self.__function_states[fun_identifier]) - 1,
                                              len(tree.children[1:]), tree.meta.line, tree.meta.column)

        # Check that each argument has the required states
        for i, arg in enumerate(tree.children[1:]):
            if not self.__function_states[fun_identifier][i].check_required_states(self.visit(arg)):
                raise StateError(f"Argument #{i} of function {fun_identifier} has the wrong state.", tree.meta.line, tree.meta.column)

        # Apply the state transitions
        for i, arg in enumerate(tree.children[1:]):
            new_state = copy(self.visit(arg))
            self.__function_states[fun_identifier][i].apply_state_transitions(new_state)
            # If the argument is an identifier, we need to update the state
            if isinstance(arg, AnnotatedTree) and arg.data == "ident":
                self.__states[arg.children[0].value] = new_state

        # Return the states of the last argument which corresponds to the return value
        return self.__function_states[fun_identifier][-1].required_states

    def ident(self, tree):
        identifier = tree.children[0].value
        state = tree.get_layer_annotation("state",identifier,"state")
        return state if state else set()

    def assign(self, tree):
        self.__states[tree.children[0].children[0].value] = self.visit(tree.children[1])

    def fun_def(self, tree):
        fun_identifier = tree.children[0].value

        arg_names = [child.value for child in tree.children[1:-1]]
        # Check if the function has a state definition

        # We need to restore the states after the function definition
        old_states = self.__states.copy()
        old_function_states = self.__function_states.copy()

        # We reset the states to the default values
        self.__states = defaultdict(set)

        if fun_identifier in self.__function_states:
            # Check that the number of arguments matches
            if len(arg_names) != len(self.__function_states[fun_identifier]) - 1:
                raise WrongArgumentCountException(fun_identifier,
                                                  len(self.__function_states[fun_identifier]) - 1,
                                                  len(arg_names),
                                                  tree.meta.line,
                                                  tree.meta.column)

            # Add the states of the arguments to the function definition
            for i, arg in enumerate(arg_names):
                self.__states[arg] = self.__function_states[fun_identifier][i].required_states

        # Visit the function body
        self.visit(tree.children[-1])

        # Restore the old states
        self.__states = old_states.copy()
        self.__function_states = old_function_states.copy()

    def block(self, tree):
        return self.visit_children(tree)

    def __default__(self, tree):
        self.visit_children(tree)
        return set()

    def _visit_tree(self, tree):
        self.__annotate_states(tree)
        return super()._visit_tree(tree)

def typecheck(tree):
    state_checker = StateLayer()

    state_checker.visit(tree)

    return tree