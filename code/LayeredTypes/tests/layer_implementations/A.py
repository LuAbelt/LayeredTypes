from tests.utils import call_order

def depends_on():
    return set()

def typecheck(tree):
    call_order.append("A")
    return tree

def parse_type(type_str):
    return None