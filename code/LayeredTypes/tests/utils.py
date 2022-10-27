import os

from compiler.Compiler import LayeredCompiler


def parse_file(file_path):
    impl_path = os.path.dirname(os.path.realpath(__file__)) + "/implementations.py"
    layer_path = os.path.dirname(os.path.realpath(__file__)) + "/layer_implementations"
    compiler = LayeredCompiler(impl_path, layer_path)

    src_path = os.path.dirname(os.path.realpath(__file__)) + f"{file_path}"
    tree = compiler.parse(src_path)

    return tree
