from builtins import *

def test(x):
    print(f"Called test with value {x}!")
    return x

def funCall(arg):
    return arg

def emptyCall():
    return 1337

def twoArgs(first, second):
    return [first, second]

def threeArgs(first, second, third):
    return [first, second, third]
