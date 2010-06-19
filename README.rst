stdeb - Python to Debian source package conversion utility
==========================================================

`stdeb <http://github.com/astraw/stdeb>`_ produces Debian source
packages from Python packages via a new distutils command,
``sdist_dsc``. Automatic defaults are provided for the Debian package,
but many aspects of the resulting package can be customized (see the
customizing section, below). An additional command, ``bdist_deb``,
creates a Debian binary package, a .deb file. The ``debianize``
command builds a ``debian/`` directory directly alongside your
setup.py.

Two convenience utilities are also provided. ``pypi-install`` will
query the `Python Package Index (PyPI) <http://pypi.python.org/>`_ for
a package, download it, create a .deb from it, and then install the
.deb. ``py2dsc`` will convert a distutils-built source tarball into a
Debian source package.

.. contents::

News
----

master branch
`````````````

This branch is recommended for all users. It requires Debhelper 7, and
thus *requires Ubuntu 8.10 (or newer) or Debian Lenny (or newer)*.

 * 2009-06-18: **Version 0.6.0**. See the `download page
   <http://pypi.python.org/pypi/stdeb/0.6.0>`__. Highlights for this
   release (you may also wish to consult the full `changelog
   <http://github.com/astraw/stdeb/blob/release-0.6.0/CHANGELOG.txt>`__):

   - A new ``debianize`` command to build a ``debian/`` directory
     alongside your setup.py file.

   - Bugfixes.

 * 2009-01-09: **Version 0.5.1**. Bugfix release. See the `download
   page <http://pypi.python.org/pypi/stdeb/0.5.1>`__, the `changelog
   <http://github.com/astraw/stdeb/blob/release-0.5.1/CHANGELOG.txt>`__
   and `release notes
   <http://github.com/astraw/stdeb/blob/release-0.5.1/RELEASE_NOTES.txt>`__.

 * 2009-12-30: **Version 0.5.0**. See the `download page
   <http://pypi.python.org/pypi/stdeb/0.5.0>`__. Highlights for this
   release (you may also wish to consult the full `changelog
   <http://github.com/astraw/stdeb/blob/release-0.5.0/CHANGELOG.txt>`__):

   - A new ``pypi-install`` script will automatically download, make a
     .deb, and install packages from the `Python Package Index (PyPI)`_.

   - Removal of the setuptools dependency.

   - New option (`--guess-conflicts-provides-replaces`) to query
     original Debian packages for Conflicts/Provides/Replaces
     information.

   - As a result of these changes and to fix a couple bugs/warts, some
     minor backwards incompatible changes and deprecations were
     made. Please check the `release notes
     <http://github.com/astraw/stdeb/blob/release-0.5.0/RELEASE_NOTES.txt>`__.

 * 2009-12-28: Version 0.4.3 Released. See the `download page`__. See the
   `changelog`__ and `release notes`__.
 * 2009-11-02: Version 0.4.2 Released. See the `download page`__. See the
   `changelog`__ and `release notes`__.
 * 2009-10-04: Version 0.4.1 Released. See the `download page`__. See the
   `changelog`__ and `release notes`__.
 * 2009-09-27: Version 0.4 Released. See the `download page`__. This
   version switches to debhelper 7. See the `Changelog for 0.4`__.

__ http://pypi.python.org/pypi/stdeb/0.4.3
__ http://github.com/astraw/stdeb/blob/release-0.4.3/CHANGELOG.txt
__ http://github.com/astraw/stdeb/blob/release-0.4.3/RELEASE_NOTES.txt
__ http://pypi.python.org/pypi/stdeb/0.4.2
__ http://github.com/astraw/stdeb/blob/release-0.4.2/CHANGELOG.txt
__ http://github.com/astraw/stdeb/blob/release-0.4.2/RELEASE_NOTES.txt
__ http://pypi.python.org/pypi/stdeb/0.4.1
__ http://github.com/astraw/stdeb/blob/release-0.4.1/CHANGELOG.txt
__ http://github.com/astraw/stdeb/blob/release-0.4.1/RELEASE_NOTES.txt
__ http://pypi.python.org/pypi/stdeb/0.4
__ http://github.com/astraw/stdeb/blob/release-0.4/CHANGELOG.txt

old-stable branch (0.3 and earlier)
```````````````````````````````````

This branch is recommended if you are operating on older Debian/Ubuntu
distributions. It is compatible with Ubuntu Hardy.

 * 2009-10-04: Version 0.3.2 Released. See the `download page`__. See the `Changelog for 0.3.2`__
 * 2009-09-27: Version 0.3.1 Released. See the `download page`__. See the `Changelog for 0.3.1`__
 * 2009-03-21: Version 0.3 Released. See the `download page`__. See the `Changelog for 0.3`__
 * 2009-02-17: Version 0.2.3 Released. See the `download page`__. See the `Changelog for 0.2.3`__
 * 2009-01-29: Version 0.2.2 Released. See the `download page`__. See the `Changelog for 0.2.2`__
 * 2008-04-26: Version 0.2.1 Released. See the `download page`__. See the `Changelog for 0.2.1`__
 * 2008-04-26: Version 0.2 Released. See the `download page`__. See the `Changelog for 0.2`__
 * 2007-04-02: Version 0.2.a1 Released. See the `old download page`_.
 * 2006-06-19: Version 0.1 Released. See the `old download page`_.

__ http://pypi.python.org/pypi/stdeb/0.3.2
__ http://github.com/astraw/stdeb/blob/release-0.3.2/CHANGELOG.txt
__ http://pypi.python.org/pypi/stdeb/0.3.1
__ http://github.com/astraw/stdeb/blob/release-0.3.1/CHANGELOG.txt
__ http://pypi.python.org/pypi/stdeb/0.3
__ http://github.com/astraw/stdeb/blob/release-0.3/CHANGELOG.txt
__ http://pypi.python.org/pypi/stdeb/0.2.3
__ http://github.com/astraw/stdeb/blob/release-0.2.3/CHANGELOG.txt
__ http://pypi.python.org/pypi/stdeb/0.2.2
__ http://github.com/astraw/stdeb/blob/release-0.2.2/CHANGELOG.txt
__ http://pypi.python.org/pypi/stdeb/0.2.1
__ http://github.com/astraw/stdeb/blob/release-0.2.1/CHANGELOG.txt
__ http://pypi.python.org/pypi/stdeb/0.2
__ http://github.com/astraw/stdeb/blob/release-0.2/CHANGELOG.txt

The commands
------------

pypi-install, command-line command
``````````````````````````````````

``pypi-install`` takes a package name, queries PyPI for it, downloads
it, builds a Debian source package and then .deb from it, and this
installs it::

  pypi-install [options] mypackage

py2dsc, command-line command
````````````````````````````

``py2dsc`` takes a .tar.gz source package and build a Debian source
package from it::

  py2dsc [options] mypackage-0.1.tar.gz # uses pre-built Python source package


sdist_dsc, distutils command
````````````````````````````

All methods eventually result in a call to the ``sdist_dsc`` distutils
command. You may prefer to do so directly::

  python setup.py --command-packages=stdeb.command sdist_dsc

A Debian source package is produced from unmodified
Python packages. The following files are produced in a newly created
subdirectory ``deb_dist``:

 * ``packagename_versionname.orig.tar.gz``
 * ``packagename_versionname-debianversion.dsc``
 * ``packagename_versionname-debianversion.diff.gz``

These can then be compiled into binary packages using the standard
Debian machinery (e.g. dpkg-buildpackage).

bdist_deb, distutils command
````````````````````````````

Also, a ``bdist_deb`` distutils command is installed. This calls the
sdist_dsc command and then runs dpkg-buildpackage on the result::

  python setup.py --command-packages=stdeb.command bdist_deb


debianize, distutils command
````````````````````````````

The ``debianize`` distutils command builds the same ``debian/``
directory as used in the previous command, but the output is placed
directly in the project's root folder (alongside setup.py). This is
useful for customizing the Debian package directly (rather than using
the various stdeb options to tune the generated package).

::

  python setup.py --command-packages=stdeb.command debianize

A note about telling distutils to use the stdeb distutils commands
``````````````````````````````````````````````````````````````````

Distutils command packages can also be specified in distutils
configuration files (rather than using the ``--command-packages``
command line argument to ``setup.py``), as specified in the `distutils
documentation
<http://docs.python.org/distutils/extending.html>`_. Specifically, you
could include this in your ``~/.pydistutils.cfg`` file::

  [global]
  command-packages: stdeb.command

Examples
--------

These all assume you have stdeb installed in your system Python
path. stdeb also works from a non-system Python path (e.g. a
`virtualenv <http://pypi.python.org/pypi/virtualenv>`_).

Quickstart 1: Install something from PyPI now, I don't care about anything else
```````````````````````````````````````````````````````````````````````````````

Do this from the command line::

  pypi-install mypackage

**Warning: Despite doing its best, there is absolutely no way stdeb
can guarantee all the Debian package dependencies will be properly
fulfilled without manual intervention. Using pypi-install bypasses
your ability to customize stdeb's behavior. Read the rest of this
document to understand how to make better packages.**

Quickstart 2: Just tell me the fastest way to make a .deb
`````````````````````````````````````````````````````````

(First, install stdeb as you normally install Python packages.)

Do this from the directory with your `setup.py` file::

  python setup.py --command-packages=stdeb.command bdist_deb

This will make a Debian source package (.dsc, .orig.tar.gz and
.diff.gz files) and then compile it to a Debian binary package (.deb)
for your current system. The result will be in ``deb_dist``.

**Warning: installing the .deb file on other versions of Ubuntu or
Debian than the one on which it was compiled will result in undefined
behavior. If you have extension modules, they will probably
break. Even in the absence of extension modules, bad stuff will likely
happen.**

For this reason, it is much better to build the Debian source package
and then compile that (e.g. using `Ubuntu's PPA`__) for each target
version of Debian or Ubuntu.

__ https://help.launchpad.net/Packaging/PPA

Quickstart 3: I read the warning, so show me how to make a source package, then compile it
``````````````````````````````````````````````````````````````````````````````````````````

This generates a source package::

  wget http://pypi.python.org/packages/source/R/Reindent/Reindent-0.1.0.tar.gz
  py2dsc Reindent-0.1.0.tar.gz

This turns it into a .deb using the standard Debian tools. (Do *this*
on the same source package for each target distribution)::

  cd deb_dist/reindent-0.1.0/
  dpkg-buildpackage -rfakeroot -uc -us

This installs it::

  cd ..
  sudo dpkg -i python-reindent_0.1.0-1_all.deb

Another example, with more explanation
``````````````````````````````````````

This example is more useful if you don't have a Python source package
(.tar.gz file generated by ``python setup.py sdist``). For the sake of
illustration, we do download such a tarball, but immediately unpack it
(alternatively, use a version control system to grab the unpacked
source of a package)::

  wget http://pypi.python.org/packages/source/R/Reindent/Reindent-0.1.0.tar.gz
  tar xzf Reindent-0.1.0.tar.gz
  cd Reindent-0.1.0

The following will generate a directory ``deb_dist`` containing the
files ``reindent_0.1.0-1.dsc``, ``reindent_0.1.0.orig.tar.gz`` and
``reindent_0.1.0-1.diff.gz``, which, together, are a debian source
package::

  python setup.py --command-packages=stdeb.command sdist_dsc

The source generated in the above way is also extracted (using
``dpkg-source -x``) and placed in the ``deb_dist`` subdirectory. To
continue the example above::

  cd deb_dist/reindent-0.1.0
  dpkg-buildpackage -rfakeroot -uc -us

Finally, the generated package can be installed::

  cd ..
  sudo dpkg -i python-reindent_0.1.0-1_all.deb

For yet another example of use, with still more explanation, see
`allmydata-tahoe ticket 251`_.

.. _allmydata-tahoe ticket 251: http://allmydata.org/trac/tahoe/ticket/251

Download
--------

Files are available at the `download page`_ (for ancient releases, see
the `old download page`_).

.. _download page: http://pypi.python.org/pypi/stdeb
.. _old download page: http://stdeb.python-hosting.com/wiki/Download

The git repository is available at
http://github.com/astraw/stdeb

Install (or, using stdeb to create an stdeb installer)
------------------------------------------------------

For a bit of fun, here's how to install stdeb using stdeb. Note that
stdeb is also in Debian and Ubuntu, so this recipe is only necessary
to install a more recent stdeb.

::

  STDEB_VERSION="0.6.0"

  # Download stdeb
  wget http://pypi.python.org/packages/source/s/stdeb/stdeb-$STDEB_VERSION.tar.gz

  # Extract it
  tar xzf stdeb-$STDEB_VERSION.tar.gz

  # Enter extracted source package
  cd stdeb-$STDEB_VERSION

  # Build .deb (making use of stdeb package directory in sys.path).
  python setup.py --command-packages=stdeb.command bdist_deb

  # Install it
  sudo dpkg -i deb_dist/python-stdeb_$STDEB_VERSION-1_all.deb

Background
----------

For the average Python package, its source distribution
(python_package.tar.gz created with ``python setup.py sdist``)
contains nearly everything necessary to make a Debian source
package. This near-equivalence encouraged me to write this distutils
extension, which executes the setup.py file to extract relevant
information. `setuptools
<http://peak.telecommunity.com/DevCenter/setuptools>`_ may optionally
be used.

I wrote this initially to Debianize several Python packages of my own,
but I have the feeling it could be generally useful. It appears
similar, at least in theory, to easydeb_, `Logilab's Devtools`_,
bdist_dpkg_ and bdist_deb_.

.. _easydeb: http://easy-deb.sourceforge.net/
.. _Logilab's DevTools: http://www.logilab.org/projects/devtools
.. _bdist_dpkg: http://svn.python.org/view/sandbox/trunk/Lib/bdist_dpkg.py
.. _bdist_deb: http://bugs.python.org/issue1054967

Features
--------

* Create a package for all Python versions supported by
  python-support. (Limiting this range is possible with the
  ``XS-Python-Version:`` config option.)

* Automatic conversion of Python package names into valid Debian
  package names.

* Attempt to automatically convert version numbers such that ordering
  is maintained. See also the config option
  ``Forced-Upstream-Version``.

* Fine grained control of version numbers. (``Debian-Version``,
  ``Forced-Upstream-Version``, ``Upstream-Version-Prefix``,
  ``Upstream-Version-Suffix`` config options.)

* Install .desktop files. (``MIME-Desktop-Files`` config option.)

* Install .mime and .sharedmimeinfo files. (``MIME-File`` and
  ``Shared-MIME-File`` config options.)

* Install copyright files. (``Copyright-File`` config option.)

* Apply patches to upstream sources. (``Stdeb-Patch-File`` config
  option.)

* Pass environment variables to setup.py script. (``Setup-Env-Vars``
  config option.)

Customizing the produced Debian source package (config options)
---------------------------------------------------------------

stdeb will attempt to provide reasonable defaults, but these are only
guesses.

There are two ways to customize the Debian source package produced by
stdeb. First, you may provide options to the distutils
commands. Second, you may provide an ``stdeb.cfg`` file.

stdeb distutils command options
```````````````````````````````

The sdist_dsc command takes command-line options to the distutils
command. For example::

  python setup.py --command-packages=stdeb.command sdist_dsc --debian-version 0MyName1

This creates a Debian package with the Debian version set to
"0MyName1".

These options can also be set via distutils configuration
files. (These are the ``setup.cfg`` file alongside ``setup.py`` and
the ~/.pydistutils.cfg file.) In that case, put the arguments in the
``[sdist_dsc]`` section. For example, a project's ``~/.setup.cfg``
file might have this::

  [sdist_dsc]
  force-buildsystem: False

To pass these commands to sdist_dsc when calling bdist_deb, do this::

  python setup.py sdist_dsc --debian-version 0MyName1 bdist_deb

====================================== =========================================
        Command line option                      Effect
====================================== =========================================
  --dist-dir (-d)                      directory to put final built
                                       distributions in (default='deb_dist')
  --patch-already-applied (-a)         patch was already applied (used when
                                       py2dsc calls sdist_dsc)
  --extra-cfg-file (-x)                additional .cfg file (in addition to
                                       .egg-info/stdeb.cfg if present)
  --patch-file (-p)                    patch file applied before setup.py
                                       called (incompatible with file
                                       specified in .cfg)
  --patch-level (-l)                   patch file applied before setup.py
                                       called (incompatible with file
                                       specified in .cfg)
  --patch-posix (-q)                   apply the patch with --posix mode
  --remove-expanded-source-dir (-r)    remove the expanded source directory
                                       requires.txt in the egg-info directory
  --pycentral-backwards-compatibility  If True (currently the default), enable
                                       migration from old stdeb that used
                                       pycentral
  --workaround-548392                  If True (currently the default), limit
                                       binary package to single Python
                                       version, working around Debian bug
                                       548392 of debhelper
  --force-buildsystem                  If True (the default), set 'DH_OPTIONS=
                                       --buildsystem=python_distutils'
  --no-backwards-compatibility         If True, set --pycentral-backwards-
                                       compatibility=False and --workaround-
                                       548392=False. (Default=False).
  --guess-conflicts-provides-replaces  If True, attempt to guess
                                       Conflicts/Provides/Replaces in
                                       debian/control based on apt-cache
                                       output. (Default=False).
  --use-premade-distfile (-P)          use .zip or .tar.gz file already made
                                       by sdist command

====================================== =========================================


You may also pass any arguments described below for the stdeb.cfg file
via distutils options. Passing the arguments this way (either on the
command line, or in the ``[sdist_dsc]`` section of a distutils .cfg
file) will take precedence. The option name should be given in lower
case.

stdeb.cfg configuration file
````````````````````````````

You may write config files of the format understood by `ConfigParser
<http://docs.python.org/lib/module-ConfigParser.html>`_. When building
each package, stdeb looks for the existance of a ``stdeb.cfg`` in the
directory with ``setup.py``. You may specify an additional config file
with the command-line option --extra-cfg-file. The section should
should either be [DEFAULT] or [package_name], which package_name is
specified as the name argument to the setup() command. An example
stdeb.cfg file is::

  [DEFAULT]
  Depends: python-numpy
  XS-Python-Version: >= 2.6

All available options:

====================================== =========================================
  Config file option                     Effect
====================================== =========================================
  Source                               debian/control Source: (Default:
                                       <source-debianized-setup-name>)
  Package                              debian/control Package: (Default:
                                       python-<debianized-setup-name>)
  Suite                                suite (e.g. stable, lucid) in changelog
                                       (Default: unstable)
  Maintainer                           debian/control Maintainer: (Default:
                                       <setup-maintainer-or-author>)
  Debian-Version                       debian version (Default: 1)
  Section                              debian/control Section: (Default:
                                       python)
  Epoch                                version epoch
  Forced-Upstream-Version              forced upstream version
  Upstream-Version-Prefix              upstream version prefix
  Upstream-Version-Suffix              upstream version suffix
  Uploaders                            uploaders
  Copyright-File                       copyright file
  Build-Depends                        debian/control Build-Depends:
  Build-Conflicts                      debian/control Build-Conflicts:
  Stdeb-Patch-File                     file containing patches for stdeb to
                                       apply
  Stdeb-Patch-Level                    patch level provided to patch command
  Depends                              debian/control Depends:
  Suggests                             debian/control Suggests:
  Recommends                           debian/control Recommends:
  XS-Python-Version                    debian/control XS-Python-Version:
  Dpkg-Shlibdeps-Params                parameters passed to dpkg-shlibdeps
  Conflicts                            debian/control Conflicts:
  Provides                             debian/control Provides:
  Replaces                             debian/control Replaces:
  MIME-Desktop-Files                   MIME desktop files
  MIME-File                            MIME file
  Shared-MIME-File                     shared MIME file
  Setup-Env-Vars                       environment variables passed to
                                       setup.py
  Udev-Rules                           file with rules to install to udev
====================================== =========================================

The option names in stdeb.cfg files are not case sensitive.

Prerequisites
-------------

 * Python 2.5 or higher
 * Standard Debian utilities such as ``date``, ``dpkg-source`` and
   Debhelper 7 (use stdeb 0.3.x if you need to support older
   distributions without dh7)
 * If your setup.py uses the setuptools features ``setup_requires`` or
   ``install_requires``, you must run ``apt-file update`` prior to
   running any stdeb command.

TODO
----

* Make output meet `Debian Python Policy`_ specifications or the `new
  python policy`_. This will include several things, among which are:

  - the ability to make custom changelogs
  - the ability to include project-supplied documentation as a -doc package
  - include license information in debian/copyright
  - the ability to include project-supplied examples, tests, and data
    as a separate package
  - much more not listed

* Create (better) documentation

* Log output using standard distutils mechanisms

* Refactor the source code to have a simpler, more sane design

.. _debian python policy: http://www.debian.org/doc/packaging-manuals/python-policy/
.. _new python policy: http://wiki.debian.org/DebianPython/NewPolicy

Call for volunteers
-------------------

I don't have a lot of time for this. This project stands a very real
chance of being only a shadow of its potential self unless people step
up and contribute. There are numerous ways in which people could
help. In particular, I'd be interested in finding a co-maintainer or
maintainer if the project generates any interest. Secondarily, I would
appreciate advice from Debian developers or Ubuntu MOTUs about the
arcane details of Python packaging.

Mailing list
------------

Please address all questions to the distutils-SIG_

.. _distutils-SIG: http://mail.python.org/mailman/listinfo/distutils-sig

License
-------

MIT-style license. Copyright (c) 2006-2009 stdeb authors.

See the LICENSE.txt file provided with the source distribution for
full details.

Authors
-------

* Andrew Straw <strawman@astraw.com>
* Pedro Algarvio, aka, s0undt3ch <ufs@ufsoft.org>
* Gerry Reno (initial bdist_deb implementation)

Additional Credits
------------------

* Zooko O'Whielacronx for the autofind-depends patch.
* Brett (last name unknown) for the --ignore-install-requires patch.
* Ximin Luo for a bug fix.
* Alexander D. Sedov for bug fixes and suggestions.
* Michele Mattioni for bug fix.
* Alexander V. Nikolaev for the debhelper buildsystem specification.
* Roland Sommer for the description field bugfix.
* Barry Warsaw for suggesting the debianize command.
* GitHub_ for hosting services.
* WebFaction_ (aka `python-hosting`_) for previous hosting services.

.. _GitHub: http://github.com/
.. _WebFaction: http://webfaction.com/
.. _python-hosting: http://python-hosting.com/
