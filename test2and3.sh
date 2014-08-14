#!/bin/bash
set -e

# setup paths

if [ "${PY2EXE}" == "" ]; then
  PY2EXE=`which python2`;
fi

if [ "${PY3EXE}" == "" ]; then
  PY3EXE=`which python3`;
fi

echo "using Python 2 at ${PY2EXE}"
echo "using Python 3 at ${PY3EXE}"

## Test very basic py2 and py3 packages ------

cd test_data/py2_only_pkg
${PY2EXE} setup.py --command-packages stdeb.command sdist_dsc --with-python2=true --with-python3=false bdist_deb
cd ../..

cd test_data/py3_only_pkg
${PY3EXE} setup.py --command-packages stdeb.command sdist_dsc --with-python3=true --with-python2=false bdist_deb
cd ../..

