import setuptools, sys, os, shutil
from setuptools import Command
import pkg_resources

from stdeb.util import expand_tarball, expand_zip
from stdeb.util import DebianInfo, build_dsc, stdeb_cmdline_opts, stdeb_cmd_bool_opts

__all__ = ['sdist_dsc']
    
class sdist_dsc(Command):
    decription = "distutils command to create a debian source distribution"

    user_options = stdeb_cmdline_opts + [
        ('use-premade-distfile=','p',
         'use .zip or .tar.gz file already made by sdist command'),
        ]
    
    boolean_options = stdeb_cmd_bool_opts
    
    def initialize_options (self):
        self.use_pycentral = 0
        self.dist_dir = None
        self.default_distribution = None
        self.default_maintainer = None
        self.extra_cfg_files = None
        self.use_premade_distfile = None
        
    def finalize_options(self):
        if self.dist_dir is None:
            self.dist_dir = 'deb_dist'
        if self.default_distribution is None:
            self.default_distribution = 'experimental'

    def run(self):
        ###############################################
        # 1. setup initial variables

        #    A. create config defaults
        module_name = self.distribution.get_name()
        if self.default_maintainer is None:
            if (self.distribution.get_maintainer() != 'UNKNOWN' and
                self.distribution.get_maintainer_email() != 'UNKNOWN'):
                self.default_maintainer = "%s <%s>"%(
                    self.distribution.get_maintainer(),
                    self.distribution.get_maintainer_email())
            elif (self.distribution.get_author() != 'UNKNOWN' and
                  self.distribution.get_author_email() != 'UNKNOWN'):
                self.default_maintainer = "%s <%s>"%(
                    self.distribution.get_author(),
                    self.distribution.get_author_email())
            else:
                defaults['Maintainer'] = "unknown <unknown@unknown>"
        
        #    B. find config files (if any)
        #         find .egg-info directory
        egg_name = pkg_resources.safe_name(module_name)
        egg_info_dirname = pkg_resources.to_filename(egg_name)+'.egg-info'
        config_fname = os.path.join(egg_info_dirname,'stdeb.cfg')
        
        cfg_files = []
        if os.path.exists(config_fname):
            cfg_files.append(config_fname)
        if self.extra_cfg_files is not None:
            self.extra_cfg_files = self.extra_cfg_files.split()
            cfg_files.extend(self.extra_cfg_files)

        debinfo = DebianInfo(cfg_files=cfg_files,
                             module_name = module_name,
                             default_distribution=self.default_distribution,
                             default_maintainer=self.default_maintainer,
                             upstream_version = self.distribution.get_version(),
                             use_pycentral = self.use_pycentral,
                             has_ext_modules = self.distribution.has_ext_modules(),
                             description = self.distribution.get_description(),
                             long_description = self.distribution.get_long_description(),
                             )
        ###############################################
        # 2. Build source tree and rename it to be in self.dist_dir



        #    B. create source archive in new directory
        if 1:
            repackaged_dirname = debinfo.source+'-'+debinfo.upstream_version
            fullpath_repackaged_dirname = os.path.join(self.dist_dir,repackaged_dirname)
        if self.use_premade_distfile is not None:
            expand_dir = os.path.join(self.dist_dir,'tmp_sdist_dsc')
            if os.path.exists(expand_dir):
                shutil.rmtree(expand_dir)
            if not os.path.exists(self.dist_dir):
                os.mkdir(self.dist_dir)
            os.mkdir(expand_dir)

            if self.use_premade_distfile.lower().endswith('.zip'):
                expand_zip(self.use_premade_distfile,cwd=expand_dir)
            elif self.use_premade_distfile.lower().endswith('.tar.gz'):
                expand_tarball(self.use_premade_distfile,cwd=expand_dir)
            else:
                raise RuntimeError('could not guess format of original sdist file')

            # now the sdist package is expanded in expand_dir
            expanded_root_files = os.listdir(expand_dir)
            assert len(expanded_root_files)==1
            base_dir = os.path.join(expand_dir,expanded_root_files[0])
            os.renames(base_dir, fullpath_repackaged_dirname)
            del base_dir
        else:
            if os.path.exists(fullpath_repackaged_dirname):
                shutil.rmtree(fullpath_repackaged_dirname)     
            # generate a new sdist
            if 1:
                self.distribution.get_command_obj('sdist').keep_temp=True
            if 0:
                self.distribution.get_command_obj('sdist').dist_dir=self.dist_dir
            self.run_command('sdist')

            # move original source tree 
            if 1:
                base_dir = self.distribution.get_fullname()
                os.renames(base_dir, fullpath_repackaged_dirname)
                del base_dir

            
        ###############################################
        # 2. Build source tree and rename it to be in self.dist_dir
         
        build_dsc(debinfo,self.dist_dir,repackaged_dirname)
