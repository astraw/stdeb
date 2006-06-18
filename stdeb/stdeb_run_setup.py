#!/usr/bin/env python
USAGE = """\
usage: stdeb_run_setup [options]


"""

import sys
import stdeb

def main():
    f='setup.py'
    sys.argv[0] = f
    sys.argv.insert(1,'sdist_dsc')
    execfile(f,{'__name__':'__main__'})

if __name__=='__main__':
    main()
