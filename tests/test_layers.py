import unittest
from graphlib import CycleError

from compiler.Compiler import LayerVerificationState
from utils import get_compiler, full_path, call_order

class TestLayerDefinitions(unittest.TestCase):

    def test_single_definition(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/layers/single_layer_def.fl")
        compiler.typecheck(src_file)

        self.assertEqual(len(compiler.layers), 1)
        self.assertTrue("base" in compiler.layers)

    def test_multiple_definitions(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/layers/multiple_layers.fl")
        compiler.typecheck(src_file)

        self.assertEqual(len(compiler.layers), 2)
        self.assertTrue("base" in compiler.layers)
        self.assertTrue("other" in compiler.layers)

    def test_missing_layer(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/layers/non_existant_layer.fl")
        with self.assertRaises(FileNotFoundError):
            compiler.typecheck(src_file)
        pass


class TestLayerDependencies(unittest.TestCase):

    def test_simple_dependency(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/layers/simple_dependency.fl")

        call_order.clear()

        compiler.typecheck(src_file)

        self.assertEqual(len(compiler.layers), 2)
        self.assertTrue("A" in compiler.layers)
        self.assertTrue("B" in compiler.layers)

        self.assertEqual(call_order, ["A", "B"])
        pass

    def test_multiple_dependencies(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/layers/proper_dependency.fl")

        call_order.clear()

        compiler.typecheck(src_file)

        self.assertEqual(len(compiler.layers), 4)
        self.assertTrue("A" in compiler.layers)
        self.assertTrue("B" in compiler.layers)
        self.assertTrue("C" in compiler.layers)
        self.assertTrue("D" in compiler.layers)

        self.assertIn(call_order, [["A", "B", "C", "D"],["A", "C", "B", "D"]])

    def test_circular_dependency(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/layers/create_cycle.fl")

        with self.assertRaises(CycleError):
            compiler.typecheck(src_file)

    def test_circular_dependency_2(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/layers/create_cycle.fl")

        compiler.typecheck(src_file, raise_on_error=False)

        self.assertEqual(compiler.layer_states["cycleA"], LayerVerificationState.CYCLE)
        self.assertEqual(compiler.layer_states["cycleB"], LayerVerificationState.CYCLE)

    def test_implicit_dependency(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/layers/implicit_dependency.fl")

        call_order.clear()

        with self.assertWarns(UserWarning):
            compiler.typecheck(src_file)

        self.assertEqual(len(compiler.layers), 2)
        self.assertTrue("A" in compiler.layers)
        self.assertTrue("B" in compiler.layers)

        self.assertEqual(["A", "B"], call_order)

    def test_implicit_cycle(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/layers/implicit_cycle.fl")

        with self.assertRaises(CycleError) as e:
            compiler.typecheck(src_file)

    def test_implicit_cycle_2(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/layers/implicit_cycle.fl")

        compiler.typecheck(src_file, raise_on_error=False)

        self.assertEqual(compiler.layer_states["cycleA"], LayerVerificationState.CYCLE)
        self.assertEqual(compiler.layer_states["cycleB"], LayerVerificationState.CYCLE)

    def test_implicit_multiple_layers(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/layers/implicit_multiple_layers.fl")

        call_order.clear()

        with self.assertWarns(UserWarning):
            compiler.typecheck(src_file)

        self.assertEqual(len(compiler.layers), 4)
        self.assertTrue("A" in compiler.layers)
        self.assertTrue("B" in compiler.layers)
        self.assertTrue("C" in compiler.layers)
        self.assertTrue("D" in compiler.layers)

        self.assertIn(call_order, [["A", "B", "C", "D"], ["A", "C", "B", "D"]])

    def test_complex_layers(self):
        compiler = get_compiler()
        src_file = full_path("/test_code/layers/complex_layers.fl")

        call_order.clear()

        compiler.typecheck(src_file, raise_on_error=False)

        self.assertEqual(LayerVerificationState.SUCCESS, compiler.layer_states["A"])
        self.assertEqual(LayerVerificationState.SUCCESS, compiler.layer_states["B"])
        self.assertEqual(LayerVerificationState.SUCCESS, compiler.layer_states["C"])
        self.assertEqual(LayerVerificationState.SUCCESS, compiler.layer_states["D"])
        self.assertEqual(LayerVerificationState.CYCLE, compiler.layer_states["cycleA"])
        self.assertEqual(LayerVerificationState.CYCLE, compiler.layer_states["cycleB"])
        self.assertEqual(LayerVerificationState.FAILURE, compiler.layer_states["failLayerA"])
        self.assertEqual(LayerVerificationState.BLOCKED, compiler.layer_states["blockedLayerB"])
        self.assertEqual(LayerVerificationState.BLOCKED, compiler.layer_states["blockedLayerC"])
        self.assertEqual(LayerVerificationState.CYCLE_BLOCKED, compiler.layer_states["dependOnCycleA"])

