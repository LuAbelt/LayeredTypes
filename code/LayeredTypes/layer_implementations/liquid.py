from compiler.interpreters import LiquidTypeChecker

def typecheck(tree):
    liquid_checker = LiquidTypeChecker.LiquidLayer()
    liquid_checker.visit(tree)

    return tree
