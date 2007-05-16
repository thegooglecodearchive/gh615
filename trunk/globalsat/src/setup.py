from distutils.core import setup
import py2exe, os

#strip subversion files
def f(x): return x[0] != '.' 

dir = '..\\src\\exportTemplates\\'
files = list()
for template in filter(f, os.listdir("..\\src\\exportTemplates\\")):
    files.append(dir+template) 

setup(
      console = ['..\\src\\serial_test.py'],
      data_files = [("exportTemplates",files),("export",[])]
      )


