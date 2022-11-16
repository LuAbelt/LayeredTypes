from tests.utils import call_order

def depends_on():
    return { "B", "C"}

def typecheck(tree, annotations, layer_refinements):
    call_order.append("D")
    return tree, annotations

def parse_type(type_str):
    return None