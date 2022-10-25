import os.path
import unittest

from compiler.Compiler import LayeredCompiler

class TestParser(unittest.TestCase):

    def __parse_file(self, file_path):
        impl_path = os.path.dirname(os.path.realpath(__file__)) + "/implementations.py"
        layer_path = os.path.dirname(os.path.realpath(__file__)) + "/layer_implementations"
        compiler = LayeredCompiler(impl_path, layer_path)

        src_path = os.path.dirname(os.path.realpath(__file__)) + f"{file_path}"
        tree = compiler.parse(src_path)

        return tree


    def test_layer_def(self):
        tree = self.__parse_file("/test_code/syntax/layer.fl")

        self.assertEqual(tree.data, "start")
        self.assertEqual(tree.children[0].data, "layer")
        self.assertEqual(tree.children[0].children[0].data, "ident")
        self.assertEqual(tree.children[0].children[0].children[0].value, "id")
        self.assertEqual(tree.children[0].children[1].data, "ident")
        self.assertEqual(tree.children[0].children[1].children[0].value, "layer")
        self.assertEqual(tree.children[0].children[2].value, "{Refinement}")
        pass

    def test_assign(self):
        tree = self.__parse_file("/test_code/syntax/assign.fl")

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

        tree = self.__parse_file("/test_code/syntax/assign_custom.fl")

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
        tree = self.__parse_file("/test_code/syntax/if_stmt.fl")

        self.assertEqual(tree.data, "start")
        self.assertEqual(tree.children[0].data, "if_stmt")
        self.assertEqual(tree.children[0].children[0].data, "ident")
        self.assertEqual(tree.children[0].children[0].children[0], "condition")
        self.assertEqual(tree.children[0].children[1].data, "true")
        self.assertEqual(tree.children[0].children[2].data, "false")

    def test_let_stmt(self):
        tree = self.__parse_file("/test_code/syntax/let_stmt.fl")

        self.assertEqual(tree.data, "start")
        self.assertEqual(tree.children[0].data, "let_stmt")
        self.assertEqual(tree.children[0].children[0].data, "ident")
        self.assertEqual(tree.children[0].children[0].children[0], "x")
        self.assertEqual(tree.children[0].children[1].data, "num")
        self.assertEqual(tree.children[0].children[1].children[0], "42")
        self.assertEqual(tree.children[0].children[2].data, "ident")
        self.assertEqual(tree.children[0].children[2].children[0], "x")
        pass

    def test_bin_op(self):
        pass

    def test_call(self):
        tree = self.__parse_file("/test_code/syntax/fun_call.fl")

        self.assertEqual(tree.data, "start")
        self.assertEqual(tree.children[0].data, "fun_call")
        self.assertEqual(tree.children[0].children[0], "funCall")
        self.assertEqual(tree.children[0].children[1].data, "ident")
        self.assertEqual(tree.children[0].children[1].children[0], "argument")

        self.assertEqual(tree.children[1].data, "fun_call")
        self.assertEqual(tree.children[1].children[0], "funCall")
        self.assertEqual(tree.children[1].children[1].data, "num")
        self.assertEqual(tree.children[1].children[1].children[0], "42")

        self.assertEqual(tree.children[2].data, "fun_call")
        self.assertEqual(tree.children[2].children[0], "funCall")
        self.assertEqual(tree.children[2].children[1].data, "true")

        self.assertEqual(tree.children[3].data, "fun_call")
        self.assertEqual(tree.children[3].children[0], "funCall")
        self.assertEqual(tree.children[3].children[1].data, "false")

    def test_func_def(self):
        tree = self.__parse_file("/test_code/syntax/fun_def.fl")

        self.assertEqual(tree.data, "start")
        self.assertEqual(tree.children[0].data, "fun_def")
        self.assertEqual(tree.children[0].children[0], "function")
        self.assertEqual(tree.children[0].children[1], "arg")
        self.assertEqual(tree.children[0].children[2].data, "fun_body")
        self.assertEqual(tree.children[0].children[2].children[0].data, "ident")
        self.assertEqual(tree.children[0].children[2].children[0].children[0], "arg")

    def test_constants(self):
        tree = self.__parse_file("/test_code/syntax/constants.fl")

        self.assertEqual(tree.data, "start")
        self.assertEqual(tree.children[0].data, "num")
        self.assertEqual(tree.children[0].children[0], "0")
        self.assertEqual(tree.children[1].data, "num")
        self.assertEqual(tree.children[1].children[0], "1")
        self.assertEqual(tree.children[2].data, "num")
        self.assertEqual(tree.children[2].children[0], "-1")
        self.assertEqual(tree.children[3].data, "true")
        self.assertEqual(tree.children[4].data, "false")