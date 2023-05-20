import os

from compiler.Compiler import LayeredCompiler

call_order = []

def full_path(file_path):
    return os.path.dirname(os.path.realpath(__file__)) + f"{file_path}"

def parse_file(file_path):
    compiler = get_compiler()

    src_path = full_path(file_path)
    tree = compiler.parse(src_path)

    return tree

def get_compiler(impl_path = full_path("/implementations.py"), layer_path = full_path("/layer_implementations")):
    compiler = LayeredCompiler(layer_path, impl_path)

    return compiler

def typecheck_correct_file(test, file_path, layers_path = "/../layer_implementations"):
    compiler = get_compiler(layer_path = full_path(layers_path))
    src_file = full_path(file_path)

    compiler.typecheck(src_file)
    # We don't need to do anything here, just make sure it does not throw an exception
    test.assertTrue(True)