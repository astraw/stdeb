#!/bin/bash
set -e

if [ "$UID" -ne "0" ]; then
  echo "$0 must be run as root"
  exit 1
fi

# Package with source tarball on PyPI:
pypi-install pyflakes --verbose=2
dpkg --purge python-pyflakes

# Package with no source tarball on PyPI: (v 0.6.2, 2009-12-30)
pypi-install posix_ipc --verbose=2
dpkg --purge python-posixipc

echo "skipping known failure tests"
exit 0

# Known failing tests: A pure python package with source zip on
#  PyPI. (This fails because stdeb doesn't handle .zip source
#  archives.)
pypi-install zope.site --verbose=2

#  A pure python package with source tarball on PyPI.  (This fails if
#   the Debian/Ubuntu original "pyro" package is already
#   installed. This should use apt-file to find that binary package is
#   "pyro".)
apt-get install pyro # get upstream version
pypi-install Pyro --verbose=2
