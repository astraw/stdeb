#!/bin/bash
set -e

rm -rf deb_dist

for i in `seq 1 2`; do

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
echo "contents of .deb from $SOURCE_TARBALL in case 1:"
dpkg --contents deb_dist/*.deb

#cleanup case 1
rm -rf deb_dist

# case 2: build from pre-existing source tarball using distutils
# ==============================================================
tar xzf $SOURCE_TARBALL
cd $SOURCE_TARBALL_DIR
python setup.py --command-packages=stdeb.command sdist_dsc
cd deb_dist/$DEBSOURCE
dpkg-buildpackage -rfakeroot -uc -us
cd ..
echo "contents of .deb from $SOURCE_TARBALL in case 2:"
dpkg --contents *.deb
cd ../..

#cleanup case 2
# ==============================================================
rm -rf $SOURCE_TARBALL_DIR


# case 3: build from pre-existing source tarball with py2dsc
# ==============================================================
py2dsc-deb $SOURCE_TARBALL

echo "contents of .deb from $SOURCE_TARBALL in case 3:"
dpkg --contents deb_dist/*.deb

#cleanup case 3
rm -rf deb_dist


#cleanup original tarball
rm -rf $SOURCE_TARBALL

done

echo "All tests passed."
