# This is a simple layer that performs some rudimentary typechecking.
# It supports the following types:
# - int
# - short
# - long
# - byte
# - float
# - double
# - bool
# - str
#
# We assume that narrowing conversions are allowed, but not widening conversions.

def depends_on():
    return set()

def typecheck(tree, annotations, layer_refinements):

    return tree, annotations

def parse_type(type_str : str):
    return None
