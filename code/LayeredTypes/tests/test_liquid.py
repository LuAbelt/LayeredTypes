import unittest

from aeon.frontend.parser import mk_parser, parse_type
from compiler.Exceptions import LayerException
from tests.utils import parse_file, typecheck_correct_file, get_compiler, full_path


class TestLiquidLayer(unittest.TestCase):
    def test_simple_assign(self):
        typecheck_correct_file(self, "/test_code/liquid/simple_assignment.fl")

    def test_simple_assignment_infer(self):
        typecheck_correct_file(self, "/test_code/liquid/simple_assignment_infer.fl")

    def test_simple_assignment_fail(self):
        compiler = get_compiler(layer_path="../layer_implementations")
        src_file = full_path("/test_code/liquid/simple_assignment_fail.fl")

        with self.assertRaises(LayerException) as context:
            compiler.typecheck(src_file)

        self.assertEqual("liquid", context.exception.layer_name)
        e = context.exception.original_exception
        self.assertEqual("LiquidSubtypeException", e.__class__.__name__)
        self.assertEqual(4, e.lineno)
        self.assertEqual(1, e.offset)

        type_expected = parse_type("{c:Int | c > 0}")
        type_actual = parse_type("{v:Int | v == 0}")
        self.assertEqual(type_actual, e.type_actual)
        self.assertEqual(type_expected, e.type_expected)

    def test_simple_assignment_infer_fail(self):
        compiler = get_compiler(layer_path="../layer_implementations")
        src_file = full_path("/test_code/liquid/simple_assignment_infer_fail.fl")

        with self.assertRaises(LayerException) as context:
            compiler.typecheck(src_file)

        self.assertEqual("liquid", context.exception.layer_name)
        e = context.exception.original_exception
        self.assertEqual("LiquidSubtypeException", e.__class__.__name__)
        self.assertEqual(16, e.lineno)
        self.assertEqual(5, e.offset)

        type_expected = parse_type("{v:Int | v > 5}")
        type_actual = parse_type("{v:Int | v == 3}")
        self.assertEqual(type_actual, e.type_actual)
        self.assertEqual(type_expected, e.type_expected)

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
        compiler = get_compiler(layer_path="../layer_implementations")
        src_file = full_path("/test_code/liquid/let_inner_layer_fail.fl")

        with self.assertRaises(LayerException) as context:
            compiler.typecheck(src_file, False)

        self.assertEqual("liquid", context.exception.layer_name)
        e = context.exception.original_exception
        self.assertEqual("LiquidTypeUndefinedError", e.__class__.__name__)
        self.assertEqual(12, e.lineno)
        self.assertEqual(1, e.offset)
        self.assertEqual("y", e.identifier)

    def test_ident_type_undefined(self):
        compiler = get_compiler(layer_path="../layer_implementations")
        src_file = full_path("/test_code/liquid/ident_type_undefined.fl")

        with self.assertRaises(LayerException) as context:
            compiler.typecheck(src_file,check_cf=False)

        self.assertEqual("liquid", context.exception.layer_name)
        e = context.exception.original_exception
        self.assertEqual("LiquidTypeUndefinedError", e.__class__.__name__)
        self.assertEqual(3, e.lineno)
        self.assertEqual(1, e.offset)
        self.assertEqual("x", e.identifier)

    def test_fun_type_undefined(self):
        compiler = get_compiler(layer_path="../layer_implementations")
        src_file = full_path("/test_code/liquid/fun_type_undefined.fl")

        with self.assertRaises(LayerException) as context:
            compiler.typecheck(src_file,check_cf=False)

        self.assertEqual("liquid", context.exception.layer_name)
        e = context.exception.original_exception
        self.assertEqual("LiquidTypeUndefinedError", e.__class__.__name__)
        self.assertEqual(3, e.lineno)
        self.assertEqual(1, e.offset)
        self.assertEqual("oneArg", e.identifier)

    def test_assign_fail(self):
        compiler = get_compiler(layer_path="../layer_implementations")
        src_file = full_path("/test_code/liquid/assign_fail.fl")

        with self.assertRaises(LayerException) as context:
            compiler.typecheck(src_file)

        self.assertEqual("liquid", context.exception.layer_name)
        e = context.exception.original_exception
        self.assertEqual("FeatureNotSupportedError", e.__class__.__name__)
        self.assertEqual(4, e.lineno)
        self.assertEqual(1, e.offset)

    def test_fun_def(self):
        #TODO
        self.assertTrue(False)