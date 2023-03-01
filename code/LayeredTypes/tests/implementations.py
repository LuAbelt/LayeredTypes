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

def threeArgs(first, second, third):
    return [first, second, third]

def f():
    pass

def noArgs():
    return 1
