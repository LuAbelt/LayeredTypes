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
        self.assertTrue(False)

    def test_bool_assign(self):
        self.__typecheck_correct_file("/test_code/typechecking/bool_assign.fl")

    def test_simple_fun(self):
        self.__typecheck_correct_file("/test_code/typechecking/simple_fun.fl")

    def test_fun_with_args(self):
        self.__typecheck_correct_file("/test_code/typechecking/fun_with_args.fl")

    def test_narrowing_assign(self):
        self.assertTrue(False)

    def test_simple_bool(self):
        self.__typecheck_correct_file("/test_code/typechecking/simple_bool.fl")

    def test_simple_num(self):
        self.__typecheck_correct_file("/test_code/typechecking/simple_num.fl")

    def test_widening_assign(self):
        self.__typecheck_correct_file("/test_code/typechecking/widening_assign_num.fl")

    def test_wrong_arg_type(self):
        self.assertTrue(False)

    def test_bin_ops(self):
        self.__typecheck_correct_file("/test_code/typechecking/bin_ops.fl")
