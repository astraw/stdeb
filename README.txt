stdeb - Python to Debian source package conversion utility
==========================================================

stdeb_ is a distutils command to Debian source packages from Python
packages. It attempts to provide automatic defaults, but many aspects
of the resulting package can be customized via a simple config file.

.. _stdeb: http://stdeb.python-hosting.com/

Instant summary
---------------

::

  python -c "import stdeb; execfile('setup.py')" stdeb

This command creates a Debian source package from unmodified Python
packages. (``packagename_versionname.orig.tar.gz`` is created along
with the ``packagename-versionname`` directory with all Debian-needed
changes. These consist solely of a ``packagename-versionname/debian``
subdirectory with auto-generated ``changelog``, ``compat``,
``control``, and ``rules`` files.)

Download
--------

Files are available at the `download page`_.

.. _download page: http://stdeb.python-hosting.com/wiki/Download

Background
----------

For the average Python package, its source distribution
(python_package.tar.gz created with ``python setup.py sdist``)
contains nearly everything necessary to make a Debian source
package. This near-equivalence encouraged me to write this little
utility, which is a distutils extension which allows one to type
``python setup.py stdeb`` to create a Debian source layout. This
process is made significantly easier through the use of setuptools_.

.. _setuptools: http://peak.telecommunity.com/DevCenter/setuptools

Although it's not implemented, using setuptools might provide us with
tools to make the job of "Debianizing" python console and gui scripts,
for example, much easier.

I wrote this initially to Debianize several Python packages of my own,
but I have the feeling it could be generally useful. It appears
similar in theory to easydeb_, which I haven't (successfully) used. (I
tried for 5 minutes, but the fatal flaw for me is that easydeb is GPL
licensed.) `Logilab's Devtools`_ also appears to have a similar
concept, but I couldn't even get beyond the French documentation.

.. _easydeb: http://easy-deb.sourceforge.net/
.. _Logilab's DevTools: http://www.logilab.org/projects/devtools

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

Here's an example .cfg file for my build of numpy_::

 [DEFAULT]
 Debian-Version: 0ads1
 
 [numpy]
 Source: python-numpy
 Build-Depends: python-dev, refblas3-dev, lapack3-dev, python2.3-dev, python2.4-dev, python-setuptools, python2.3-setuptools, python2.4-setuptools
 Build-Conflicts: atlas3-base, atlas3-base-dev

.. _numpy: http://scipy.org/NumPy

Interaction with numpy distutils
--------------------------------

numpy_ has it's own derivative of distutils that breaks the trick
given in the Instant Summary. In order to get this working again,
here's a simple trick::

  python -c "import stdeb, sys;f='setup.py';sys.argv[0]=f;execfile(f)" stdeb

(This works by setting ``sys.argv[0]`` to what numpy expects.)

TODO
----

 * Make output meet `Debian Python Policy`_ specifications, or the
   `new python policy`_. This will include several things,
   including the ability to make custom changelogs, to make use of
   project-supplied documentation (including license information),
   and to make separate -doc binary packages.
 * Support python-central_ and/or python-support.
 * Create (better) documentation
 * Log output using standard distutils mechanisms

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

License
-------

MIT-style license. Copyright (c) 2006 stdeb authors.

Authors
-------

Andrew Straw, California Institute of Technology <strawman@astraw.com>