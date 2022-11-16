from tests.utils import call_order

def depends_on():
    return set()

def typecheck(tree, annotations, layer_refinements):
    call_order.append("A")
    return tree, annotations

def parse_type(type_str):
    return None