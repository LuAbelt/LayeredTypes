from os import O_RDWR

from builtins import len, print, open

def openFile(filename:str):
    return open(filename, "r")

def closeFile(filehandle):
    filehandle.close()
def strToInt(s:str) -> int:
    return int(s)

def getLine(lines:list, i:int) -> str:
    return lines[i]

# Create a function that takes an open filehandle and returns a list of lines
def readLines(filehandle) -> list:
    return filehandle.readlines()