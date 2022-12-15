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
    compiler = LayeredCompiler(impl_path, layer_path)

    return compiler