import setuptools
from setuptools import setup

from distutils.util import convert_path
d = {}; execfile(convert_path('stdeb/command/__init__.py'),d)
SETUP_COMMANDS = d['__all__']

setup(name='stdeb',
      version='0.0.1',
      author='Andrew Straw',
      author_email='strawman@astraw.com',
      description='Python to Debian source package conversion utility',
      long_description="""stdeb is a distutils command to Debian source packages from Python
packages. It attempts to provide automatic defaults, but many aspects
of the resulting package can be customized via a simple config file.""",
      license='MIT',
      homepage='http://stdeb.python-hosting.com/',
      packages=setuptools.find_packages(),

      # register ourselves (using setuptools) with distutils:
      entry_points = {
    'distutils.commands':[
    "%(cmd)s = stdeb.command.%(cmd)s:%(cmd)s" % locals()
    for cmd in SETUP_COMMANDS
    ],
    },
      )
