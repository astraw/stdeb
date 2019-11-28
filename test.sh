#!/bin/bash
set -e

# setup tests

## remove old build results
rm -rf deb_dist

# setup paths

if [ "${PYEXE}" == "" ]; then
  PYEXE=`which python`;
fi

echo "using Python at ${PYEXE}"

PY2DSC_LOC=`which py2dsc`
PY2DSC_DEB_LOC=`which py2dsc-deb`
PYPI_DOWNLOAD_LOC=`which pypi-download`
PYPI_INSTALL_LOC=`which pypi-install`

PY2DSC="${PYEXE} ${PY2DSC_LOC}"
PY2DSC_DEB="${PYEXE} ${PY2DSC_DEB_LOC}"
PYPI_DOWNLOAD="${PYEXE} ${PYPI_DOWNLOAD_LOC}"
PYPI_INSTALL="${PYEXE} ${PYPI_INSTALL_LOC}"

# Run tests

## Test some basic tests. Just make sure these don't fail.

${PY2DSC} --help > /dev/null
${PY2DSC_DEB} --help > /dev/null
${PYPI_DOWNLOAD} --help > /dev/null
${PYPI_INSTALL} --help > /dev/null

## Run test cases on each of the following packages

# Set an upper bound on the size of the compressed deb_specific. We are not
# applying any patches here so this should be pretty small.
MAX_DEB_SPECIFIC_SIZE=5000

for i in `seq 1 3`; do
if [ $i -eq "1" ]; then
SOURCE_PACKAGE=requests
SOURCE_RELEASE=2.6.0
SOURCE_TARBALL_DIR=${SOURCE_PACKAGE}-${SOURCE_RELEASE}
SOURCE_TARBALL=${SOURCE_TARBALL_DIR}.tar.gz
DEBSOURCE=${SOURCE_TARBALL_DIR}
elif [ $i -eq "2" ]; then
SOURCE_PACKAGE=Reindent
SOURCE_RELEASE=0.1.1
SOURCE_TARBALL_DIR=${SOURCE_PACKAGE}-${SOURCE_RELEASE}
SOURCE_TARBALL=${SOURCE_TARBALL_DIR}.tar.gz
DEBSOURCE=reindent-${SOURCE_RELEASE}
elif [ $i -eq "3" ]; then
SOURCE_PACKAGE=psycopg2
SOURCE_RELEASE=2.7
SOURCE_TARBALL_DIR=${SOURCE_PACKAGE}-${SOURCE_RELEASE}
SOURCE_TARBALL=${SOURCE_TARBALL_DIR}.tar.gz
DEBSOURCE=${SOURCE_TARBALL_DIR}
else
    echo "unknown case"
    exit 1
fi

export DEB_BUILD_OPTIONS=nocheck # psycopg2 tests fail

# get a file to work with
# ==============================================================
${PYPI_DOWNLOAD} ${SOURCE_PACKAGE} --release ${SOURCE_RELEASE}

# case 1: build from pre-existing source tarball with py2dsc
# ==============================================================
${PY2DSC} $SOURCE_TARBALL

cd deb_dist/$DEBSOURCE
dpkg-buildpackage -rfakeroot -uc -us
cd ../..
for DEBFILE in deb_dist/*.deb; do
  echo "contents of $DEBFILE from $SOURCE_TARBALL in case 1:"
  dpkg --contents $DEBFILE
done
DEB_SPECIFIC_SIZE=$(stat -c '%s' deb_dist/*.debian.tar.?z)
if ((${DEB_SPECIFIC_SIZE}>${MAX_DEB_SPECIFIC_SIZE})); then
    echo "ERROR: debian specific file larger than expected"
    exit 1
else
    echo "${SOURCE_PACKAGE} case 1: deb_specific size ${DEB_SPECIFIC_SIZE}"
fi

#cleanup case 1
rm -rf deb_dist

# case 2: build from pre-existing source tarball using distutils
# ==============================================================
tar xzf $SOURCE_TARBALL
cd $SOURCE_TARBALL_DIR
which python
python -c "import sys; print('sys.version',sys.version)"
python setup.py --command-packages=stdeb.command sdist_dsc
cd deb_dist/$DEBSOURCE
dpkg-buildpackage -rfakeroot -uc -us
cd ../..
for DEBFILE in deb_dist/*.deb; do
  echo "contents of $DEBFILE from $SOURCE_TARBALL in case 2:"
  dpkg --contents $DEBFILE
done
DEB_SPECIFIC_SIZE=$(stat -c '%s' deb_dist/*.debian.tar.?z)
if ((${DEB_SPECIFIC_SIZE}>${MAX_DEB_SPECIFIC_SIZE})); then
    echo "ERROR: debian specific file larger than expected"
    exit 1
else
    echo "${SOURCE_PACKAGE} case 2: deb_specific size ${DEB_SPECIFIC_SIZE}"
fi
cd ..

#cleanup case 2
# ==============================================================
rm -rf $SOURCE_TARBALL_DIR


# case 3: build from pre-existing source tarball with py2dsc
# ==============================================================
${PY2DSC_DEB} $SOURCE_TARBALL

for DEBFILE in deb_dist/*.deb; do
  echo "contents of $DEBFILE from $SOURCE_TARBALL in case 3:"
  dpkg --contents $DEBFILE
done
DEB_SPECIFIC_SIZE=$(stat -c '%s' deb_dist/*.debian.tar.?z)
if ((${DEB_SPECIFIC_SIZE}>${MAX_DEB_SPECIFIC_SIZE})); then
    echo "ERROR: debian specific file larger than expected"
    exit 1
else
    echo "${SOURCE_PACKAGE} case 3: deb_specific size ${DEB_SPECIFIC_SIZE}"
fi

#cleanup case 3
rm -rf deb_dist


#cleanup original tarball
rm -rf $SOURCE_TARBALL

done

echo "All tests passed."
