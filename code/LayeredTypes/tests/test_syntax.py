import os.path
import unittest

from compiler.Compiler import LayeredCompiler
from tests.utils import parse_file

class TestParser(unittest.TestCase):

    def test_layer_def(self):
        tree = parse_file("/test_code/syntax/layer.fl")

        self.assertEqual(tree.data, "start")
        self.assertEqual(tree.children[0].data, "layer")
        self.assertEqual(tree.children[0].children[0].data, "ident")
        self.assertEqual(tree.children[0].children[0].children[0].value, "id")
        self.assertEqual(tree.children[0].children[1].data, "ident")
        self.assertEqual(tree.children[0].children[1].children[0].value, "layer")
        self.assertEqual(tree.children[0].children[2].value, "{Refinement}")
        pass

    def test_assign(self):
        tree = parse_file("/test_code/syntax/assign.fl")

        self.assertEqual(tree.data, "start")
        self.assertEqual(tree.children[0].data, "assign")
        self.assertEqual(tree.children[0].children[0].data, "ident")
        self.assertEqual(tree.children[0].children[0].children[0], "x")
        self.assertEqual(tree.children[0].children[1].data, "true")

        self.assertEqual(tree.children[1].data, "assign")
        self.assertEqual(tree.children[1].children[0].data, "ident")
        self.assertEqual(tree.children[1].children[0].children[0], "y")
        self.assertEqual(tree.children[1].children[1].data, "ident")
        self.assertEqual(tree.children[1].children[1].children[0], "x")

        tree = parse_file("/test_code/syntax/assign_custom.fl")

        self.assertEqual(tree.data, "start")
        self.assertEqual(tree.children[0].data, "assign")
        self.assertEqual(tree.children[0].children[0].data, "ident")
        self.assertEqual(tree.children[0].children[0].children[0], "x")
        self.assertEqual(tree.children[0].children[1].data, "custom_expr")
        self.assertEqual(tree.children[0].children[1].children[0], "\"MyType\"")

        self.assertEqual(tree.children[1].data, "assign")
        self.assertEqual(tree.children[1].children[0].data, "ident")
        self.assertEqual(tree.children[1].children[0].children[0], "y")
        self.assertEqual(tree.children[1].children[1].data, "custom_expr")
        self.assertEqual(tree.children[1].children[1].children[0], "{1,2,3}")

    def test_if_stmt(self):
        tree = parse_file("/test_code/syntax/if_stmt.fl")

        self.assertEqual(tree.data, "start")
        self.assertEqual(len(tree.children), 4)

        def check_if_stmt(tree, condition, then_body_length, else_body_length):
            self.assertEqual(tree.data, "if_stmt")
            self.assertEqual(tree.children[0].data, "ident")
            self.assertEqual(tree.children[0].children[0], condition)
            self.assertEqual(tree.children[1].data, "block")
            self.assertEqual(len(tree.children[1].children), then_body_length)

            if else_body_length > 0:
                self.assertEqual(tree.children[2].data, "block")
                self.assertEqual(len(tree.children[2].children), else_body_length)

        check_if_stmt(tree.children[0], "condition", 1, 1)
        check_if_stmt(tree.children[1], "condition", 1, 1)
        check_if_stmt(tree.children[2], "condition", 3, 2)
        check_if_stmt(tree.children[3], "condition", 1, 0)

        # We skip checking parsing of the body of the if statement, because it is already tested in other tests

    def test_let_stmt(self):
        tree = parse_file("/test_code/syntax/let_stmt.fl")

        self.assertEqual(tree.data, "start")
        self.assertEqual(len(tree.children), 4)

        def check_let_stmt(tree, ident, value, body_length):
            self.assertEqual(tree.data, "let_stmt")
            self.assertEqual(tree.children[0].data, "ident")
            self.assertEqual(tree.children[0].children[0], ident)
            self.assertEqual(tree.children[1].data, value[0])
            if value[1] is not None:
                self.assertEqual(tree.children[1].children[0], value[1])

            self.assertEqual(tree.children[2].data, "block")
            self.assertEqual(len(tree.children[2].children), body_length)

        # Check general let construct and body sizes
        check_let_stmt(tree.children[0], "x", ("num", "42"), 1)
        check_let_stmt(tree.children[1], "x", ("num", "42"), 1)
        check_let_stmt(tree.children[2], "x", ("ident", "y"), 1)
        check_let_stmt(tree.children[3], "x", ("num", "42"), 3)

        # Specifically check bodies of let constructs
        self.assertEqual(tree.children[0].children[2].data, "block")
        self.assertEqual(len(tree.children[0].children[2].children), 1)
        self.assertEqual(tree.children[0].children[2].children[0].data, "ident")
        self.assertEqual(tree.children[0].children[2].children[0].children[0], "x")

        # Skip second and third let as these are identical to the first
        self.assertEqual(tree.children[3].children[2].data, "block")
        self.assertEqual(len(tree.children[3].children[2].children), 3)
        self.assertEqual(tree.children[3].children[2].children[0].data, "bin_op")
        self.assertEqual(tree.children[3].children[2].children[1].data, "bin_op")
        self.assertEqual(tree.children[3].children[2].children[2].data, "bin_op")
        # We don't check the bodies of the bin_ops as these are tested elsewhere

    def test_bin_op(self):
        tree = parse_file("/test_code/syntax/bin_op.fl")

        def check_bin_op(tree, op):
            self.assertEqual(tree.data, "bin_op")
            self.assertEqual(tree.children[0].data, "ident")
            self.assertEqual(tree.children[0].children[0], "a")
            self.assertEqual(tree.children[1], op)
            self.assertEqual(tree.children[2].data, "ident")
            self.assertEqual(tree.children[2].children[0], "b")

        self.assertEqual(tree.data, "start")
        check_bin_op(tree.children[0], "+")
        check_bin_op(tree.children[1], "-")
        check_bin_op(tree.children[2], "*")
        check_bin_op(tree.children[3], ">")
        check_bin_op(tree.children[4], "<")
        check_bin_op(tree.children[5], ">=")
        check_bin_op(tree.children[6], "<=")
        check_bin_op(tree.children[7], "==")
        check_bin_op(tree.children[8], "!=")


    def test_call(self):
        tree = parse_file("/test_code/syntax/fun_call.fl")


        def check_call(tree, function_identifier, arg_identifiers):
            self.assertEqual(tree.data, "fun_call")
            self.assertEqual(len(tree.children), len(arg_identifiers) + 1)
            self.assertEqual(tree.children[0], function_identifier)

            for i in range(len(arg_identifiers)):
                self.assertEqual(tree.children[i+1].data, arg_identifiers[i][0])
                if arg_identifiers[i][1] is not None:
                    self.assertEqual(tree.children[i+1].children[0], arg_identifiers[i][1])


        self.assertEqual(tree.data, "start")
        check_call(tree.children[0], "funCall", [("ident","argument")])
        check_call(tree.children[1], "funCall", [("num","42")])
        check_call(tree.children[2], "funCall", [("true",None)])
        check_call(tree.children[3], "funCall", [("false",None)])
        check_call(tree.children[4], "emptyCall", [])
        check_call(tree.children[5], "twoArgs", [("ident","first"), ("ident","second")])
        check_call(tree.children[6], "threeArgs", [("ident","first"), ("ident","second"), ("ident","third")])

    def test_func_def(self):
        tree = parse_file("/test_code/syntax/fun_def.fl")

        def check_fun_def(tree, function_identifier, arg_identifiers, body):
            self.assertEqual(tree.data, "fun_def")
            self.assertEqual(len(tree.children), len(arg_identifiers) + 2)
            self.assertEqual(tree.children[0], function_identifier)
            self.assertEqual(tree.children[1:-1], arg_identifiers)
            self.assertEqual(tree.children[-1].data, "block")
            for i in range(len(body)):
                self.assertEqual(tree.children[-1].children[i].data, body[i][0])
                if body[i][1] is not None:
                    self.assertEqual(tree.children[-1].children[i].children[0], body[i][1])

        self.assertEqual(tree.data, "start")

        check_fun_def(tree.children[0], "function", ["arg"], [("ident","arg")])
        check_fun_def(tree.children[1], "noArgs", [], [("num","42")])
        check_fun_def(tree.children[2], "twoArgs", ["first", "second"], [("ident","first"), ("ident","second")])
        check_fun_def(tree.children[3], "manyArgs", ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth"], [("ident","first"), ("ident","second"), ("ident","third"), ("ident","fourth"), ("ident","fifth"), ("ident","sixth"), ("ident","seventh"), ("ident","eighth"), ("ident","ninth"), ("ident","tenth")])

    def test_constants(self):
        tree = parse_file("/test_code/syntax/constants.fl")

        self.assertEqual(tree.data, "start")
        self.assertEqual(tree.children[0].data, "num")
        self.assertEqual(tree.children[0].children[0], "0")
        self.assertEqual(tree.children[1].data, "num")
        self.assertEqual(tree.children[1].children[0], "1")
        self.assertEqual(tree.children[2].data, "num")
        self.assertEqual(tree.children[2].children[0], "-1")
        self.assertEqual(tree.children[3].data, "true")
        self.assertEqual(tree.children[4].data, "false")
