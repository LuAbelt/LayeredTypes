import unittest

from tests.utils import get_compiler, full_path


class Typechecking(unittest.TestCase):
    def __typecheck_correct_file(self, file_path):
        compiler = get_compiler()
        src_file = full_path(file_path)

        compiler.typecheck(src_file)
        # We don't need to do anything here, just make sure it does not throw an exception
        self.assertTrue(True)
    def test_assign_bool_to_num(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/typechecking/assign_bool_to_num.fl")

        with self.assertRaises(TypeError):
            compiler.typecheck(src_file)

    def test_bool_assign(self):
        self.__typecheck_correct_file("/test_code/typechecking/bool_assign.fl")

    def test_simple_fun(self):
        self.__typecheck_correct_file("/test_code/typechecking/simple_fun.fl")

    def test_fun_with_args(self):
        self.__typecheck_correct_file("/test_code/typechecking/fun_with_args.fl")

    def test_narrowing_assign(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/typechecking/narrowing_assign.fl")

        with self.assertRaises(TypeError):
            compiler.typecheck(src_file)

    def test_simple_bool(self):
        self.__typecheck_correct_file("/test_code/typechecking/simple_bool.fl")

    def test_simple_num(self):
        self.__typecheck_correct_file("/test_code/typechecking/simple_num.fl")

    def test_widening_assign(self):
        self.__typecheck_correct_file("/test_code/typechecking/widening_assign_num.fl")

    def test_wrong_arg_type(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/typechecking/wrong_arg_type.fl")

        with self.assertRaises(TypeError):
            compiler.typecheck(src_file)

    def test_bin_ops(self):
        self.__typecheck_correct_file("/test_code/typechecking/bin_ops.fl")

    def test_function_name_as_arg(self):
        self.__typecheck_correct_file("/test_code/typechecking/function_name_as_arg.fl")

    def test_type_annotation_different_scope(self):
        self.__typecheck_correct_file("/test_code/typechecking/type_annotation_different_scope.fl")

    def test_type_only_defined_outer_scope(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/typechecking/type_only_defined_outer_scope.fl")

        with self.assertRaises(TypeError) as context:
            compiler.typecheck(src_file)

        self.assertTrue("6:5: Type for variable 'x' is not defined" in str(context.exception))

    def test_type_only_defined_inner_scope(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/typechecking/type_only_defined_inner_scope.fl")

        with self.assertRaises(TypeError) as context:
            compiler.typecheck(src_file)

        self.assertTrue("10:1: Type for variable 'x' is not defined" in str(context.exception))