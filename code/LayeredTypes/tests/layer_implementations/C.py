from utils import call_order

def depends_on():
    return {"A"}

def typecheck(tree):
    call_order.append("C")
    return tree

def parse_type(type_str):
    return None