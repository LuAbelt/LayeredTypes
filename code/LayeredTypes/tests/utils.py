import os

from compiler.Compiler import LayeredCompiler


def parse_file(file_path):
    compiler = get_compiler()

    src_path = os.path.dirname(os.path.realpath(__file__)) + f"{file_path}"
    tree = compiler.parse(src_path)

    return tree

def get_compiler():
    impl_path = os.path.dirname(os.path.realpath(__file__)) + "/implementations.py"
    layer_path = os.path.dirname(os.path.realpath(__file__)) + "/layer_implementations"
    compiler = LayeredCompiler(impl_path, layer_path)

    return compiler