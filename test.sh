#!/bin/bash
set -e

# setup tests

## remove old build results
rm -rf deb_dist

# Run tests

## Test some basic tests. Just make sure these don't fail.

py2dsc --help > /dev/null
py2dsc-deb --help > /dev/null
pypi-download --help > /dev/null
pypi-install --help > /dev/null

## Run test cases on each of the following packages

# Set an upper bound on the size of the compressed diff. We are not
# applying any patches here so this should be pretty small.
MAX_DIFF_SIZE=5000

for i in `seq 1 3`; do
if [ $i -eq "1" ]; then
SOURCE_PACKAGE=requests
SOURCE_RELEASE=2.2.1
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
SOURCE_PACKAGE=lxml
SOURCE_RELEASE=3.3.5
SOURCE_TARBALL_DIR=${SOURCE_PACKAGE}-${SOURCE_RELEASE}
SOURCE_TARBALL=${SOURCE_TARBALL_DIR}.tar.gz
DEBSOURCE=${SOURCE_TARBALL_DIR}
else
    echo "unknown case"
    exit 1
fi

# get a file to work with
# ==============================================================
pypi-download ${SOURCE_PACKAGE} --release ${SOURCE_RELEASE}

# case 1: build from pre-existing source tarball with py2dsc
# ==============================================================
py2dsc $SOURCE_TARBALL

cd deb_dist/$DEBSOURCE
dpkg-buildpackage -rfakeroot -uc -us
cd ../..
for DEBFILE in deb_dist/*.deb; do
  echo "contents of $DEBFILE from $SOURCE_TARBALL in case 1:"
  dpkg --contents $DEBFILE
done
DIFF_SIZE=$(stat -c '%s' deb_dist/*.diff.gz)
if ((${DIFF_SIZE}>${MAX_DIFF_SIZE})); then
    echo "ERROR: diff file larger than expected"
    exit 1
else
    echo "${SOURCE_PACKAGE} case 1: diff size ${DIFF_SIZE}"
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
  echo "contents of $DEBFILE from $SOURCE_TARBALL in case 1:"
  dpkg --contents $DEBFILE
done
DIFF_SIZE=$(stat -c '%s' deb_dist/*.diff.gz)
if ((${DIFF_SIZE}>${MAX_DIFF_SIZE})); then
    echo "ERROR: diff file larger than expected"
    exit 1
else
    echo "${SOURCE_PACKAGE} case 2: diff size ${DIFF_SIZE}"
fi
cd ..

#cleanup case 2
# ==============================================================
rm -rf $SOURCE_TARBALL_DIR


# case 3: build from pre-existing source tarball with py2dsc
# ==============================================================
py2dsc-deb $SOURCE_TARBALL

for DEBFILE in deb_dist/*.deb; do
  echo "contents of $DEBFILE from $SOURCE_TARBALL in case 1:"
  dpkg --contents $DEBFILE
done
DIFF_SIZE=$(stat -c '%s' deb_dist/*.diff.gz)
if ((${DIFF_SIZE}>${MAX_DIFF_SIZE})); then
    echo "ERROR: diff file larger than expected"
    exit 1
else
    echo "${SOURCE_PACKAGE} case 3: diff size ${DIFF_SIZE}"
fi

#cleanup case 3
rm -rf deb_dist


#cleanup original tarball
rm -rf $SOURCE_TARBALL

done

echo "All tests passed."
