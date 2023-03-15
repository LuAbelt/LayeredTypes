import unittest

from compiler.Exceptions import LayerException
from utils import get_compiler, full_path, typecheck_correct_file


class Typechecking(unittest.TestCase):
    def test_assign_bool_to_num(self):
        compiler = get_compiler(layer_path = full_path("/../layer_implementations"))
        src_file = full_path("/test_code/typechecking/assign_bool_to_num.fl")

        with self.assertRaises(LayerException) as context:
            compiler.typecheck(src_file)

        self.assertEqual(context.exception.layer_name, "typecheck")

        e = context.exception.original_exception
        self.assertEqual(e.__class__.__name__, "TypecheckException")
        self.assertEqual(e.lineno, 8)
        self.assertEqual(e.offset, 1)

    def test_bool_assign(self):
        typecheck_correct_file(self, "/test_code/typechecking/bool_assign.fl")

    def test_simple_fun(self):
        typecheck_correct_file(self, "/test_code/typechecking/simple_fun.fl")

    def test_fun_with_args(self):
        typecheck_correct_file(self, "/test_code/typechecking/fun_with_args.fl")

    def test_narrowing_assign(self):
        compiler = get_compiler(layer_path = full_path("/../layer_implementations"))
        src_file = full_path("/test_code/typechecking/narrowing_assign.fl")

        with self.assertRaises(LayerException) as context:
            compiler.typecheck(src_file)

        self.assertEqual(context.exception.layer_name, "typecheck")

        e = context.exception.original_exception
        self.assertEqual(e.__class__.__name__, "TypecheckException")
        self.assertEqual(e.lineno, 10)
        self.assertEqual(e.offset, 1)

    def test_simple_bool(self):
        typecheck_correct_file(self, "/test_code/typechecking/simple_bool.fl")

    def test_simple_num(self):
        typecheck_correct_file(self, "/test_code/typechecking/simple_num.fl")

    def test_widening_assign(self):
        typecheck_correct_file(self, "/test_code/typechecking/widening_assign_num.fl")

    def test_wrong_arg_type(self):
        compiler = get_compiler(layer_path = full_path("/../layer_implementations"))
        src_file = full_path("/test_code/typechecking/wrong_arg_type.fl")

        with self.assertRaises(LayerException) as context:
            compiler.typecheck(src_file)

        self.assertEqual(context.exception.layer_name, "typecheck")

        e = context.exception.original_exception
        self.assertEqual(e.__class__.__name__, "TypecheckException")
        self.assertEqual(e.lineno, 7)
        self.assertEqual(e.offset, 1)

    def test_bin_ops(self):
        typecheck_correct_file(self, "/test_code/typechecking/bin_ops.fl")

    def test_function_name_as_arg(self):
        typecheck_correct_file(self, "/test_code/typechecking/function_name_as_arg.fl")

    def test_type_annotation_different_scope(self):
        typecheck_correct_file(self, "/test_code/typechecking/type_annotation_different_scope.fl")

    def test_type_only_defined_outer_scope(self):
        compiler = get_compiler(layer_path = full_path("/../layer_implementations"))
        src_file = full_path("/test_code/typechecking/type_only_defined_outer_scope.fl")

        with self.assertRaises(LayerException) as context:
            compiler.typecheck(src_file)

        self.assertEqual(context.exception.layer_name, "typecheck")

        e = context.exception.original_exception
        self.assertEqual(e.__class__.__name__, "TypecheckException")
        self.assertEqual(9, e.lineno)
        self.assertEqual(5, e.offset)

    def test_type_only_defined_inner_scope(self):
        compiler = get_compiler(layer_path = full_path("/../layer_implementations"))
        src_file = full_path("/test_code/typechecking/type_only_defined_inner_scope.fl")

        with self.assertRaises(LayerException) as context:
            compiler.typecheck(src_file)

        self.assertEqual(context.exception.layer_name, "typecheck")

        e = context.exception.original_exception
        self.assertEqual(e.__class__.__name__, "TypecheckException")
        self.assertEqual(12, e.lineno)
        self.assertEqual(1, e.offset)

    def test_if_properly_typed(self):
        typecheck_correct_file(self, "/test_code/typechecking/if_properly_typed.fl")

    def test_if_illegal_typed(self):
        compiler = get_compiler(layer_path = full_path("/../layer_implementations"))
        src_file = full_path("/test_code/typechecking/if_illegal_typed.fl")

        with self.assertRaises(LayerException) as context:
            compiler.typecheck(src_file)

        self.assertEqual(context.exception.layer_name, "typecheck")

        e = context.exception.original_exception
        self.assertEqual(e.__class__.__name__, "TypecheckException")
        self.assertEqual(e.lineno, 5)
        self.assertEqual(e.offset, 1)
