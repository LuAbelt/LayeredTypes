import unittest

from compiler.transformers.CheckCF import CheckCF
from tests.utils import parse_file


class TestControlFlow(unittest.TestCase):
    def test_undefined_ident(self):
        tree1 = parse_file("/test_code/control_flow/undefined_ident.fl")
        tree2 = parse_file("/test_code/control_flow/undefined_ident_2.fl")

        check_cf = CheckCF()

        self.assertRaises(RuntimeError, check_cf.visit_topdown, tree1)
        self.assertRaises(RuntimeError, check_cf.visit_topdown, tree2)

    def test_undefined_ident_in_if(self):
        pass

    def test_function_usage_before_def(self):
        pass

    def test_function_def_scope(self):
        pass

    def test_recursive_fun(self):
        pass

    def test_let_scope(self):
        pass


