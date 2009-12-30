from distutils.core import setup

setup(name='stdeb',
      # Keep version in sync with stdeb/__init__.py, Install section
      # of README.rst, and USER_AGENT in scripts/pypi-install.
      version='0.5.0',
      author='Andrew Straw',
      author_email='strawman@astraw.com',
      description='Python to Debian source package conversion utility',
      long_description=\
      """stdeb extends distutils to make Debian source packages from Python
packages. It attempts to provide automatic defaults, but many aspects
of the resulting package can be customized via a configuration file.""",
      license='MIT',
      url='http://github.com/astraw/stdeb',
      packages=['stdeb','stdeb.command'],
      scripts=['scripts/py2dsc',
               'scripts/pypi-install',
               ],
)
