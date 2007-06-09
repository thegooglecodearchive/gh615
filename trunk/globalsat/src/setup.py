from distutils.core import setup
import py2exe
import sys, os, glob

'''
setup(
     name = "gh615_console",
     console = ['..\\src\\gh615_console.py'],
     data_files = [("exportTemplates",files),("export",[]),("","..\\src\\config.xml")],
     zipfile = "stuff.zip",
     description = "gh615 console",
     version = "0.1",
     author = "Till Hennig",
     #author_email = "cliechti@gmx.net",
     url = "http://code.google.com/p/gh615/"
)
'''

setup(
      console = ['..\\src\\gh615_console.py'],
      #data_files = [("exportTemplates",files),("export",[])],
      data_files = [("",["..\\src\\config.xml"]),("exportTemplates",glob.glob("..\\src\\exportTemplates\\*.txt")),("export",[])],
      zipfile = None,
      description = "gh615 console",
      version = "0.1",
      author = "Till Hennig",
      url = "http://code.google.com/p/gh615/"
      )