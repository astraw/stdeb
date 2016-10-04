import os, glob
import stdeb.util as util

from distutils.core import Command

__all__ = ['install_deb']

class install_deb(Command):
    description = 'distutils command to install debian binary package'

    user_options = []
    boolean_options = []

    def initialize_options (self):
        pass

    def finalize_options (self):
        pass

    def run(self):
        # generate .deb file
        self.run_command('bdist_deb')

        # get relevant options passed to sdist_dsc
        sdist_dsc = self.get_finalized_command('sdist_dsc')

        # execute system command and read output (execute and read output of find cmd)
        target_dirs = []
        target_debs = glob.glob( os.path.join( sdist_dsc.dist_dir, '*.deb' ) )

        if len(target_debs)==0:
            raise ValueError('could not find .deb file')

        for target_deb in target_debs:
            # define system command to execute (install .deb binary pkg)
            syscmd = ['dpkg','--install',target_deb]
            util.process_command(syscmd)
