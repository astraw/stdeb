from distutils.core import setup
import codecs

f = codecs.open('README.rst', encoding='utf-8')
long_description = '\n'.join( [line for line in f] )
f.close()
del f

setup(name='stdeb',
      # Keep version in sync with stdeb/__init__.py, Install section
      # of README.rst, and USER_AGENT in scripts/pypi-install.
      version='0.8.1',
      author='Andrew Straw',
      author_email='strawman@astraw.com',
      description='Python to Debian source package conversion utility',
      long_description=long_description,
      license='MIT',
      url='http://github.com/astraw/stdeb',
      packages=['stdeb','stdeb.command'],
      scripts=['scripts/py2dsc',
               'scripts/py2dsc-deb',
               'scripts/pypi-download',
               'scripts/pypi-install',
               ],
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
)
