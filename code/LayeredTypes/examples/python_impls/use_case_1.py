from builtins import len, print, open
from pathlib import Path

class FileDescriptor:
    def __init__(self, filename):
        self._filename = filename
        self._filehandle = None

    def open(self):
        if self._filehandle is not None:
            raise Exception("File already open")
        self._filehandle = open(self._filename, "r")

    def close(self):
        if self._filehandle is None:
            raise Exception("File not open")
        self._filehandle.close()
        self._filehandle = None

    def read(self):
        if self._filehandle is None:
            raise Exception("File not open")

        # Check if the file still has data to read
        pos = self._filehandle.tell()
        if pos == self._filehandle.seek(0, 2):
            raise Exception("File has no more data to read")

        # Seek back to the previous position
        self._filehandle.seek(pos)
        return self._filehandle.readlines()
def createFD(filename:str) -> FileDescriptor:
    return FileDescriptor(filename)
def openFile(fileHandle: FileDescriptor):
    fileHandle.open()

def closeFile(filehandle: FileDescriptor):
    filehandle.close()
def strToInt(s:str) -> int:
    return int(s)

def getLine(lines:list, i:int) -> str:
    return lines[i]

# Create a function that takes an open filehandle and returns a list of lines
def readLines(filehandle: FileDescriptor) -> list:
    return filehandle.read()