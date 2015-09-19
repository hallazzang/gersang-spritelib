from distutils.core import setup, Extension

setup(name='cspritelib',
      version='1.1.0',
      ext_modules=[Extension('cspritelib', ['cspritelib.c'])]
)