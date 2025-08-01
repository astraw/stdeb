#!/bin/bash
set -e

if [ "$UID" -ne "0" ]; then
  echo "$0 must be run as root"
  exit 1
fi

# Package with source tarball on PyPI:
# Later versions of pyflakes fail to build on Ubuntu Focal

ROS_PKG_DEPS=(python3-{dateutil,distro,docutils,pyparsing,vcstools,yaml})

apt-get install -y ${ROS_PKG_DEPS[@]} --no-install-recommends 
pypi-install catkin_pkg --verbose=2
pypi-install rospkg --verbose=2
pypi-install rosdistro --verbose=2
pypi-install rosdep --verbose=2
env DEB_BUILD_OPTIONS=nocheck pypi-install bloom --verbose=2 --release=0.13.0
dpkg --purge ${ROS_PKG_DEPS[@]} python3-{catkin-pkg,rosdistro,rospkg,rosdep,bloom}

# This test fails on Ubuntu 12.04 due to what looks like a bug with
# "dh_auto_clean -O--buildsystem=python_distutils" not changing into the
# directory with setup.py and thus its "import prober" fails. That's not
# an stdeb bug. We could run this test on later versions of Debian/Ubuntu.
#
# Package with no source tarball on PyPI: (v 0.6.2, 2009-12-30)
#pypi-install posix_ipc --release=0.6.2 --verbose=2 --allow-unsafe-download
#dpkg --purge python-posixipc

echo "skipping known failure tests"
exit 0

#  A pure python package with source tarball on PyPI.  (This fails if
#   the Debian/Ubuntu original "pyro" package is already
#   installed. This should use apt-file to find that binary package is
#   "pyro".)
apt-get install pyro # get upstream version
pypi-install Pyro --verbose=2
