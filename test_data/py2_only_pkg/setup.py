#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup
from distutils.command.build import build
import sys


class my_build(build):
    """ensure (at runtime) we are running python 2"""
    def __init__(self, *args, **kwargs):
        assert sys.version_info[0] == 2
        build.__init__(self, *args, **kwargs)


setup(
    name='py2_only_pkg',
    packages=['py2_only_pkg'],
    version='0.1',
    cmdclass={'build': my_build},
    author='Mister Unicodé',
    author_email='mister.unicode@example.tld',
    description='Python 2 package with Unicodé fields',
    long_description='This is a Python 2 package with Unicodé data.',
)
