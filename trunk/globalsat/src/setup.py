#===============================================================================
# 
# from distutils.core import setup
# import py2exe, os
# 
# #strip subversion files
# def f(x): return x[0] != '.' 
# 
# dir = '..\\src\\exportTemplates\\'
# files = list()
# for template in filter(f, os.listdir("..\\src\\exportTemplates\\")):
#    files.append(dir+template) 
# 
# setup(
#      console = ['..\\src\\gh615_console.py'],
#      data_files = [("exportTemplates",files),("export",[])]
#      #,zipfile = None
#      )
#===============================================================================


# This is a setup.py example script for the use with py2exe
from distutils.core import setup
import py2exe
import sys, os

# #strip subversion files
def f(x): return x[0] != '.' 
# 
dir = '..\\src\\exportTemplates\\'
files = list()
for template in filter(f, os.listdir("..\\src\\exportTemplates\\")):
   files.append(dir+template) 

#this script is only useful for py2exe so just run that distutils command.
#that allows to run it with a simple double click.
sys.argv.append('py2exe')

#get an icon from somewhere.. the python installation should have one:
icon = os.path.join(os.path.dirname(sys.executable), 'py.ico')

setup(
    options = {'py2exe': {
        'excludes': ['javax.comm'],
        'optimize': 2,
        'dist_dir': 'dist',
        }
    },

    name = "wgh615_console",
    console = ['..\\src\\gh615_console.py'],
    zipfile = "stuff.zip",
    
    description = "Simple serial terminal application",
    version = "0.1",
    author = "Chris Liechti",
    author_email = "cliechti@gmx.net",
    url = "http://pyserial.sf.net",
)