import os
import shutil
import tempfile

from stdeb import log
from stdeb.util import expand_sdist_file
from stdeb.util import build_dsc, stdeb_cmdline_opts, \
     stdeb_cmd_bool_opts, stdeb_cfg_options
from stdeb.util import repack_tarball_with_debianized_dirname
from stdeb.command.common import common_debian_package_command

__all__ = ['sdist_dsc']


class sdist_dsc(common_debian_package_command):
    description = "distutils command to create a debian source distribution"

    user_options = stdeb_cmdline_opts + [
        ('use-premade-distfile=', 'P',
         'use .zip or .tar.gz file already made by sdist command'),
        ] + stdeb_cfg_options

    boolean_options = stdeb_cmd_bool_opts

    def initialize_options(self):
        self.use_premade_distfile = None
        common_debian_package_command.initialize_options(self)

    def run(self):
        debinfo = self.get_debinfo()
        if debinfo.patch_file != '' and self.patch_already_applied:
            raise RuntimeError('A patch was already applied, but another '
                               'patch is requested.')

        repackaged_dirname = debinfo.source+'-'+debinfo.upstream_version
        fullpath_repackaged_dirname = os.path.join(self.dist_dir,
                                                   repackaged_dirname)

        cleanup_dirs = []
        if self.use_premade_distfile is None:
            # generate original tarball
            sdist_cmd = self.distribution.get_command_obj('sdist')
            self.run_command('sdist')

            source_tarball = None
            for archive_file in sdist_cmd.get_archive_files():
                if archive_file.endswith('.tar.gz'):
                    source_tarball = archive_file

            if source_tarball is None:
                raise RuntimeError('sdist did not produce .tar.gz file')

            # make copy of source tarball in deb_dist/
            local_source_tarball = os.path.split(source_tarball)[-1]
            shutil.copy2(source_tarball, local_source_tarball)
            source_tarball = local_source_tarball
            self.use_premade_distfile = source_tarball
        else:
            source_tarball = self.use_premade_distfile

        # Copy source tree assuming that package-0.1.tar.gz contains
        # single top-level path 'package-0.1'. The contents of this
        # directory are then used.

        if os.path.exists(fullpath_repackaged_dirname):
            shutil.rmtree(fullpath_repackaged_dirname)

        tmpdir = tempfile.mkdtemp()
        expand_sdist_file(os.path.abspath(source_tarball),
                          cwd=tmpdir)
        expanded_base_files = os.listdir(tmpdir)
        assert len(expanded_base_files) == 1
        actual_package_dirname = expanded_base_files[0]
        shutil.move(os.path.join(tmpdir, actual_package_dirname),
                    fullpath_repackaged_dirname)

        # ensure premade sdist can actually be used
        self.use_premade_distfile = os.path.abspath(self.use_premade_distfile)
        expand_dir = os.path.join(self.dist_dir, 'tmp_sdist_dsc')
        cleanup_dirs.append(expand_dir)
        if os.path.exists(expand_dir):
            shutil.rmtree(expand_dir)
        if not os.path.exists(self.dist_dir):
            os.mkdir(self.dist_dir)
        os.mkdir(expand_dir)

        expand_sdist_file(self.use_premade_distfile, cwd=expand_dir)

        is_tgz = False
        if self.use_premade_distfile.lower().endswith('.tar.gz'):
            is_tgz = True

        # now the sdist package is expanded in expand_dir
        expanded_root_files = os.listdir(expand_dir)
        assert len(expanded_root_files) == 1
        distname_in_premade_distfile = expanded_root_files[0]
        debianized_dirname = repackaged_dirname
        original_dirname = os.path.split(distname_in_premade_distfile)[-1]
        do_repack = False
        if is_tgz:
            source_tarball = self.use_premade_distfile
        else:
            log.warn('WARNING: .orig.tar.gz will be generated from sdist '
                     'archive ("%s") because it is not a .tar.gz file',
                     self.use_premade_distfile)
            do_repack = True

        if do_repack:
            tmp_dir = os.path.join(self.dist_dir, 'tmp_repacking_dir')
            os.makedirs(tmp_dir)
            cleanup_dirs.append(tmp_dir)
            source_tarball = os.path.join(tmp_dir, 'repacked_sdist.tar.gz')
            repack_tarball_with_debianized_dirname(self.use_premade_distfile,
                                                   source_tarball,
                                                   debianized_dirname,
                                                   original_dirname)
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
                  patch_posix=self.patch_posix,
                  remove_expanded_source_dir=self.remove_expanded_source_dir,
                  sign_dsc=self.sign_results,
                  ignore_source_changes=self.ignore_source_changes,
                  )

        for rmdir in cleanup_dirs:
            shutil.rmtree(rmdir)
