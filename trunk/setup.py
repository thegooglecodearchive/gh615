from distutils.core import setup
import py2exe
import sys, os, glob

setup(
      console = ['..\\src\\gh615_console.py'],
      #data_files = [("exportTemplates",files),("export",[])],
      data_files = [("",["..\\src\\config.ini"]),("exportTemplates",glob.glob("..\\src\\exportTemplates\\*.txt")),("export",[])],
      zipfile = None,
      description = "gh615 console",
      version = "0.1",
      author = "Till Hennig",
      url = "http://code.google.com/p/gh615/"
      )