#!/bin/bash
set -e

rm -rf deb_dist

for i in `seq 1 2`; do

if [ $i -eq "1" ]; then
SOURCE_URL=http://astraw.com/misc_files/simplepack-8.0.1+r23437.tar.gz
SOURCE_TARBALL=simplepack-8.0.1+r23437.tar.gz
SOURCE_TARBALL_DIR=simplepack-8.0.1+r23437
DEBSOURCE=simplepack-8.0.1+r23437
elif [ $i -eq "2" ]; then
SOURCE_URL=http://pypi.python.org/packages/source/R/Reindent/Reindent-0.1.0.tar.gz
SOURCE_TARBALL=Reindent-0.1.0.tar.gz
SOURCE_TARBALL_DIR=Reindent-0.1.0
DEBSOURCE=reindent-0.1.0
else
    echo "unknown case"
    exit 1
fi

# get a file to work with
# ==============================================================
wget $SOURCE_URL

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
