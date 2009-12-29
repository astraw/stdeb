stdeb - Python to Debian source package conversion utility
==========================================================

stdeb_ produces Debian source packages from Python packages via a new
distutils command, ``sdist_dsc``. Automatic defaults are provided for
the Debian package, but many aspects of the resulting package can be
customized via a configuration file. An additional command,
``bdist_deb``, creates a Debian binary package, a .deb file.

.. _stdeb: http://github.com/astraw/stdeb

.. contents::

News
----

master branch
`````````````

 * 2009-12-28: Version 0.4.3 Released. See the `download page`__. See the
   `changelog`__ and `release notes`__.
 * 2009-11-02: Version 0.4.2 Released. See the `download page`__. See the
   `changelog`__ and `release notes`__.
 * 2009-10-04: Version 0.4.1 Released. See the `download page`__. See the
   `changelog`__ and `release notes`__.
 * 2009-09-27: Version 0.4 Released. See the `download page`__. This
   version switches to debhelper 7, and thus *requires Ubuntu Intrepid
   or Debian Lenny* at a minimum (unless you use backports). See the
   `Changelog for 0.4`__

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

Invocation
----------

All methods eventually result in a call to the ``sdist_dsc`` distutils
command. You may prefer to do so directly::

  python -c "import stdeb; execfile('setup.py')" sdist_dsc

Alternatively, two scripts are provided::

  stdeb_run_setup [options] # calls "python setup.py sdist_dsc [options]"

  py2dsc [options] mypackage-0.1.tar.gz # uses pre-built Python source package

In all cases, a Debian source package is produced from unmodified
Python packages. The following files are produced in a newly created
subdirectory ``deb_dist``:

 * ``packagename_versionname.orig.tar.gz``
 * ``packagename_versionname-debianversion.dsc``
 * ``packagename_versionname-debianversion.diff.gz``

These can then be compiled into binary packages using the standard
Debian machinery (e.g. dpkg-buildpackage).

Also, a ``bdist_deb`` distutils command is installed. This calls the
sdist_dsc command and then runs dpkg-buildpackage on the result::

  python -c "import stdeb; execfile('setup.py')" bdist_deb

Examples
--------

Quickstart 1: Just tell me the fastest way to make a .deb
`````````````````````````````````````````````````````````

Do this from the directory with your `setup.py` file::

  python -c "import stdeb; execfile('setup.py')" bdist_deb

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

Quickstart 2: I read the warning, so show me how to make a source package, then compile it
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

  python setup.py sdist_dsc

(For packages that don't use setuptools, you need to get the stdeb
monkeypatch for the sdist_dsc distutils command. So, do this: ``python
-c "import stdeb; execfile('setup.py')" sdist_dsc``, or use the
command ``stdeb_run_setup``, which does just this.)

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

Background
----------

For the average Python package, its source distribution
(python_package.tar.gz created with ``python setup.py sdist``)
contains nearly everything necessary to make a Debian source
package. This near-equivalence encouraged me to write this distutils
extension, which executes the setup.py file to extract relevant
information. This process is made significantly easier through the use
of setuptools_.

.. _setuptools: http://peak.telecommunity.com/DevCenter/setuptools

setuptools is used because of some nice features.  For example,
setuptools makes the job of "Debianizing" python console and gui
scripts much easier.

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
  is maintained. (The setuptools version sorting is different than the
  Debian version sorting.) See also the config option
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

To customize the Debian source package produced, you may write config
files of the format understood by ConfigParser_. When building each
package, stdeb looks for the existance of a ``stdeb.cfg`` file in the
``.egg-info`` directory. You may specify an additional config file
with the command-line option --extra-cfg-file. Other command line
options may also be provided.

.. _ConfigParser: http://docs.python.org/lib/module-ConfigParser.html

======================== ================================================
  Config file option       Effect
======================== ================================================
Debian-Version           Set Debian version
Maintainer               Set Debian maintainer
Forced-Upstream-Version  Force upstream version number
Upstream-Version-Prefix  Force upstream version prefix (e.g. epoch)
Upstream-Version-Suffix  Force upstream version suffix
Build-Depends            Add entry to debian/control
Depends                  Add entry to debian/control
Package                  Name of (binary) package
Source                   Nome of source package
XS-Python-Version        Add to debian/control (limits Python versions)
MIME-Desktop-Files       Filename of .desktop file(s) to install
MIME-File                Filename of .mime file(s) to install
Shared-MIME-File         Filename of .sharedmimeinfo file(s) to install
Copyright-File           Filename of copyright file to install
Stdeb-Patch-File         Patches to apply
Setup-Env-Vars           Environment variables to set on call to setup.py
======================== ================================================

====================================== =========================================
        Command line option                      Effect
====================================== =========================================
  --dist-dir (-d)                      directory to put final built
                                       distributions in (default='deb_dist')
  --patch-already-applied (-a)         patch was already applied (used when
                                       py2dsc calls sdist_dsc)
  --default-distribution (-z)          distribution name to use if not
                                       specified in .cfg (default='unstable')
  --default-maintainer (-m)            maintainer name and email to use if not
                                       specified in .cfg (default from
                                       setup.py)
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
  --ignore-install-requires (-i)       ignore the requirements from
                                       requires.txt in the egg-info directory
  --debian-version                     debian version
  --pycentral-backwards-compatibility  If True (currently the default), enable
                                       migration from old stdeb that used
                                       pycentral
  --workaround-548392                  If True (currently the default), limit
                                       binary package to single Python
                                       version, working around Debian bug
                                       548392 of debhelper
  --no-backwards-compatibility         If True, set --pycentral-backwards-
                                       compatibility=False and --workaround-
                                       548392=False. (Default=False).
  --use-premade-distfile (-P)          use .zip or .tar.gz file already made
                                       by sdist command

====================================== =========================================


Prerequisites
-------------

 * Python_ 2.5 or higher (older python OK if you use subprocess.py
   with backports from Python 2.5)
 * Standard Debian utilities such as ``date``, ``dpkg-source`` and
   Debhelper 7 (use stdeb 0.3.x if you need to support older
   distributions without dh7)

.. _Python: http://www.python.org/

Using stdeb on stdeb
--------------------

There is a chicken-and-egg problem when trying to make a Debian
package of stdeb with stdeb. Here's a recipe to avoid it::

 # in the stdeb distribution directory (with setup.py)
 python setup.py sdist
 python setup.py build
 PYTHONPATH="build/lib" python stdeb/py2dsc.py dist/stdeb-VERSION.tar.gz

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

* Zooko O'Whielacronx for the autofind-depends patch
* Brett (last name unknown) for the --ignore-install-requires patch
* Ximin Luo for a bug fix
* Alexander D. Sedov for bug fixes and suggestions
* Michele Mattioni for bug fix
* Alexander V. Nikolaev for the debhelper buildsystem specification
* GitHub_ for hosting services.
* WebFaction_ (aka `python-hosting`_) for previous hosting services.

.. _GitHub: http://github.com/
.. _WebFaction: http://webfaction.com/
.. _python-hosting: http://python-hosting.com/
