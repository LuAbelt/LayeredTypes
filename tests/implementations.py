from builtins import *

def test(x):
    print(f"Called test with value {x}!")
    return x

def funCall(arg):
    return arg

def fun(arg):
    return arg + 1

def emptyCall():
    return 1337

def twoArgs(first, second):
    return [first , second]

def create(r,c):
    return [r,c]

def threeArgs(first, second, third):
    return [first, second, third]

def f():
    pass

def noArgs():
    return 1

def initList():
    return []

def append(ls, val):
    ls.append(val)
    return ls

def create_list(n: int):
    return list(range(n))
