import os
import sys

from stdeb import log
from distutils.core import Command
from distutils.errors import DistutilsModuleError

from stdeb.util import DebianInfo, DH_DEFAULT_VERS, stdeb_cfg_options


class common_debian_package_command(Command):
    def initialize_options(self):
        self.patch_already_applied = 0
        self.remove_expanded_source_dir = 0
        self.patch_posix = 0
        self.dist_dir = None
        self.extra_cfg_file = None
        self.patch_file = None
        self.patch_level = None
        self.ignore_install_requires = None
        self.debian_version = None
        self.no_backwards_compatibility = None
        self.guess_conflicts_provides_replaces = None
        if sys.version_info[0] == 2:
            self.with_python2 = 'True'
            self.with_python3 = 'False'
        else:
            assert sys.version_info[0] == 3
            self.with_python2 = 'False'
            self.with_python3 = 'True'
        self.no_python2_scripts = 'False'
        self.no_python3_scripts = 'False'
        self.force_x_python3_version = False
        self.allow_virtualenv_install_location = False
        self.with_dh_virtualenv = False
        self.with_dh_systemd = False
        self.sign_results = False
        self.ignore_source_changes = False
        self.compat = DH_DEFAULT_VERS

        # deprecated options
        self.default_distribution = None
        self.default_maintainer = None

        # make distutils happy by filling in default values
        for longopt, shortopt, description in stdeb_cfg_options:
            assert longopt.endswith('=')
            name = longopt[:-1]
            name = name.replace('-', '_')
            setattr(self, name, None)

    def finalize_options(self):
        def str_to_bool(mystr):
            if mystr.lower() == 'false':
                return False
            elif mystr.lower() == 'true':
                return True
            else:
                raise ValueError(
                    'bool string "%s" is not "true" or "false"' % mystr)
        if self.dist_dir is None:
            self.dist_dir = 'deb_dist'
        if self.patch_level is not None:
            self.patch_level = int(self.patch_level)

        if self.guess_conflicts_provides_replaces is None:
            # the default
            self.guess_conflicts_provides_replaces = False
        else:
            self.guess_conflicts_provides_replaces = str_to_bool(
                self.guess_conflicts_provides_replaces)

        self.with_python2 = str_to_bool(self.with_python2)
        self.with_python3 = str_to_bool(self.with_python3)
        self.no_python2_scripts = str_to_bool(self.no_python2_scripts)
        self.no_python3_scripts = str_to_bool(self.no_python3_scripts)
        if self.maintainer is not None:
            # Get the locale specifying the encoding in sys.argv
            import codecs
            import locale
            fs_enc = codecs.lookup(locale.getpreferredencoding()).name
            if hasattr(os, 'fsencode'):  # this exists only in Python 3
                m = os.fsencode(self.maintainer)  # convert to orig raw bytes

                # Now, convert these raw bytes into unicode.
                m = m.decode(fs_enc)  # Set your locale if you get errors here

                self.maintainer = m
            else:
                # Python 2
                if hasattr(self.maintainer, 'decode'):
                    self.maintainer = self.maintainer.decode(fs_enc)

    def get_debinfo(self):
        ###############################################
        # 1. setup initial variables
        #    A. create config defaults
        module_name = self.distribution.get_name()

        if 1:
            # set default maintainer
            if os.environ.get('DEBEMAIL'):
                guess_maintainer = "%s <%s>" % (
                    os.environ.get('DEBFULLNAME', os.environ['DEBEMAIL']),
                    os.environ['DEBEMAIL'])
            elif (
                self.distribution.get_maintainer() != 'UNKNOWN' and
                self.distribution.get_maintainer_email() != 'UNKNOWN'
            ):
                guess_maintainer = "%s <%s>" % (
                    self.distribution.get_maintainer(),
                    self.distribution.get_maintainer_email())
            elif (self.distribution.get_author() != 'UNKNOWN' and
                  self.distribution.get_author_email() != 'UNKNOWN'):
                guess_maintainer = "%s <%s>" % (
                    self.distribution.get_author(),
                    self.distribution.get_author_email())
            else:
                guess_maintainer = "unknown <unknown@unknown>"
        if self.default_maintainer is not None:
            log.warn('Deprecation warning: you are using the '
                     '--default-maintainer option. '
                     'Switch to the --maintainer option.')
            guess_maintainer = self.default_maintainer
        if hasattr(guess_maintainer, 'decode'):
            # python 2 : convert (back to) unicode
            guess_maintainer = guess_maintainer.decode('utf-8')

        #    B. find config files (if any)
        cfg_files = []
        if self.extra_cfg_file is not None:
            cfg_files.append(self.extra_cfg_file)

        use_setuptools = True
        try:
            ei_cmd = self.distribution.get_command_obj('egg_info')
        except DistutilsModuleError:
            use_setuptools = False

        config_fname = 'stdeb.cfg'
        # Distutils fails if not run from setup.py dir, so this is OK.
        if os.path.exists(config_fname):
            cfg_files.append(config_fname)

        if use_setuptools:
            self.run_command('egg_info')
            egg_info_dirname = ei_cmd.egg_info

            # Pickup old location of stdeb.cfg
            config_fname = os.path.join(egg_info_dirname, 'stdeb.cfg')
            if os.path.exists(config_fname):
                log.warn('Deprecation warning: stdeb detected old location of '
                         'stdeb.cfg in %s. This file will be used, but you '
                         'should move it alongside setup.py.' %
                         egg_info_dirname)
                cfg_files.append(config_fname)

            egg_module_name = egg_info_dirname[
                :egg_info_dirname.index('.egg-info')]
            egg_module_name = egg_module_name.split(os.sep)[-1]
        else:
            # We don't have setuptools, so guess egg_info_dirname to
            # find old stdeb.cfg.

            entries = os.listdir(os.curdir)
            for entry in entries:
                if not (entry.endswith('.egg-info') and os.path.isdir(entry)):
                    continue
                # Pickup old location of stdeb.cfg
                config_fname = os.path.join(entry, 'stdeb.cfg')
                if os.path.exists(config_fname):
                    log.warn('Deprecation warning: stdeb detected '
                             'stdeb.cfg in %s. This file will be used, but '
                             'you should move it alongside setup.py.' % entry)
                    cfg_files.append(config_fname)

        upstream_version = self.distribution.get_version()
        bad_chars = ':_'
        for bad_char in bad_chars:
            if bad_char in upstream_version:
                raise ValueError("Illegal character (%r) detected in version. "
                                 "This will break the debian tools." %
                                 bad_char)

        description = self.distribution.get_description()
        if hasattr(description, 'decode'):
            # python 2 : convert (back to) unicode
            description = description.decode('utf-8')
        description = description[:60]

        long_description = self.distribution.get_long_description()
        if hasattr(long_description, 'decode'):
            # python 2 : convert (back to) unicode
            long_description = long_description.decode('utf-8')
        long_description = long_description

        debinfo = DebianInfo(
            cfg_files=cfg_files,
            module_name=module_name,
            default_distribution=self.default_distribution,
            guess_maintainer=guess_maintainer,
            upstream_version=upstream_version,
            has_ext_modules=self.distribution.has_ext_modules(),
            description=description,
            long_description=long_description,
            homepage=self.distribution.get_url(),
            patch_file=self.patch_file,
            patch_level=self.patch_level,
            debian_version=self.debian_version,
            setup_requires=(),  # XXX How do we get the setup_requires?
            use_setuptools=use_setuptools,
            guess_conflicts_provides_replaces=(
                self.guess_conflicts_provides_replaces),
            sdist_dsc_command=self,
            with_python2=self.with_python2,
            with_python3=self.with_python3,
            no_python2_scripts=self.no_python2_scripts,
            no_python3_scripts=self.no_python3_scripts,
            force_x_python3_version=self.force_x_python3_version,
            allow_virtualenv_install_location=(
                self.allow_virtualenv_install_location),
            compat=self.compat,
            with_dh_virtualenv=self.with_dh_virtualenv,
            with_dh_systemd=self.with_dh_systemd,
        )
        return debinfo
