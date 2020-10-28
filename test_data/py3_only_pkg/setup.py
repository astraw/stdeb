#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from distutils.core import setup
from distutils.command.build import build
import sys


class my_build(build):
    """ensure (at runtime) we are running python 3"""
    def __init__(self, *args, **kwargs):
        assert sys.version_info[0] == 3
        build.__init__(self, *args, **kwargs)


setup(
    name='py3_only_pkg',
    packages=['py3_only_pkg'],
    version='0.1',
    cmdclass={'build': my_build},
    author='Mister Unicodé',
    author_email='mister.unicode@example.tld',
    description='Python 3 package with Unicodé fields',
    long_description='This is a Python 3 package with Unicodé data.',
)
