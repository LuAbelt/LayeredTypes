from compiler.interpreters import LiquidTypeChecker

def depends_on():
    return {"rows","cols"}
def typecheck(tree):
    liquid_checker = LiquidTypeChecker.LiquidLayer(layer_identifier="rowcols", additional_contexts={"rows", "cols"})
    liquid_checker.visit(tree)

    return tree
