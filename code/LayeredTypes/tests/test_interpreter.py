import os
import unittest

from compiler.Interpreters import SimpleInterpreter
from tests.utils import parse_file


# We create a new Interpreter as we want the return value for each statement
class SimpleTestInterpreter(SimpleInterpreter):
    def __init__(self):
        impl_path = os.path.dirname(os.path.realpath(__file__)) + "/implementations.py"
        layer_path = os.path.dirname(os.path.realpath(__file__)) + "/layer_implementations"

        super().__init__(implementation_file=impl_path)

    def run(self, tree, variables=None, functions=None):
        if functions is None:
            functions = dict()

        if variables is None:
            variables = dict()

        self.variables = variables
        self.functions = functions

        return self.visit(tree)

class TestInterpreter(unittest.TestCase):
    def test_assign(self):
        tree = parse_file("/test_code/syntax/assign.fl")

        interpreter = SimpleTestInterpreter()
        result = interpreter.run(tree)

        self.assertEqual(len(interpreter.variables), 3)
        self.assertEqual(interpreter.variables["x"], True)
        self.assertEqual(interpreter.variables["y"], True)
        self.assertEqual(interpreter.variables["z"], 42)

        self.assertEqual(len(result),3)
        self.assertEqual(result[0], None)
        self.assertEqual(result[1], None)
        self.assertEqual(result[2], None)

    def test_assign_custom(self):
        pass

    def test_bin_op(self):
        tree = parse_file("/test_code/syntax/bin_op.fl")

        interpreter = SimpleTestInterpreter()
        result = interpreter.run(tree, {"a": 7, "b": 3})

        self.assertEqual(result[0], 10)     # a + b
        self.assertEqual(result[1], 4)      # a - b
        self.assertEqual(result[2], 21)     # a * b
        self.assertEqual(result[3], True)   # a > b
        self.assertEqual(result[4], False)  # a < b
        self.assertEqual(result[5], True)   # a >= b
        self.assertEqual(result[6], False)  # a <= b
        self.assertEqual(result[7], False)  # a == b
        self.assertEqual(result[8], True)   # a != b

        result = interpreter.run(tree, {"a": 5, "b": 5})
        self.assertEqual(result[3], False)  # a > b
        self.assertEqual(result[4], False)  # a < b
        self.assertEqual(result[5], True)   # a >= b
        self.assertEqual(result[6], True)   # a <= b
        self.assertEqual(result[7], True)   # a == b
        self.assertEqual(result[8], False)  # a != b

    def test_constants(self):
        tree = parse_file("/test_code/syntax/constants.fl")

        interpreter = SimpleTestInterpreter()
        result = interpreter.run(tree)

        self.assertEqual(len(result), 5)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1], 1)
        self.assertEqual(result[2], -1)
        self.assertEqual(result[3], True)
        self.assertEqual(result[4], False)

    def test_fun_call(self):
        tree = parse_file("/test_code/syntax/fun_call.fl")

        interpreter = SimpleTestInterpreter()
        result = interpreter.run(tree, variables = {"argument": 7, "first": 7, "second": 3, "third": 5})

        self.assertEqual(len(result), 7)
        self.assertEqual(result[0], 7)
        self.assertEqual(result[1], 42)
        self.assertEqual(result[2], True)
        self.assertEqual(result[3], False)
        self.assertEqual(result[4], 1337)
        self.assertEqual(result[5], [7, 3])
        self.assertEqual(result[6], [7, 3, 5])

    def test_fun_def(self):
        tree = parse_file("/test_code/syntax/fun_def.fl")

        interpreter = SimpleTestInterpreter()
        result = interpreter.run(tree)

        # A function definition should not return anything
        self.assertEqual(len(result), 4)
        self.assertEqual(result, [None for _ in range(4)])

        # The functions should be in the function dictionary
        self.assertEqual(len(interpreter.functions), 4)
        self.assertTrue("function" in interpreter.functions.keys())
        self.assertTrue("noArgs" in interpreter.functions.keys())
        self.assertTrue("twoArgs" in interpreter.functions.keys())
        self.assertTrue("manyArgs" in interpreter.functions.keys())

        # Check the function definitions
        self.assertEqual(interpreter.functions["function"].name, "function")
        self.assertEqual(interpreter.functions["function"].args, ["arg"])

        self.assertEqual(interpreter.functions["noArgs"].name, "noArgs")
        self.assertEqual(interpreter.functions["noArgs"].args, [])

        self.assertEqual(interpreter.functions["twoArgs"].name, "twoArgs")
        self.assertEqual(interpreter.functions["twoArgs"].args, ["first", "second"])

        self.assertEqual(interpreter.functions["manyArgs"].name, "manyArgs")
        self.assertEqual(interpreter.functions["manyArgs"].args, ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth"])

        # TODO: Check the function bodies by running them

    def test_if(self):
        tree = parse_file("/test_code/syntax/if_stmt.fl")

        interpreter = SimpleTestInterpreter()

        result = interpreter.run(tree, {"condition": True})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], True)

        result = interpreter.run(tree, {"condition": False})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], False)

    def test_let(self):
        tree = parse_file("/test_code/syntax/let_stmt.fl")

        interpreter = SimpleTestInterpreter()
        result = interpreter.run(tree)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 42)

        self.assertEqual(len(interpreter.variables),0)

