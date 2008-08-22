from distutils.core import setup
import py2exe
import sys, os, glob

setup(
      console = ['..\\src\\gh615_console.py'],
      data_files = [
                    ("", ["..\\src\\config.ini"]),
                    ("", ["..\\src\\README"]),
                    #("", ["..\\src\\cherrypy.conf"]),
                    ("exportTemplates", glob.glob("..\\src\\exportTemplates\\*.txt")),
                    ("exportTemplates", ['..\\src\\exportTemplates\\formats.ini']),
                    ("exportTemplates\\pre", glob.glob("..\\src\\exportTemplates\\pre\\*.py")),
                    
                    #("gui", glob.glob("..\\src\\gui\\*.*")),
                    #    ("gui\\waypoints", glob.glob("..\\src\\gui\\waypoints\\*.*")),
                    #    ("gui\\tracks", glob.glob("..\\src\\gui\\tracks\\*.*")),
                    ("export", []),
                    ("import", [])
      ],
      
      options = { 'py2exe': {
        "compressed": 1,
        "optimize": 1,
        "bundle_files": 1, #3 = many files, 1 = bundled into exe
#        'packages': ["email"],
        'excludes': ["image","OpenSSL","Tkconstants","Tkinter","tcl"]
         }
      },
      #comment out to package into exe
      #zipfile = None,
      zipfile = 'libraries',
      
      description = "GH615",
      version = "0.1",
      author = "Till Hennig",
      url = "http://code.google.com/p/gh615/"
      )