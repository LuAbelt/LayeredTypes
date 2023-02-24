import unittest

from tests.utils import parse_file, typecheck_correct_file, get_compiler, full_path


class TestLiquidLayer(unittest.TestCase):
    def test_simple_assign(self):
        typecheck_correct_file(self, "/test_code/liquid/simple_assignment.fl")

    def test_simple_assignment_infer(self):
        typecheck_correct_file(self, "/test_code/liquid/simple_assignment_infer.fl")

    def test_simple_assignment_fail(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/liquid/simple_assignment_fail.fl")

        with self.assertRaises(Exception):
            compiler.typecheck(src_file)

    def test_fun_call(self):
        typecheck_correct_file(self, "/test_code/liquid/fun_call.fl")