#!/bin/bash

SOURCE_URL=http://pypi.python.org/packages/source/R/Reindent/Reindent-0.1.0.tar.gz
SOURCE_TARBALL=Reindent-0.1.0.tar.gz
SOURCE=Reindent-0.1.0
DEBSOURCE=reindent-0.1.0
DEBPACKAGE=python-reindent_0.1.0-1_all.deb

wget $SOURCE_URL; if [[ $? -ne 0 ]]; then exit $?; fi

# case 1: build from pre-existing source tarball
py2dsc $SOURCE_TARBALL; if [[ $? -ne 0 ]]; then exit $?; fi

cd deb_dist/$DEBSOURCE; if [[ $? -ne 0 ]]; then exit $?; fi
dpkg-buildpackage -rfakeroot -uc -us; if [[ $? -ne 0 ]]; then exit $?; fi
cd ../..; if [[ $? -ne 0 ]]; then exit $?; fi
echo "contents of .deb in case 1:"
dpkg --contents deb_dist/$DEBPACKAGE; if [[ $? -ne 0 ]]; then exit $?; fi

#cleanup case 1
rm -rf deb_dist; if [[ $? -ne 0 ]]; then exit $?; fi

# case 2: build from pre-existing source tarball
tar xzf $SOURCE_TARBALL; if [[ $? -ne 0 ]]; then exit $?; fi
cd $SOURCE; if [[ $? -ne 0 ]]; then exit $?; fi
stdeb_run_setup; if [[ $? -ne 0 ]]; then exit $?; fi
cd deb_dist/$DEBSOURCE; if [[ $? -ne 0 ]]; then exit $?; fi
dpkg-buildpackage -rfakeroot -uc -us; if [[ $? -ne 0 ]]; then exit $?; fi
cd ..; if [[ $? -ne 0 ]]; then exit $?; fi
echo "contents of .deb in case 2:"
dpkg --contents $DEBPACKAGE; if [[ $? -ne 0 ]]; then exit $?; fi
cd ../..

#cleanup case 2
rm -rf $SOURCE; if [[ $? -ne 0 ]]; then exit $?; fi

#cleanup original tarball
rm -rf $SOURCE_TARBALL; if [[ $? -ne 0 ]]; then exit $?; fi

echo "All tests passed."
