import unittest

from compiler.transformers.CheckCF import CheckCF
from tests.utils import parse_file


class TestControlFlow(unittest.TestCase):
    def test_undefined_ident(self):
        tree1 = parse_file("/test_code/control_flow/undefined_ident.fl")
        tree2 = parse_file("/test_code/control_flow/undefined_ident_2.fl")

        check_cf = CheckCF()

        with self.assertRaises(SyntaxError) as context:
            check_cf.visit_topdown(tree1)

        self.assertEqual(context.exception.lineno, 1)
        self.assertEqual(context.exception.offset, 1)
        self.assertEqual(context.exception.end_lineno, 1)
        self.assertEqual(context.exception.end_offset, 10)

        with self.assertRaises(SyntaxError) as context:
            check_cf.visit_topdown(tree2)

        self.assertEqual(context.exception.lineno, 3)
        self.assertEqual(context.exception.offset, 14)
        self.assertEqual(context.exception.end_lineno, 3)
        self.assertEqual(context.exception.end_offset, 24)

    def test_undefined_ident_in_if(self):
        tree = parse_file("/test_code/control_flow/undef_id_if.fl")

        check_cf = CheckCF()

        with self.assertRaises(SyntaxError) as context:
            check_cf.visit_topdown(tree)

        self.assertEqual(context.exception.lineno, 7)
        self.assertEqual(context.exception.offset, 4)
        self.assertEqual(context.exception.end_lineno, 7)
        self.assertEqual(context.exception.end_offset, 5)

    def test_function_usage_before_def(self):
        tree = parse_file("/test_code/control_flow/fun_usage_before_def.fl")

        check_cf = CheckCF()

        self.assertWarns(RuntimeWarning, check_cf.visit_topdown, tree)

    def test_function_def_scope(self):
        tree = parse_file("/test_code/control_flow/fun_def_out_of_scope.fl")

        check_cf = CheckCF()

        with self.assertRaises(SyntaxError) as context:
            check_cf.visit_topdown(tree)

        self.assertEqual(context.exception.lineno, 5)
        self.assertEqual(context.exception.offset, 1)
        self.assertEqual(context.exception.end_lineno, 5)
        self.assertEqual(context.exception.end_offset, 2)

    def test_recursive_fun(self):
        tree = parse_file("/test_code/control_flow/recursive_fun.fl")

        check_cf = CheckCF()

        try:
            check_cf.visit_topdown(tree)
        except Exception:
            self.fail("Unexpected exception raised")

    def test_let_in_scope(self):
        tree = parse_file("/test_code/control_flow/let_in_scope.fl")

        check_cf = CheckCF()

        try:
            check_cf.visit_topdown(tree)
        except Exception:
            self.fail("Unexpected exception raised")


    def test_let_out_of_scope(self):
        tree = parse_file("/test_code/control_flow/let_out_of_scope.fl")

        check_cf = CheckCF()

        with self.assertRaises(SyntaxError) as context:
            check_cf.visit_topdown(tree)

        self.assertEqual(context.exception.lineno, 5)
        self.assertEqual(context.exception.offset, 1)
        self.assertEqual(context.exception.end_lineno, 5)
        self.assertEqual(context.exception.end_offset, 2)

    def test_let_already_defined(self):
        tree = parse_file("/test_code/control_flow/let_already_defined.fl")

        check_cf = CheckCF()

        with self.assertRaises(SyntaxError) as context:
            check_cf.visit_topdown(tree)

        self.assertEqual(context.exception.lineno, 3)
        self.assertEqual(context.exception.offset, 5)
        self.assertEqual(context.exception.end_lineno, 3)
        self.assertEqual(context.exception.end_offset, 6)