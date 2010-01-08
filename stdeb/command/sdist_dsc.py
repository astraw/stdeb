import sys, os, shutil

from distutils.core import Command
from distutils.errors import DistutilsModuleError

from stdeb import log
from stdeb.util import expand_sdist_file, recursive_hardlink
from stdeb.util import DebianInfo, build_dsc, stdeb_cmdline_opts, \
     stdeb_cmd_bool_opts, stdeb_cfg_options
from stdeb.util import repack_tarball_with_debianized_dirname

__all__ = ['sdist_dsc']


class sdist_dsc(Command):
    description = "distutils command to create a debian source distribution"

    user_options = stdeb_cmdline_opts + [
        ('use-premade-distfile=','P',
         'use .zip or .tar.gz file already made by sdist command'),
        ] + stdeb_cfg_options

    boolean_options = stdeb_cmd_bool_opts

    def initialize_options (self):
        self.patch_already_applied = 0
        self.remove_expanded_source_dir = 0
        self.patch_posix = 0
        self.dist_dir = None
        self.extra_cfg_file = None
        self.patch_file = None
        self.patch_level = None
        self.use_premade_distfile = None
        self.ignore_install_requires = None
        self.debian_version = None
        self.pycentral_backwards_compatibility = None
        self.workaround_548392 = None
        self.force_buildsystem = None
        self.no_backwards_compatibility = None
        self.guess_conflicts_provides_replaces = None

        # deprecated options
        self.default_distribution = None
        self.default_maintainer = None

        # make distutils happy by filling in default values
        for longopt, shortopt, description in stdeb_cfg_options:
            assert longopt.endswith('=')
            name = longopt[:-1]
            name = name.replace('-','_')
            setattr( self, name, None )

    def finalize_options(self):
        def str_to_bool(mystr):
            if mystr.lower() == 'false':
                return False
            elif mystr.lower() == 'true':
                return True
            else:
                raise ValueError('bool string "%s" is not "true" or "false"'%mystr)
        if self.dist_dir is None:
            self.dist_dir = 'deb_dist'
        if self.patch_level is not None:
            self.patch_level = int(self.patch_level)

        if self.pycentral_backwards_compatibility is not None:
            print '='*50,repr(self.pycentral_backwards_compatibility)
            self.pycentral_backwards_compatibility = str_to_bool(
                self.pycentral_backwards_compatibility)
            print '='*50,repr(self.pycentral_backwards_compatibility)
        if self.workaround_548392 is not None:
            self.workaround_548392 = str_to_bool(self.workaround_548392)

        if self.force_buildsystem is not None:
            self.force_buildsystem = str_to_bool(self.force_buildsystem)

        if self.no_backwards_compatibility:
            if self.pycentral_backwards_compatibility==True:
                raise ValueError('inconsistent backwards compatibility '
                                 'command line options')
            if self.workaround_548392==True:
                raise ValueError('inconsistent backwards compatibility '
                                 'command line options')
            self.workaround_548392=False
            self.pycentral_backwards_compatibility=False

        if self.workaround_548392 is None:
            self.workaround_548392=True
            # emit future change warnging?

        if self.force_buildsystem is None:
            self.force_buildsystem = True

        if self.pycentral_backwards_compatibility is None:
            self.pycentral_backwards_compatibility=True
             # emit future change warnging?

        if self.guess_conflicts_provides_replaces is None:
            # the default
            self.guess_conflicts_provides_replaces = False
        else:
            self.guess_conflicts_provides_replaces = str_to_bool(
                self.guess_conflicts_provides_replaces)

    def run(self):
        ###############################################
        # 1. setup initial variables
        #    A. create config defaults
        module_name = self.distribution.get_name()

        if 1:
            # set default maintainer
            if (self.distribution.get_maintainer() != 'UNKNOWN' and
                self.distribution.get_maintainer_email() != 'UNKNOWN'):
                guess_maintainer = "%s <%s>"%(
                    self.distribution.get_maintainer(),
                    self.distribution.get_maintainer_email())
            elif (self.distribution.get_author() != 'UNKNOWN' and
                  self.distribution.get_author_email() != 'UNKNOWN'):
                guess_maintainer = "%s <%s>"%(
                    self.distribution.get_author(),
                    self.distribution.get_author_email())
            else:
                guess_maintainer = "unknown <unknown@unknown>"
        if self.default_maintainer is not None:
            log.warn('Deprecation warning: you are using the '
                     '--default-maintainer option. '
                     'Switch to the --maintainer option.')
            guess_maintainer = self.default_maintainer

        #    B. find config files (if any)
        cfg_files = []
        if self.extra_cfg_file is not None:
            cfg_files.append(self.extra_cfg_file)

        use_setuptools = True
        try:
            ei_cmd = self.distribution.get_command_obj('egg_info')
        except DistutilsModuleError, err:
            use_setuptools = False

        install_requires = ()
        have_script_entry_points = None

        config_fname = 'stdeb.cfg'
        # Distutils fails if not run from setup.py dir, so this is OK.
        if os.path.exists(config_fname):
            cfg_files.append(config_fname)

        if use_setuptools:
            self.run_command('egg_info')
            egg_info_dirname = ei_cmd.egg_info

            # Pickup old location of stdeb.cfg
            config_fname = os.path.join(egg_info_dirname,'stdeb.cfg')
            if os.path.exists(config_fname):
                log.warn('Deprecation warning: stdeb detected old location of '
                         'stdeb.cfg in %s. This file will be used, but you '
                         'should move it alongside setup.py.' %egg_info_dirname)
                cfg_files.append(config_fname)

            egg_module_name = egg_info_dirname[:egg_info_dirname.index('.egg-info')]
            egg_module_name = egg_module_name.split(os.sep)[-1]

            try:
                if not self.ignore_install_requires:
                    install_requires = open(os.path.join(egg_info_dirname,'requires.txt'),'rU').read()
            except EnvironmentError:
                pass

            if 1:
                # determine whether script specifies setuptools entry_points
                ep_fname = os.path.join(egg_info_dirname,'entry_points.txt')
                if os.path.exists(ep_fname):
                    entry_points = open(ep_fname,'rU').readlines()
                else:
                    entry_points = ''
                entry_points = [ep.strip() for ep in entry_points]

                if ('[console_scripts]' in entry_points or
                    '[gui_scripts]' in entry_points):
                    have_script_entry_points = True
        else:
            # We don't have setuptools, so guess egg_info_dirname to
            # find old stdeb.cfg.

            entries = os.listdir(os.curdir)
            for entry in entries:
                if not (entry.endswith('.egg-info') and os.path.isdir(entry)):
                    continue
                # Pickup old location of stdeb.cfg
                config_fname = os.path.join(entry,'stdeb.cfg')
                if os.path.exists(config_fname):
                    log.warn('Deprecation warning: stdeb detected '
                             'stdeb.cfg in %s. This file will be used, but you '
                             'should move it alongside setup.py.' % entry)
                    cfg_files.append(config_fname)

        if have_script_entry_points is None:
            have_script_entry_points = self.distribution.has_scripts()

        debinfo = DebianInfo(
            cfg_files=cfg_files,
            module_name = module_name,
            default_distribution=self.default_distribution,
            guess_maintainer=guess_maintainer,
            upstream_version = self.distribution.get_version(),
            has_ext_modules = self.distribution.has_ext_modules(),
            description = self.distribution.get_description()[:60],
            long_description = self.distribution.get_long_description(),
            patch_file = self.patch_file,
            patch_level = self.patch_level,
            install_requires = install_requires,
            debian_version = self.debian_version,
            workaround_548392=self.workaround_548392,
            force_buildsystem=self.force_buildsystem,
            have_script_entry_points = have_script_entry_points,
            pycentral_backwards_compatibility=self.pycentral_backwards_compatibility,
            setup_requires = (), # XXX How do we get the setup_requires?
            use_setuptools = use_setuptools,
            guess_conflicts_provides_replaces=self.guess_conflicts_provides_replaces,
            sdist_dsc_command = self,
        )
        if debinfo.patch_file != '' and self.patch_already_applied:
            raise RuntimeError('A patch was already applied, but another '
                               'patch is requested.')

        ###############################################
        # 2. Build source tree and rename it to be in self.dist_dir

        #    A. create source archive in new directory
        repackaged_dirname = debinfo.source+'-'+debinfo.upstream_version
        fullpath_repackaged_dirname = os.path.join(self.dist_dir,
                                                   repackaged_dirname)

        source_tarball = None
        cleanup_dirs = []

        exclude_dirs = ['.svn', '.git']
        # copy source tree
        if os.path.exists(fullpath_repackaged_dirname):
            shutil.rmtree(fullpath_repackaged_dirname)
        os.makedirs(fullpath_repackaged_dirname)
        orig_dir = os.path.abspath(os.curdir)
        for src in os.listdir(orig_dir):
            if src not in exclude_dirs+[self.dist_dir,'build','dist']:
                dst = os.path.join(fullpath_repackaged_dirname,src)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, symlinks=True)
                else:
                    shutil.copy2(src, dst )
        # remove .pyc files which dpkg-source cannot package
        for root, dirs, files in os.walk(fullpath_repackaged_dirname):
            for name in files:
                if name.endswith('.pyc'):
                    fullpath = os.path.join(root,name)
                    os.unlink(fullpath)
            for name in dirs:
                if name in exclude_dirs:
                    fullpath = os.path.join(root,name)
                    shutil.rmtree(fullpath)

        if self.use_premade_distfile is not None:
        # ensure premade sdist can actually be used
            self.use_premade_distfile = os.path.abspath(self.use_premade_distfile)
            expand_dir = os.path.join(self.dist_dir,'tmp_sdist_dsc')
            cleanup_dirs.append(expand_dir)
            if os.path.exists(expand_dir):
                shutil.rmtree(expand_dir)
            if not os.path.exists(self.dist_dir):
                os.mkdir(self.dist_dir)
            os.mkdir(expand_dir)

            expand_sdist_file(self.use_premade_distfile,cwd=expand_dir)

            is_tgz=False
            if self.use_premade_distfile.lower().endswith('.tar.gz'):
                is_tgz=True

            # now the sdist package is expanded in expand_dir
            expanded_root_files = os.listdir(expand_dir)
            assert len(expanded_root_files)==1
            distname_in_premade_distfile = expanded_root_files[0]
            debianized_dirname = repackaged_dirname
            original_dirname = os.path.split(distname_in_premade_distfile)[-1]
            do_repack=False
            if is_tgz:
                source_tarball = self.use_premade_distfile
            else:
                log.warn('WARNING: .orig.tar.gz will be generated from sdist '
                         'archive ("%s") because it is not a .tar.gz file',
                         self.use_premade_distfile)
                do_repack=True

            if do_repack:
                tmp_dir = os.path.join(self.dist_dir, 'tmp_repacking_dir' )
                os.makedirs( tmp_dir )
                cleanup_dirs.append(tmp_dir)
                source_tarball = os.path.join(tmp_dir,'repacked_sdist.tar.gz')
                repack_tarball_with_debianized_dirname(self.use_premade_distfile,
                                                       source_tarball,
                                                       debianized_dirname,
                                                       original_dirname )
            if source_tarball is not None:
                # Because we deleted all .pyc files above, if the
                # original source dist has them, we will have
                # (wrongly) deleted them. So, quit loudly rather
                # than fail silently.
                for root, dirs, files in os.walk(fullpath_repackaged_dirname):
                    for name in files:
                        if name.endswith('.pyc'):
                            raise RuntimeError('original source dist cannot '
                                               'contain .pyc files')
        else:
            if 0:
                # haven't figured out why
                raise NotImplementedError("the code path is broken right now")


        ###############################################
        # 3. Find all directories

        for pkgdir in self.distribution.packages or []:
            debinfo.dirlist += ' ' + pkgdir.replace('.', '/')

        ###############################################
        # 4. Build source tree and rename it to be in self.dist_dir

        build_dsc(debinfo,
                  self.dist_dir,
                  repackaged_dirname,
                  orig_sdist=source_tarball,
                  patch_posix = self.patch_posix,
                  remove_expanded_source_dir=self.remove_expanded_source_dir,
                  )

        for rmdir in cleanup_dirs:
            shutil.rmtree(rmdir)
