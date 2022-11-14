from tests.utils import call_order

def depends_on():
    return {"A"}

def typecheck(tree):
    call_order.append("B")
    return tree

def parse_type(type_str):
    return None