import setuptools, sys, os, shutil
from setuptools import Command
import ConfigParser
import subprocess

__all__ = ['stdeb']

def parse_vals(cfg,section,option):
    "parse comma separated values in debian control file style from .cfg"
    vals = cfg.get(section,option)
    vals = vals.split(',')
    vals = [v.strip() for v in vals]
    vals = [v for v in vals if len(v)]
    return vals

def parse_val(cfg,section,option):
    "extract a single value from .cfg"
    vals = parse_vals(cfg,section,option)
    assert len(vals)==1
    return vals[0]

def debianize_name(name):
    "make name acceptable as a Debian package name"
    name = name.replace('_','')
    name = name.lower()
    return name

def make_tarball(tarball_fname,directory,cwd=None):
    "create a tarball from a directory"
    args = ['/bin/tar','czf',tarball_fname,directory]
    res = subprocess.Popen(
        args, cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        )
    returncode = res.wait()
    if returncode:
        print >> sys.stderr, 'ERROR running: %s'%(' '.join(args),)
        print >> sys.stderr, 'ERROR in',cwd
        print >> sys.stderr, res.stderr.read()
        raise RuntimeError('returncode %d'%returncode)
    
def get_date_822():
    """return output of 822-date command"""
    args = ['/usr/bin/822-date']
    res = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        )
    returncode = res.wait()
    if returncode:
        print >> sys.stderr, 'ERROR running: %s'%(' '.join(args),)
        print >> sys.stderr, res.stderr.read()
        raise RuntimeError('returncode %d'%returncode)
    result = res.stdout.read().strip()
    return result

class DebianInfo:
    """Empty class to hold values"""
    pass
    
class stdeb(Command):
    decription = "distutils command to create a debian source distribution"

    user_options = [
        ('dist-dir=', 'd',
         "directory to put final built distributions in (default='deb_dist')"),
        ('use-pycentral=', 'c', # not tested yet
         'use pycentral support for multiple Python versions (NOT TESTED)'),
        ('default-distribution=', 'z',
         "which distribution name to use if not specified in .cfg (default='experimental')"),
        ('default-maintainer=', 'm',
         'maintainer name and email to use if not specified in .cfg (default from setup.py)'),
        ('extra-cfg-file=','x',
         'use a .cfg file specified here (in addition to .egg-info/stdeb.cfg if present)'),
        ]
    
    boolean_options = [
        'use-pycentral',
    ]

    def initialize_options (self):
        self.use_pycentral = 0
        self.dist_dir = None
        self.default_distribution = None
        self.default_maintainer = None
        self.extra_cfg_file = None
        
    def finalize_options(self):
        if self.dist_dir is None:
            self.dist_dir = 'deb_dist'
        if self.default_distribution is None:
            self.default_distribution = 'experimental'

    def _get_cfg_defaults(self):
        defaults = {}

        defaults['Source']=debianize_name(self.module_name)
        defaults['Package']='python-%s'%(debianize_name(self.module_name),)
        
        defaults['Distribution']=self.default_distribution
        
        defaults['Debian-Version']='1'

        if self.default_maintainer is None:
            if (self.distribution.get_maintainer() != 'UNKNOWN' and
                self.distribution.get_maintainer_email() != 'UNKNOWN'):
                defaults['Maintainer'] = "%s <%s>"%(
                    self.distribution.get_maintainer(),
                    self.distribution.get_maintainer_email())
            elif (self.distribution.get_author() != 'UNKNOWN' and
                  self.distribution.get_author_email() != 'UNKNOWN'):
                defaults['Maintainer'] = "%s <%s>"%(
                    self.distribution.get_author(),
                    self.distribution.get_author_email())
            else:
                defaults['Maintainer'] = "unknown <unknown@unknown>"
        else:
            defaults['Maintainer'] = self.default_maintainer
            
        defaults['Build-Depends'] = ''
        defaults['Build-Conflicts'] = ''
        defaults['Depends'] = ''
        defaults['Suggests'] = ''
        defaults['Recommends'] = ''
        
        defaults['Conflicts'] = ''
        defaults['Provides'] = ''
            
        return defaults

    def run(self):
        
        ###############################################
        # 1. create intelligent defaults and read config file

        self.module_name = self.distribution.get_name()
        
        #    A. find .egg-info directory
        self.run_command('egg_info')
        ei_cmd = self.get_finalized_command('egg_info')
        #    B. get config file name
        config_fname = os.path.join(ei_cmd.egg_info,'stdeb.cfg')
        #    C. create SafeConfigParser instance with defaults
        cfg = ConfigParser.SafeConfigParser(self._get_cfg_defaults())
        #    D. read the config files (if any)
        cfg_files = []
        if self.extra_cfg_file is not None:
            cfg_files.append(self.extra_cfg_file)
        if os.path.exists(config_fname):
            cfg_files.append(config_fname)
            
        cfg.read(cfg_files)

        ###############################################
        # 2. Prepare Debian variables

        debinfo = DebianInfo()
        debinfo.module_name = self.module_name
        debinfo.source = parse_val(cfg,self.module_name,'Source')
        debinfo.package = parse_val(cfg,self.module_name,'Package')
        debinfo.upstream_version = self.distribution.get_version()
        debinfo.packaging_version = parse_val(cfg,self.module_name,'Debian-Version')
        debinfo.full_version = '%s-%s'%(debinfo.upstream_version,
                                        debinfo.packaging_version)
        debinfo.distname = parse_val(cfg,self.module_name,'Distribution')
        debinfo.maintainer = parse_val(cfg,self.module_name,'Maintainer')
        debinfo.date822 = get_date_822()
        if self.use_pycentral:
            raise NotImplementedError('') # need to call 'pycentral showversions'
        else:
            current = sys.version[:3]
            debinfo.pycentral_showversions=current

        depends = []

        if self.use_pycentral:
            depends.append('${python:Depends}')

        if self.distribution.has_ext_modules():
            debinfo.architecture = 'any'
            depends.append('${shlibs:Depends}')
        else:
            debinfo.architecture = 'all'
            
        depends.extend(parse_vals(cfg,self.module_name,'Depends') )
        debinfo.depends = ', '.join(depends)
        
        debinfo.description = self.distribution.get_description()
        long_description = self.distribution.get_long_description()
        if long_description != 'UNKNOWN':
            ld2=[]
            for line in long_description.split('\n'):
                ls = line.strip()
                if len(ls):
                    ld2.append(' '+line)
                else:
                    ld2.append(' .')
            debinfo.long_description = '\n'.join(ld2)
        else:
            debinfo.long_description = ''


        build_deps = [
            'python-all-dev',
#            'python-setuptools',
            'python2.3-setuptools',
            'python2.4-setuptools',
            ]
        
        if self.use_pycentral:
            build_deps.extend(  [
                'debhelper (>= 5.0.37.1)',
                'python-central (>= 0.4.10)',
                ] )
        else:
            build_deps.extend(  [
                'debhelper (>=5)',
                ])


        build_deps.extend( parse_vals(cfg,self.module_name,'Build-Depends') )
        debinfo.build_depends = ', '.join(build_deps)

        debinfo.suggests = ', '.join( parse_vals(cfg,self.module_name,'Suggests') )
        debinfo.recommends = ', '.join( parse_vals(cfg,self.module_name,'Recommends') )

        debinfo.source_stanza_extras = ''
        
        build_conflicts = parse_vals(cfg,self.module_name,'Build-Conflicts')
        if len(build_conflicts):
            debinfo.source_stanza_extras += ('Build-Conflicts: '+
                                              ', '.join( build_conflicts )+'\n')

        if self.use_pycentral:
            debinfo.source_stanza_extras += 'XS-Python-Version: all\n'
            debinfo.package_stanza_extras = """XB-Python-Version: ${python:Versions}
Provides: ${python:Provides}
"""
        else:
            debinfo.package_stanza_extras = ''
            
        conflicts = parse_vals(cfg,self.module_name,'Conflicts')
        if len(conflicts):
            debinfo.package_stanza_extras += ('Conflicts: '+
                                              ', '.join( conflicts )+'\n')

        provides = parse_vals(cfg,self.module_name,'Provides')
        if len(provides):
            debinfo.package_stanza_extras += ('Provides: ' +
                                              ', '.join( provides  )+'\n')

        ###############################################
        # 3. Build source tree and rename it to be in self.dist_dir
        
        #    A. Find new dirname and delete any pre-existing contents
        new_dirname = debinfo.source+'-'+debinfo.upstream_version
        fullpath_new_dirname = os.path.join(self.dist_dir,new_dirname)
        if os.path.exists(fullpath_new_dirname):
            shutil.rmtree(fullpath_new_dirname)
        #    B. create source archive (in temporary directory)
        self.distribution.get_command_obj('sdist').keep_temp=True
        self.run_command('sdist')
        #    C. move original source tree into new directory
        base_dir = self.distribution.get_fullname()
        os.renames(base_dir, fullpath_new_dirname) # XXX should hard-link
        del base_dir # no longer useful

        ###############################################
        # 4. make original source tarball
        make_tarball('%s.orig.tar.gz'%new_dirname.replace('-','_'),
                     new_dirname,
                     cwd=self.dist_dir)
        
        ###############################################
        # 5. create debian/ directory and contents
        
        debian_dir = os.path.join(fullpath_new_dirname,'debian')
        os.mkdir(debian_dir)
        
        #    A. debian/changelog

        fd = open( os.path.join(debian_dir,'changelog'), mode='w')
        fd.write('%(source)s (%(full_version)s) %(distname)s; urgency=low\n'%debinfo.__dict__)
        fd.write('\n')
        fd.write('  * source package automatically created by stdeb\n')
        fd.write('\n')
        fd.write(' -- %(maintainer)s  %(date822)s\n'%debinfo.__dict__)
        fd.close()
        
        #    B. debian/control
        control = """Source: %(source)s
Maintainer: %(maintainer)s
Section: python
Priority: optional
Build-Depends: %(build_depends)s
Standards-Version: 3.7.2
%(source_stanza_extras)s
Package: %(package)s
Architecture: %(architecture)s
Depends: %(depends)s
Recommends: %(recommends)s
Suggests: %(suggests)s
%(package_stanza_extras)sDescription: %(description)s
%(long_description)s
"""%debinfo.__dict__
        fd = open( os.path.join(debian_dir,'control'), mode='w')
        fd.write(control)
        fd.close()
        
        #    C. debian/rules
        if debinfo.architecture == 'all':
            debinfo.rules_binary="""binary-arch:
        
binary-indep: build install
        dh_testdir -i
        dh_testroot -i
#        dh_installchangelogs -i changelog
        dh_installdocs -i
        dh_installexamples  -i
#        dh_pycentral -i
        dh_strip -i
        dh_compress -i -X.py
        dh_fixperms -i
        dh_installdeb -i
        dh_gencontrol -i
        dh_md5sums -i
        dh_builddeb -i

binary: binary-indep binary-arch
"""
        else:
            debinfo.rules_binary="""binary-indep:

binary-arch: build install
        dh_testdir -a
        dh_testroot -a
#        dh_installchangelogs -a changelog
        dh_installdocs -a
        dh_installexamples  -a
#        dh_pycentral -a
        dh_strip -a
        dh_compress -a -X.py
        dh_fixperms -a
        dh_installdeb -a
        dh_shlibdeps -a
        dh_gencontrol -a
        dh_md5sums -a
        dh_builddeb -a

binary: binary-indep binary-arch
"""

        rules = """#!/usr/bin/make -f

# automatically generated by stdeb

export DH_VERBOSE=1

PACKAGE_NAME=%(package)s
MODULE_NAME=%(module_name)s

DEB_UPSTREAM_VERSION=%(upstream_version)s
PYVERS=%(pycentral_showversions)s

build: build-stamp
build-stamp: $(PYVERS:%%=build-python%%)
        touch $@
build-python%%:
        python$* -c "import setuptools; execfile('setup.py')" build
        touch $@
clean:
        dh_testdir
        dh_testroot
        rm -f *-stamp
        rm -rf dist build
        -find -name '*.py[co]' | xargs rm -f
#        find . -name *.pyc -exec rm {} \;
        dh_clean

install: build install-prereq $(PYVERS:%%=install-python%%)
install-prereq:
        dh_testdir
        dh_testroot
        dh_clean -k

install-python%%:
        python$* -c "import setuptools; execfile('setup.py')" install \
                --no-compile --single-version-externally-managed \
                --root $(CURDIR)/debian/${PACKAGE_NAME}         # install only one Egg dir (without python's version number)
        mv debian/${PACKAGE_NAME}/usr/lib/python$*/site-packages/${MODULE_NAME}-${DEB_UPSTREAM_VERSION}-py$*.egg-info \
        debian/${PACKAGE_NAME}/usr/lib/python$*/site-packages/${MODULE_NAME}.egg-info

%(rules_binary)s

.PHONY: build clean binary-indep binary-arch binary install configure
"""%debinfo.__dict__

        rules = rules.replace('        ','\t')
        rules_fname = os.path.join(debian_dir,'rules')
        fd = open( rules_fname, mode='w')
        fd.write(rules)
        fd.close()
        os.chmod(rules_fname,0755)

        #    C. debian/compat
        fd = open( os.path.join(debian_dir,'compat'), mode='w')
        fd.write('4\n')
        fd.close()
