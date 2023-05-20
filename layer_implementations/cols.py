from compiler.interpreters import LiquidTypeChecker

def typecheck(tree):
    liquid_checker = LiquidTypeChecker.LiquidLayer(layer_identifier="cols")
    liquid_checker.visit(tree)

    return tree
