import setuptools
from setuptools import setup

import stdeb

setup(name='stdeb',
      version=stdeb.__version__,
      author='Andrew Straw',
      author_email='strawman@astraw.com',
      description='Python to Debian source package conversion utility',
      long_description=\
      """stdeb extends distutils to make Debian source packages from Python
packages. It attempts to provide automatic defaults, but many aspects
of the resulting package can be customized via a configuration file.""",
      license='MIT',
      url='http://github.com/astraw/stdeb',
      packages=setuptools.find_packages(),

      # register ourselves (using setuptools) with distutils:
      entry_points = {
        'distutils.commands':['sdist_dsc = stdeb.command.sdist_dsc:sdist_dsc',
                              'bdist_deb = stdeb.command.bdist_deb:bdist_deb',
                              ],
        'console_scripts':['py2dsc = stdeb.py2dsc:main',
                           'stdeb_run_setup = stdeb.stdeb_run_setup:main']
      },
)
