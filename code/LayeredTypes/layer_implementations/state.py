import re
from collections import defaultdict

import lark.visitors


class ArgumentState:
    def __init__(self):
        self.required_states = set()
        self.state_transitions = set()

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

    def add_required_state(self, state):
        self.required_states.add(state)

    def add_state_transition(self, before, after):
        self.state_transitions.add((before, after))
        self.required_states.add(before)

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


class StateLayer(lark.visitors.Interpreter):
    def __init__(self):
        self.__states = defaultdict(set)
        self.__function_states = dict()

    def layer(self, tree):
        identifier = tree.children[0].children[0].value
        layer_name = tree.children[1].children[0].value

        if layer_name != "state":
            return tree

        states = [t.strip for t in tree.children[2].value.split("->")]

        if len(states) == 1:
            # State definition for a identifier
            # That case can be used to check that a variable has a specific state or manually define a transition
            arg_state = self.ArgumentState(states[0])
            if not arg_state.check_required_states(self.__states[identifier]):
                raise TypeError(
                    f"{tree.meta.line}:{tree.meta.column}: Identifier {identifier} does not have the required state.")
            arg_state.apply_state_transitions(self.__states[identifier])

        else:
            # This is a definition for a function
            self.__function_states[identifier] = [self.ArgumentState(s) for s in states]

    def fun_call(self, tree):
        fun_identifier = tree.children[0].value

        if fun_identifier not in self.__function_states:
            return set()

        # Check that each argument has the required states
        for i, arg in enumerate(tree.children[1:-1]):
            if not self.__function_states[fun_identifier][i].check_required_states(self.visit(arg)):
                raise TypeError(
                    f"{tree.meta.line}:{tree.meta.column}: Function {fun_identifier} was called with invalid state for argument {i}.")

        # Apply the state transitions
        for i, arg in enumerate(tree.children[1:-1]):
            self.__function_states[fun_identifier][i].apply_state_transitions(self.visit(arg))

        # Return the states of the last argument which corresponds to the return value
        return self.__function_states[fun_identifier][-1].required_states

    def ident(self, tree):
        return self.__states[tree.children[0].value] if tree.value in self.__states else set()

    def assign(self, tree):
        self.__states[tree.children[0].value] = self.visit(tree.children[1])

    def fun_def(self, tree):
        raise NotImplementedError()

    def __default__(self, tree):
        return set()

def typecheck(tree):
    pass