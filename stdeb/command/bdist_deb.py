import os
import stdeb.util as util
from stdeb.command.sdist_dsc import sdist_dsc

from distutils.core import Command

__all__ = ['bdist_deb']

class bdist_deb(Command):
    description = 'distutils command to create debian binary package'

    user_options = []
    boolean_options = []

    def initialize_options (self):
        pass

    def finalize_options (self):
        pass

    def run(self):
        # generate .dsc source pkg
        self.run_command('sdist_dsc')

        # execute system command and read output (execute and read output of find cmd)
        dsc_tree = 'deb_dist'
        target_dir = None
        for entry in os.listdir(dsc_tree):
            fulldir = os.path.join(dsc_tree,entry)
            if os.path.isdir(fulldir):
                if target_dir is not None:
                    raise ValueError('more than one directory in deb_dist. '
                                     'Unsure which is source directory')
                else:
                    target_dir = fulldir
        if target_dir is None:
            raise ValueError('could not find debian source directory')

        # define system command to execute (gen .deb binary pkg)
        syscmd = ['dpkg-buildpackage','-rfakeroot','-uc','-b']

        util.process_command(syscmd,cwd=target_dir)

