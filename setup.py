from distutils.core import setup
import os

if int(os.environ.get('STDEB_CHECK_DEBIAN_PYTHON','1')):

    # http://travis-ci.org/ seems to run with a Python not distributed
    # by Ubuntu/Debian and thus misses critical functionality to play
    # nicely with the Debian packaging utilities.

    import distutils.command.install as imod
    opts=[x for x in imod.install.user_options if x[0]=='install-layout=']
    if len(opts)==0:
        raise RuntimeError('Your distutils install command does not support '
                           'the --install-layout option. stdeb will fail.')

setup(name='stdeb',
      # Keep version in sync with stdeb/__init__.py, Install section
      # of README.rst, and USER_AGENT in scripts/pypi-install.
      version='0.7.0',
      author='Andrew Straw',
      author_email='strawman@astraw.com',
      description='Python to Debian source package conversion utility',
      long_description=open('README.rst').read(),
      license='MIT',
      url='http://github.com/astraw/stdeb',
      packages=['stdeb','stdeb.command'],
      scripts=['scripts/py2dsc',
               'scripts/py2dsc-deb',
               'scripts/pypi-download',
               'scripts/pypi-install',
               ],
)
