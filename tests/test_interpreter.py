import os
import unittest

from compiler.Interpreters import SimpleInterpreter
from utils import parse_file, get_compiler, full_path


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

    def block(self, tree):
        result = []
        for child in tree.children:
            result.append(self.visit(child))

        return result

class TestInterpreter(unittest.TestCase):
    def test_assign(self):
        tree = parse_file("/test_code/syntax/assign.fl")

        test_interpreter = SimpleTestInterpreter()
        result = test_interpreter.run(tree)

        self.assertEqual(len(test_interpreter.variables), 3)
        self.assertEqual(test_interpreter.variables["x"], True)
        self.assertEqual(test_interpreter.variables["y"], True)
        self.assertEqual(test_interpreter.variables["z"], 42)

        self.assertEqual(len(result),3)
        self.assertEqual(result[0], None)
        self.assertEqual(result[1], None)
        self.assertEqual(result[2], None)

    def test_assign_custom(self):
        pass

    def test_bin_op(self):
        tree = parse_file("/test_code/syntax/bin_op.fl")

        test_interpreter = SimpleTestInterpreter()
        result = test_interpreter.run(tree, {"a": 7, "b": 3})

        self.assertEqual(result[0], 10)     # a + b
        self.assertEqual(result[1], 4)      # a - b
        self.assertEqual(result[2], 21)     # a * b
        self.assertEqual(result[3], True)   # a > b
        self.assertEqual(result[4], False)  # a < b
        self.assertEqual(result[5], True)   # a >= b
        self.assertEqual(result[6], False)  # a <= b
        self.assertEqual(result[7], False)  # a == b
        self.assertEqual(result[8], True)   # a != b

        result = test_interpreter.run(tree, {"a": 5, "b": 5})
        self.assertEqual(result[3], False)  # a > b
        self.assertEqual(result[4], False)  # a < b
        self.assertEqual(result[5], True)   # a >= b
        self.assertEqual(result[6], True)   # a <= b
        self.assertEqual(result[7], True)   # a == b
        self.assertEqual(result[8], False)  # a != b

    def test_constants(self):
        tree = parse_file("/test_code/syntax/constants.fl")

        test_interpreter = SimpleTestInterpreter()
        result = test_interpreter.run(tree)

        self.assertEqual(len(result), 5)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1], 1)
        self.assertEqual(result[2], -1)
        self.assertEqual(result[3], True)
        self.assertEqual(result[4], False)

    def test_fun_call(self):
        tree = parse_file("/test_code/syntax/fun_call.fl")

        test_interpreter = SimpleTestInterpreter()
        result = test_interpreter.run(tree, variables = {"argument": 7, "first": 7, "second": 3, "third": 5})

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

        test_interpreter = SimpleTestInterpreter()
        result = test_interpreter.run(tree)

        # A function definition should not return anything
        self.assertEqual(len(result), 4)
        self.assertEqual(result, [None for _ in range(4)])

        # The functions should be in the function dictionary
        self.assertEqual(len(test_interpreter.functions), 4)
        self.assertTrue("function" in test_interpreter.functions.keys())
        self.assertTrue("noArgs" in test_interpreter.functions.keys())
        self.assertTrue("twoArgs" in test_interpreter.functions.keys())
        self.assertTrue("manyArgs" in test_interpreter.functions.keys())

        # Check the function definitions
        self.assertEqual(test_interpreter.functions["function"].name, "function")
        self.assertEqual(test_interpreter.functions["function"].args, ["arg"])

        self.assertEqual(test_interpreter.functions["noArgs"].name, "noArgs")
        self.assertEqual(test_interpreter.functions["noArgs"].args, [])

        self.assertEqual(test_interpreter.functions["twoArgs"].name, "twoArgs")
        self.assertEqual(test_interpreter.functions["twoArgs"].args, ["first", "second"])

        self.assertEqual(test_interpreter.functions["manyArgs"].name, "manyArgs")
        self.assertEqual(test_interpreter.functions["manyArgs"].args, ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth"])

        # Test the function calls
        from lark import Tree, Token
        call_tree = Tree(Token('RULE', 'fun_call'), [Token('WORD', 'function'), Tree(Token('RULE', 'ident'), [Token('word', 'arg1')])])
        result = test_interpreter.run(call_tree, variables = {"arg1": 7}, functions=test_interpreter.functions)

        self.assertEqual(len(result), 1)
        self.assertEqual(result, [7])

        call_tree = Tree(Token('RULE', 'fun_call'), [Token('WORD', 'noArgs')])
        result = test_interpreter.run(call_tree, {}, test_interpreter.functions)

        self.assertEqual(len(result), 1)
        self.assertEqual(result, [42])

        call_tree = Tree(Token('RULE', 'fun_call'), [Token('WORD', 'twoArgs'), Tree(Token('RULE', 'ident'), [Token('word', 'arg1')]), Tree(Token('RULE', 'ident'), [Token('word', 'arg2')])])
        result = test_interpreter.run(call_tree, variables = {"arg1": 7, "arg2": 3}, functions=test_interpreter.functions)

        self.assertEqual(len(result), 2)
        self.assertEqual(result, [7, 3])

        call_tree = Tree(Token('RULE', 'fun_call'), [Token('WORD', 'manyArgs'), Tree(Token('RULE', 'ident'), [Token('word', 'arg1')]), Tree(Token('RULE', 'ident'), [Token('word', 'arg2')]), Tree(Token('RULE', 'ident'), [Token('word', 'arg3')]), Tree(Token('RULE', 'ident'), [Token('word', 'arg4')]), Tree(Token('RULE', 'ident'), [Token('word', 'arg5')]), Tree(Token('RULE', 'ident'), [Token('word', 'arg6')]), Tree(Token('RULE', 'ident'), [Token('word', 'arg7')]), Tree(Token('RULE', 'ident'), [Token('word', 'arg8')]), Tree(Token('RULE', 'ident'), [Token('word', 'arg9')]), Tree(Token('RULE', 'ident'), [Token('word', 'arg10')])])
        result = test_interpreter.run(call_tree, variables = {"arg1": 1, "arg2": 2, "arg3": 3, "arg4": 4, "arg5": 5, "arg6": 6, "arg7": 7, "arg8": 8, "arg9": 9, "arg10": 10}, functions=test_interpreter.functions)

        self.assertEqual(len(result), 10)
        self.assertEqual(result, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    def test_if(self):
        tree = parse_file("/test_code/syntax/if_stmt.fl")

        test_interpreter = SimpleTestInterpreter()

        result = test_interpreter.run(tree, {"condition": True})
        self.assertEqual(len(result), 4)
        self.assertEqual(result, [[True], [True], [10,11,12],[10]])

        result = test_interpreter.run(tree, {"condition": False})
        self.assertEqual(len(result), 4)
        self.assertEqual(result, [[False],[False],[20,21],None])

    def test_let(self):
        tree = parse_file("/test_code/syntax/let_stmt.fl")

        test_interpreter = SimpleTestInterpreter()
        result = test_interpreter.run(tree, {"y": 7})

        self.assertEqual(len(result), 4)
        self.assertEqual(result, [[42],[42],[7],[43,44,45]])

        self.assertEqual(len(test_interpreter.variables),1)
        self.assertTrue("y" in test_interpreter.variables.keys())

    def test_recursion(self):
        compiler = get_compiler()
        result = compiler.run(full_path("/test_code/syntax/factorial.fl"))

        self.assertEqual(result, 120)
