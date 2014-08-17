#!/bin/bash
set -e

export DO_PY2=true
export DO_PY3=true

# setup paths

if [ "${PY2EXE}" == "" ]; then
  PY2EXE=`which python2` || export DO_PY2=false
fi

if [ "${PY3EXE}" == "" ]; then
  PY3EXE=`which python3` || export DO_PY3=false
fi

# check that stdeb is actually installed
cd test_data # do test in path without stdeb source
if [ "$DO_PY2" = true ]; then
    ${PY2EXE} -c "import stdeb; print stdeb.__version__,stdeb.__file__" || export DO_PY2=false
fi

if [ "$DO_PY3" = true ]; then
    ${PY3EXE} -c "import stdeb; print(stdeb.__version__,stdeb.__file__)" || export DO_PY3=false
fi
cd ..


# --------------

PYTHONS=""
if [ "$DO_PY2" = true ]; then
    PYTHONS="${PYTHONS} ${PY2EXE}"
fi

if [ "$DO_PY3" = true ]; then
    PYTHONS="${PYTHONS} ${PY3EXE}"
fi

## ----------------------------

# Test unicode in CLI args

for WITH_CLI_MAINTAINER_ARGS in true false; do
#for WITH_CLI_MAINTAINER_ARGS in true; do
    for PYTHON in ${PYTHONS}; do

        echo ${PYTHON} WITH_CLI_MAINTAINER_ARGS ${WITH_CLI_MAINTAINER_ARGS}

        if [ "$WITH_CLI_MAINTAINER_ARGS" = true ]; then
            M1="--maintainer"
            M2="Herr Unicöde <herr.unicoede@example.tld>"
            M3="${M1},${M2}"
        else
            M3=""
        fi

        cd test_data/simple_pkg
        IFS=,
        ${PYTHON} setup.py --command-packages stdeb.command sdist_dsc ${M3} bdist_deb
        unset IFS
        cd ../..
    done
done

## -------------------------

## Tell Python that we do not have e.g. UTF-8 file encodings and thus
## force everything to be very explicit.
export LC_ALL="C"

## Test very basic py2 and py3 packages ------

if [ "$DO_PY2" = true ]; then
    echo "using Python 2 at ${PY2EXE}"
    cd test_data/py2_only_pkg
    ${PY2EXE} setup.py --command-packages stdeb.command sdist_dsc --with-python2=true --with-python3=false bdist_deb
    cd ../..
else
    echo "skipping Python 2 test"
fi

if [ "$DO_PY3" = true ]; then
    echo "using Python 3 at ${PY3EXE}"
    cd test_data/py3_only_pkg
    ${PY3EXE} setup.py --command-packages stdeb.command sdist_dsc --with-python3=true --with-python2=false bdist_deb
    cd ../..
else
    echo "skipping Python 3 test"
fi
