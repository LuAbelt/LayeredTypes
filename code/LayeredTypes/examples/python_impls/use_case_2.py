from random import randrange
from builtins import len, print

def set_list_element(ls, idx, val):
    ls[idx] = val
    return ls

def get_element(ls, idx):
    return ls[idx]

def get_list():
    # Return list with 12 random elements
    return [randrange( 100) for _ in range(12)]