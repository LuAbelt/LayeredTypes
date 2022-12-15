import os
from optparse import OptionParser

from compiler.Compiler import LayeredCompiler

if __name__ == "__main__":
    parser = OptionParser()

    parser.add_option("-f", "--file", action="store", dest="filename", help="File to compile")
    parser.add_option("-t","--typecheck", action="store_true", dest="typecheck", help="Only typecheck the program")
    parser.add_option("-i","--impls", action="store", dest="impls", help="File containing implementations")
    parser.add_option("-l","--layers", action="store", dest="layers", help="Directory containing layers")

    (options, args) = parser.parse_args()

    if options.filename is None:
        parser.error("No filename given")

    if options.impls is None:
        parser.error("No implementations file given")

    if options.layers is None:
        parser.error("No layers directory given")

    compiler = LayeredCompiler(os.path.abspath(options.impls), os.path.abspath(options.layers))

    cwd = os.getcwd()

    file = os.path.abspath(options.filename)
    os.chdir(os.path.dirname(os.path.abspath(options.filename)))

    try:
        if options.typecheck:
            compiler.typecheck(file)
        else:
            result = compiler.run(file)
            print(f"Program returned: {result}")
    finally:
        os.chdir(cwd)

