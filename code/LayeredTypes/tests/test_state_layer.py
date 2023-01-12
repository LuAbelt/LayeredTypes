import unittest

from layer_implementations.state import ArgumentState

class StateLayer(unittest.TestCase):
    def test_simple_state_add(self):
        self.assertEqual(True, False)  # add assertion here

class ArgumentStateParsing(unittest.TestCase):
    def assertEmpty(self, l):
        self.assertEqual(len(l), 0)
    def test_parse_empty(self):
        arg_state = ArgumentState("{}")
        self.assertEmpty(arg_state.required_states)
        self.assertEmpty(arg_state.state_transitions)

    def test_parse_single_state_requirement(self):
        arg_state = ArgumentState("{state}")
        self.assertSetEqual(arg_state.required_states, {"state"})
        self.assertEmpty(arg_state.state_transitions)

    def test_parse_single_state_transition(self):
        arg_state = ArgumentState("{state => otherState}")
        self.assertSetEqual(arg_state.required_states, {"state"})
        self.assertSetEqual(arg_state.state_transitions, {("state", "otherState")})

    def test_parse_multiple_state_transitions(self):
        arg_state = ArgumentState("{state1 => state2, state3 => state4}")
        self.assertSetEqual(arg_state.required_states, {"state1", "state3"})
        self.assertSetEqual(arg_state.state_transitions, {("state1", "state2"), ("state3", "state4")})

    def test_parse_multiple_state_requirements(self):
        arg_state = ArgumentState("{state1, state2}")
        self.assertSetEqual(arg_state.required_states, {"state1", "state2"})
        self.assertEmpty(arg_state.state_transitions)

    def test_parse_multiple_state_requirements_and_transitions(self):
        arg_state = ArgumentState("{state1, state2 => state3, state4 => state5}")
        self.assertSetEqual(arg_state.required_states, {"state1", "state2", "state4"})
        self.assertSetEqual(arg_state.state_transitions, {("state2", "state3"), ("state4", "state5")})

    def test_invalid_format(self):
        with self.assertRaises(ValueError):
            ArgumentState("{state1 => state2, state3 => state4")

    def test_invalid_format2(self):
        with self.assertRaises(ValueError):
            ArgumentState("state1 => state2, state3 => state4")

class ArgumentStateLogic(unittest.TestCase):
    def test_check_required_states(self):
        arg_state = ArgumentState("{state1, state2 => state3, state4 => state5}")
        self.assertTrue(arg_state.check_required_states({"state1", "state2", "state4"}))
        self.assertFalse(arg_state.check_required_states({"state1"}))
        self.assertFalse(arg_state.check_required_states({"state2"}))
        self.assertFalse(arg_state.check_required_states({"state4"}))
        self.assertFalse(arg_state.check_required_states({"state1", "state2"}))
        self.assertFalse(arg_state.check_required_states({"state1", "state4"}))
        self.assertFalse(arg_state.check_required_states({"state2", "state4"}))

    def test_apply_state_transitions(self):
        arg_state = ArgumentState("{state1, state2 => state3, state4 => state5}")
        states = {"state1", "state2", "state4"}
        arg_state.apply_state_transitions(states)
        self.assertSetEqual(states, {"state1","state3", "state5"})

    def test_apply_state_transitions2(self):
        arg_state = ArgumentState("{state1, state2 => state3, state4 => state5}")
        states = {"state1", "state2", "state3", "state4"}
        arg_state.apply_state_transitions(states)
        self.assertSetEqual(states, {"state1","state3", "state5"})

    def test_apply_transition_remove_and_create(self):
        arg_state = ArgumentState("{state1 => state2, state2 => state3}")
        states = {"state1", "state2"}
        arg_state.apply_state_transitions(states)
        self.assertSetEqual(states, {"state2","state3"})

    def test_apply_transition_remove_and_create2(self):
        arg_state = ArgumentState("{state1 => state2, state2 => state3}")
        states = {"state1", "state2", "state3"}
        arg_state.apply_state_transitions(states)
        self.assertSetEqual(states, {"state2","state3"})

    def test_apply_transition_remove_and_create3(self):
        arg_state = ArgumentState("{state3 => state1, state1 => state2}")
        states = {"state3", "state1"}
        arg_state.apply_state_transitions(states)
        self.assertSetEqual(states, {"state2","state1"})

    def test_apply_transition_remove_and_create4(self):
        arg_state = ArgumentState("{a=>b, b=>c, c=>d, d=>e}")
        states = {"a", "b", "c", "d"}
        arg_state.apply_state_transitions(states)
        self.assertSetEqual(states, {"b","c","d","e"})

    def test_apply_empty_transition(self):
        arg_state = ArgumentState("{state1 =>}")
        states = {"state1", "state2"}
        arg_state.apply_state_transitions(states)
        self.assertSetEqual(states, {"state2"})

    def test_apply_empty_transition2(self):
        arg_state = ArgumentState("{state1 =>}")
        states = {"state1"}
        arg_state.apply_state_transitions(states)
        self.assertSetEqual(states, set())

    def test_apply_empty_transition3(self):
        arg_state = ArgumentState("{state1 =>, state2 =>}")
        states = {"state2", "state1"}
        arg_state.apply_state_transitions(states)
        self.assertSetEqual(states, set())

    def test_state_transition_create(self):
        arg_state = ArgumentState("{ => state2}")
        states = set()
        arg_state.apply_state_transitions(states)
        self.assertSetEqual(states, {"state2"})

    def test_state_transition_create2(self):
        arg_state = ArgumentState("{ => state2, state1 => state3}")
        states = {"state1"}
        arg_state.apply_state_transitions(states)
        self.assertSetEqual(states, {"state2", "state3"})



if __name__ == '__main__':
    unittest.main()
