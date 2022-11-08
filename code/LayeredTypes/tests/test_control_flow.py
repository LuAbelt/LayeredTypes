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
        tree = parse_file("/test_code/control_flow/undef_id_if.fl")

        check_cf = CheckCF()

        self.assertRaises(RuntimeError, check_cf.visit_topdown, tree)

    def test_function_usage_before_def(self):
        tree = parse_file("/test_code/control_flow/fun_usage_before_def.fl")

        check_cf = CheckCF()

        self.assertWarns(RuntimeWarning, check_cf.visit_topdown, tree)

    def test_function_def_scope(self):
        tree = parse_file("/test_code/control_flow/fun_def_out_of_scope.fl")

        check_cf = CheckCF()

        self.assertRaises(RuntimeError, check_cf.visit_topdown, tree)

    def test_recursive_fun(self):
        tree = parse_file("/test_code/control_flow/recursive_fun.fl")

        check_cf = CheckCF()

        try:
            check_cf.visit_topdown(tree)
        except Exception:
            self.fail("Unexpected exception raised")

    def test_let_scope(self):
        pass


