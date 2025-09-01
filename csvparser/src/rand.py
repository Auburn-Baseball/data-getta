'''
Python script that shows an example of how to use ctypes to call
a cpp script from a python file

build (cpp file):
    g++ -fPIC -shared -o cppTest.so cppTest.cpp

run:
    python ctypesExample.py

Auth: Micah Key
'''
# Imports
import ctypes
import os

global handle

def Py_Function(csvFileName):
    return handle.Cpp_Parser(csvFileName)


if __name__ == '__main__':
    # Get the shared object file
    handle = ctypes.CDLL("/mnt/d/SchoolStuff/Spring_2024/Senior_Design_Comp_4710/build/libparser.so")

    handle.Cpp_Parser.argtypes = [ctypes.c_char_p]
    fileName = 'test.py'
    val = Py_Function(ctypes.c_char_p(fileName.encode()))
    print(val)