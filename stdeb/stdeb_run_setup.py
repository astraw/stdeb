#!/usr/bin/env python
USAGE = """\
stdeb_run_setup - Calls "python setup.py sdist_dsc" ensuring stdeb is available.

usage: stdeb_run_setup [options]


"""

import sys, os
import stdeb

def main():
    f='setup.py'
    sys.argv[0] = f
    sys.argv.insert(1,'sdist_dsc')
    this_dir = os.path.abspath(os.curdir)
    sys.path.insert(0,this_dir) # setuptools-installed scripts don't have this
    execfile(f,{'__name__':'__main__'})

if __name__=='__main__':
    main()
