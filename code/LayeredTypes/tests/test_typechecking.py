import unittest

from tests.utils import get_compiler, full_path


class Typechecking(unittest.TestCase):
    def test_assign_bool_to_num(self):
        self.assertTrue(False)

    def test_bool_assign(self):
        self.assertTrue(False)

    def test_fun_with_args(self):
        self.assertTrue(False)

    def test_narrowing_assign(self):
        self.assertTrue(False)

    def test_simple_bool(self):
        self.assertTrue(False)

    def test_simple_num(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/typechecking/simple_num.fl")

        compiler.typecheck(src_file)
        # We don't need to do anything here, just make sure it does not throw an exception
        self.assertTrue(True)

    def test_widening_assign(self):
        self.assertTrue(False)

    def test_wrong_arg_type(self):
        self.assertTrue(False)

    def test_bin_ops(self):
        self.assertTrue(False)
