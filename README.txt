stdeb - Python to Debian source package conversion utility
==========================================================

stdeb_ ("setuptools debian") produces Debian source packages from
Python packages via a new distutils command, ``sdist_dsc``. Automatic
defaults are provided for the Debian package, but many aspects of the
resulting package can be customized via a configuration file.

.. _stdeb: http://stdeb.python-hosting.com/

News
----

 * 2007-04-02: Version 0.2.a1 Released. See the `download page`_. This version uses python-central_ by default. See the `Changelog for 0.2.a1`_
 * 2006-06-19: Version 0.1 Released. See the `download page`_.

.. _Changelog for 0.2.a1: http://stdeb.python-hosting.com/file/tags/release-0.2.a1/CHANGELOG.txt

Invocation
----------

All methods eventually result in a call to the ``sdist_dsc`` distutils
command. You may prefer to do so directly::

  python -c "import stdeb; execfile('setup.py')" sdist_dsc

Alternatively, two scripts are provided::

  stdeb_run_setup [options] # calls "python setup.py sdist_dsc [options]"

  py2dsc [options] mypackage-0.1.tar.gz # uses pre-built Python source package

In all cases, a Debian source package is produced from unmodified
Python packages. The following files are produced:

 * ``packagename_versionname.orig.tar.gz``
 * ``packagename_versionname-debianversion.dsc``
 * ``packagename_versionname-debianversion.diff.gz``

These can then be compiled into binary packages using the standard
Debian machinery (e.g. dpkg-buildpackage).

Download
--------

Files are available at the `download page`_.

.. _download page: http://stdeb.python-hosting.com/wiki/Download

The subversion repository is available at
https://svn.stdeb.python-hosting.com/trunk

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
similar, at least in theory, to easydeb_, `Logilab's Devtools`_, and
bdist_dpkg_.

.. _easydeb: http://easy-deb.sourceforge.net/
.. _Logilab's DevTools: http://www.logilab.org/projects/devtools
.. _bdist_dpkg: http://svn.python.org/view/sandbox/trunk/Lib/bdist_dpkg.py

Prerequisites
-------------

 * Python_ 2.3 or greater
 * setuptools_
 * subprocess.py_ (included with Python 2.4, backwards compatible with Python 2.3)

.. _Python: http://www.python.org/
.. _subprocess.py: http://svn.python.org/view/python/trunk/Lib/subprocess.py?rev=46651&view=log

Customizing the produced Debian source package
----------------------------------------------

stdeb will attempt to provide reasonable defaults, but these are only
guesses.

To customize the Debian source package produced, you may write config
files of the format understood by ConfigParser_. When building each
package, stdeb looks for the existance of a ``stdeb.cfg`` file in the
``.egg-info`` directory. You may specify an additional config file
with the command-line option --extra-cfg-file.

.. _ConfigParser: http://docs.python.org/lib/module-ConfigParser.html

For an example configuration file I use to build several packages,
please see http://stdeb.python-hosting.com/wiki/stdeb_all.cfg

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
  python policy`_. This will include several things, including:

  - the ability to make custom changelogs
  - the ability to patch upstream source (added in 0.2.a1 release)
  - the ability to include project-supplied documentation (including
    license information) as a -doc package
  - the ability to include project-supplied examples, tests, and data
    as a separate package
  - much more not listed

* Support python-central_ and/or python-support. (added in 0.2.a1 release)

* Create (better) documentation

* Log output using standard distutils mechanisms

* Refactor the source code to have a simpler, more sane design

.. _debian python policy: http://www.debian.org/doc/packaging-manuals/python-policy/
.. _new python policy: http://wiki.debian.org/DebianPython/NewPolicy
.. _python-central: http://python-modules.alioth.debian.org/python-central_howto.txt

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

MIT-style license. Copyright (c) 2006 stdeb authors. 

See the LICENSE.txt file provided with the source distribution for
full details.

Authors
-------

Andrew Straw <strawman@astraw.com>, California Institute of
Technology

Additional Credits
------------------

* WebFaction_ (aka `python-hosting`_) for hosting services.

.. _WebFaction: http://webfaction.com/
.. _python-hosting: http://python-hosting.com/
