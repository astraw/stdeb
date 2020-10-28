import os
import stdeb.util as util

from distutils.core import Command

__all__ = ['bdist_deb']


class bdist_deb(Command):
    description = 'distutils command to create debian binary package'

    user_options = [
        ('sign-results', None,
         'Use gpg to sign the resulting .dsc and .changes file'),
        ('ignore-source-changes', None,
         'Ignore all changes on source when building source package '
         '(add -i.* option to dpkg-source'),
        ]
    boolean_options = [
        'sign-results',
        'ignore-source-changes',
        ]

    def initialize_options(self):
        self.sign_results = False
        self.ignore_source_changes = False

    def finalize_options(self):
        self.sign_results = bool(self.sign_results)
        self.ignore_source_changes = bool(self.ignore_source_changes)

    def run(self):
        # generate .dsc source pkg
        self.run_command('sdist_dsc')

        # get relevant options passed to sdist_dsc
        sdist_dsc = self.get_finalized_command('sdist_dsc')
        dsc_tree = sdist_dsc.dist_dir

        # execute system command and read output
        # (execute and read output of find cmd)
        target_dirs = []
        for entry in os.listdir(dsc_tree):
            fulldir = os.path.join(dsc_tree, entry)
            if os.path.isdir(fulldir):
                if entry == 'tmp_py2dsc':
                    continue
                target_dirs.append(fulldir)

        if len(target_dirs) > 1:
            raise ValueError('More than one directory in deb_dist. '
                             'Unsure which is source directory. All: %r' % (
                                target_dirs,))

        if len(target_dirs) == 0:
            raise ValueError('could not find debian source directory')

        # define system command to execute (gen .deb binary pkg)
        syscmd = ['dpkg-buildpackage', '-rfakeroot', '-b']

        if not self.sign_results:
            syscmd.append('-uc')

        if self.ignore_source_changes:
            syscmd.append('-i.*')

        util.process_command(syscmd, cwd=target_dirs[0])
