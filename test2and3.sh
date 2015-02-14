#!/bin/bash
set -e

export DO_PY2=true
export DO_PY3=true

# setup paths

if [ "${PY2EXE}" == "" ]; then
  PY2EXE=`which python2` || echo
  if [ "${PY2EXE}" == "" ]; then
    PY2EXE=`which python` || export DO_PY2=false
  fi
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

# Test unicode in CLI args and .cfg file

for MAINTAINER_ARGS in cli none cfgfile; do
    for PYTHON in ${PYTHONS}; do

        echo ${PYTHON} MAINTAINER_ARGS ${MAINTAINER_ARGS}

        if [ "$MAINTAINER_ARGS" = cli ]; then
            M1="--maintainer"
            M2="Herr Unicöde <herr.unicoede@example.tld>"
            M3="${M1},${M2}"
        else
            M3=""
        fi

        rm -f test_data/simple_pkg/stdeb.cfg

        if [ "$MAINTAINER_ARGS" = cfgfile ]; then
            cat > test_data/simple_pkg/stdeb.cfg <<EOF
[DEFAULT]
maintainer=Frau Unicöde <frau.unicoede@example.tld>
EOF
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

    # test the "debianize" command
    rm -rf debian
    ${PY2EXE} setup.py --command-packages stdeb.command debianize
    rm -rf debian

    # test the "sdist_dsc" and "bdist_deb" commands
    ${PY2EXE} setup.py --command-packages stdeb.command sdist_dsc --with-python2=true --with-python3=false bdist_deb
    cd ../..
else
    echo "skipping Python 2 test"
fi


if [ "$DO_PY3" = true ]; then
    # Due to http://bugs.python.org/issue9561 (fixed in Py 3.2) we skip this test in 3.0 and 3.1.
    ${PY3EXE} -c "import sys; ec=0 if sys.version_info[1]>=2 else 1; sys.exit(ec)"  && rc=$? || rc=$?

    if [ "$rc" == 0 ]; then

      echo "using Python 3 at ${PY3EXE}"
      cd test_data/py3_only_pkg

      # test the "debianize" command
      rm -rf debian
      ${PY3EXE} setup.py --command-packages stdeb.command debianize
      rm -rf debian

      # test the "sdist_dsc" and "bdist_deb" commands
      ${PY3EXE} setup.py --command-packages stdeb.command sdist_dsc --with-python3=true --with-python2=false bdist_deb
      cd ../..
    else
      echo "skipping Python >= 3.2 test"
    fi
else
    echo "skipping Python 3 test"
fi
