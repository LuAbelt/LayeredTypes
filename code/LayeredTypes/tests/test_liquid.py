import unittest

from compiler.Exceptions import LayerException
from tests.utils import parse_file, typecheck_correct_file, get_compiler, full_path


class TestLiquidLayer(unittest.TestCase):
    def test_simple_assign(self):
        typecheck_correct_file(self, "/test_code/liquid/simple_assignment.fl")

    def test_simple_assignment_infer(self):
        typecheck_correct_file(self, "/test_code/liquid/simple_assignment_infer.fl")

    def test_simple_assignment_fail(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/liquid/simple_assignment_fail.fl")

        with self.assertRaises(LayerException):
            compiler.typecheck(src_file)

        # TODO: Check exact error
        self.assertTrue(False)

    def test_simple_assignment_infer_fail(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/liquid/simple_assignment_infer_fail.fl")

        with self.assertRaises(LayerException):
            compiler.typecheck(src_file)

        # TODO: Check exact error
        self.assertTrue(False)

    def test_fun_call_noArgs(self):
        typecheck_correct_file(self, "/test_code/liquid/fun_call_noArgs.fl")

    def test_fun_call_noArgs_assign(self):
        typecheck_correct_file(self, "/test_code/liquid/fun_call_noArgs_assign.fl")

    def test_fun_call_oneArg(self):
        typecheck_correct_file(self, "/test_code/liquid/fun_call_oneArg.fl")

    def test_fun_call_oneArg_assign(self):
        typecheck_correct_file(self, "/test_code/liquid/fun_call_oneArg_assign.fl")

    def test_fun_call_twoArgs(self):
        typecheck_correct_file(self, "/test_code/liquid/fun_call_twoArgs.fl")

    def test_fun_call_twoArgs_assign(self):
        typecheck_correct_file(self, "/test_code/liquid/fun_call_twoArgs_assign.fl")

    def test_nested_fun_call(self):
        typecheck_correct_file(self, "/test_code/liquid/nested_fun_call.fl")

    def test_let_inner_layer(self):
        typecheck_correct_file(self, "/test_code/liquid/let_inner_layer.fl")

    def test_let_inner_layer_fail(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/liquid/let_inner_layer_fail.fl")

        with self.assertRaises(LayerException):
            compiler.typecheck(src_file)

        # TODO: Check exact error
        self.assertTrue(False)

    def test_ident_type_undefined(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/liquid/ident_type_undefined.fl")

        with self.assertRaises(LayerException):
            compiler.typecheck(src_file)

        # TODO: Check exact error
        self.assertTrue(False)

    def test_fun_type_undefined(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/liquid/fun_type_undefined.fl")

        with self.assertRaises(LayerException):
            compiler.typecheck(src_file)

        # TODO: Check exact error
        self.assertTrue(False)

    def test_assign_fail(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/liquid/assign_fail.fl")

        with self.assertRaises(LayerException):
            compiler.typecheck(src_file)

        # TODO: Check exact error
        self.assertTrue(False)