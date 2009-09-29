import os
import stdeb.util as util
from stdeb.command.sdist_dsc import sdist_dsc

__all__ = ['bdist_deb']

class bdist_deb(sdist_dsc):
    description = 'distutils command to create debian binary package'

    # extend the run method
    def run(self):
        # call parent run() method to generate .dsc source pkg
	sdist_dsc.run(self)

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

