from tests.utils import call_order

def depends_on():
    return { "B", "C"}

def typecheck(tree):
    call_order.append("D")
    return tree

def parse_type(type_str):
    return None