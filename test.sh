#!/bin/bash

rm -rf deb_dist

for i in `seq 1 3`; do

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
elif [ $i -eq "3" ]; then
SOURCE_URL=http://astraw.com/misc_files/twisted-svn-r23437.tar.gz
SOURCE_TARBALL=twisted-svn-r23437.tar.gz
SOURCE_TARBALL_DIR=twisted.svn
DEBSOURCE=twisted-8.0.1-r23437
else
    echo "unknown case"
    exit 1
fi

# get a file to work with
# ==============================================================
wget $SOURCE_URL; if [[ $? -ne 0 ]]; then exit $?; fi

# case 1: build from pre-existing source tarball
# ==============================================================
py2dsc $SOURCE_TARBALL; if [[ $? -ne 0 ]]; then exit $?; fi

cd deb_dist/$DEBSOURCE; if [[ $? -ne 0 ]]; then exit $?; fi
dpkg-buildpackage -rfakeroot -uc -us; if [[ $? -ne 0 ]]; then exit $?; fi
cd ../..; if [[ $? -ne 0 ]]; then exit $?; fi
echo "contents of .deb from $SOURCE_TARBALL in case 1:"
dpkg --contents deb_dist/*.deb; if [[ $? -ne 0 ]]; then exit $?; fi

#cleanup case 1
rm -rf deb_dist; if [[ $? -ne 0 ]]; then exit $?; fi

# case 2: build from pre-existing source tarball
# ==============================================================
tar xzf $SOURCE_TARBALL; if [[ $? -ne 0 ]]; then exit $?; fi
cd $SOURCE_TARBALL_DIR; if [[ $? -ne 0 ]]; then exit $?; fi
python setup.py --command-packages=stdeb.command sdist_dsc; if [[ $? -ne 0 ]]; then exit $?; fi
cd deb_dist/$DEBSOURCE; if [[ $? -ne 0 ]]; then exit $?; fi
dpkg-buildpackage -rfakeroot -uc -us; if [[ $? -ne 0 ]]; then exit $?; fi
cd ..; if [[ $? -ne 0 ]]; then exit $?; fi
echo "contents of .deb from $SOURCE_TARBALL in case 2:"
dpkg --contents *.deb; if [[ $? -ne 0 ]]; then exit $?; fi
cd ../..

#cleanup case 2
# ==============================================================
rm -rf $SOURCE_TARBALL_DIR; if [[ $? -ne 0 ]]; then exit $?; fi

#cleanup original tarball
rm -rf $SOURCE_TARBALL; if [[ $? -ne 0 ]]; then exit $?; fi

done

echo "All tests passed."
