#
# This module contains most of the code of stdeb.
#
import sys, os, shutil, sets
import ConfigParser
import subprocess

__all__ = ['DebianInfo','build_dsc','expand_tarball','expand_zip',
           'stdeb_cmdline_opts','stdeb_cmd_bool_opts','recursive_hardlink']

stdeb_cmdline_opts = [
    ('dist-dir=', 'd',
     "directory to put final built distributions in (default='deb_dist')"),
    ('use-pycentral=', 'c', # not tested yet
     'use pycentral support for multiple Python versions (NOT TESTED)'),
    ('default-distribution=', 'z',
     "which distribution name to use if not specified in .cfg (default='experimental')"),
    ('default-maintainer=', 'm',
     'maintainer name and email to use if not specified in .cfg (default from setup.py)'),
    ('extra-cfg-files=','x',
     'use .cfg files specified here (in addition to .egg-info/stdeb.cfg if present)'),
    ('remove-expanded-source-dir=','r',
     'remove the expanded source directory')
    ]

stdeb_cmd_bool_opts = [
    'use-pycentral',
    'remove-expanded-source-dir',
    ]

class NotGiven: pass

def recursive_hardlink(src,dst):
    dst = os.path.abspath(dst)
    orig_dir = os.path.abspath(os.curdir)
    os.chdir(src)
    try:
        for root,dirs,files in os.walk(os.curdir):
            for file in files:
                fullpath = os.path.normpath(os.path.join(root,file))
                dirname, fname = os.path.split(fullpath)
                dstdir = os.path.normpath(os.path.join(dst,dirname))
                if not os.path.exists(dstdir):
                    os.makedirs(dstdir)
                newpath = os.path.join(dstdir,fname)
                if os.path.exists(newpath):
                    if os.path.samefile(fullpath,newpath):
                        continue
                    else:
                        os.unlink(newpath)
                #print 'linking %s -> %s'%(fullpath,newpath)
                os.link(fullpath,newpath)
    finally:
        os.chdir(orig_dir)

def debianize_name(name):
    "make name acceptable as a Debian package name"
    name = name.replace('_','')
    name = name.lower()
    return name

def debianize_version(name):
    "make name acceptable as a Debian package name"
    name = name.replace('_','-')
    name = name.lower()
    return name

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
    
def make_tarball(tarball_fname,directory,cwd=None):
    "create a tarball from a directory"
    if tarball_fname.endswith('.gz'): opts = 'czf'
    else: opts = 'cf'
    args = ['/bin/tar',opts,tarball_fname,directory]
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
    
def expand_tarball(tarball_fname,cwd=None):
    "expand a tarball"
    if tarball_fname.endswith('.gz'): opts = 'xzf'
    else: opts = 'xf'
    args = ['/bin/tar',opts,tarball_fname]
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
    
def expand_zip(zip_fname,cwd=None):
    "expand a zip"
    args = ['/usr/bin/unzip',zip_fname]
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
    
def dpkg_source_b(arg1,arg2=None,cwd=None):
    "call dpkg-source -b arg1 [arg2]"
    args = ['/usr/bin/dpkg-source','-b',arg1]
    if arg2 is not None:
        args.append(arg2)
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

def parse_vals(cfg,section,option):
    """parse comma separated values in debian control file style from .cfg"""
    try:
        vals = cfg.get(section,option)
    except ConfigParser.NoSectionError, err:
        if section != 'DEFAULT':
            vals = cfg.get('DEFAULT',option)
        else:
            raise err
    vals = vals.split(',')
    vals = [v.strip() for v in vals]
    vals = [v for v in vals if len(v)]
    return vals

def parse_val(cfg,section,option):
    """extract a single value from .cfg"""
    vals = parse_vals(cfg,section,option)
    if len(vals)==0:
        return ''
    else:
        assert len(vals)==1
    return vals[0]

class DebianInfo:
    """encapsulate information for Debian distribution system"""
    def __init__(self,
                 cfg_files=NotGiven,
                 module_name=NotGiven,
                 default_distribution=NotGiven,
                 default_maintainer=NotGiven,
                 upstream_version=NotGiven,
                 use_pycentral=NotGiven,
                 has_ext_modules=NotGiven,
                 description=NotGiven,
                 long_description=NotGiven,
                 ):
        if cfg_files is NotGiven: raise ValueError("cfg_files must be supplied")
        if module_name is NotGiven: raise ValueError("module_name must be supplied")
        if default_distribution is NotGiven: raise ValueError("default_distribution must be supplied")
        if default_maintainer is NotGiven: raise ValueError("default_maintainer must be supplied")
        if upstream_version is NotGiven: raise ValueError("upstream_version must be supplied")
        if use_pycentral is NotGiven: raise ValueError("use_pycentral must be supplied")
        if has_ext_modules is NotGiven: raise ValueError("has_ext_modules must be supplied")
        if description is NotGiven: raise ValueError("description must be supplied")
        if long_description is NotGiven: raise ValueError("long_description must be supplied")
        
        cfg_defaults = self._make_cfg_defaults(module_name=module_name,
                                               default_distribution=default_distribution,
                                               default_maintainer=default_maintainer,
                                               )
        
        cfg = ConfigParser.SafeConfigParser(cfg_defaults)
        cfg.read(cfg_files)

        debinfo = self # convert old code...
        debinfo.module_name = module_name
        debinfo.source = parse_val(cfg,module_name,'Source')
        debinfo.package = parse_val(cfg,module_name,'Package')
        pure_upstream_version = upstream_version 
        upstream_version_prefix = parse_val(cfg,module_name,'Upstream-Version-Prefix')
        upstream_version_suffix = parse_val(cfg,module_name,'Upstream-Version-Suffix')
        debinfo.upstream_version = (upstream_version_prefix+
                                    debianize_version(pure_upstream_version)+
                                    upstream_version_suffix)
        debinfo.packaging_version = parse_val(cfg,module_name,'Debian-Version')
        debinfo.full_version = '%s-%s'%(debinfo.upstream_version,
                                        debinfo.packaging_version)
        debinfo.distname = parse_val(cfg,module_name,'Distribution')
        debinfo.maintainer = parse_val(cfg,module_name,'Maintainer')
        debinfo.date822 = get_date_822()
        if use_pycentral:
            raise NotImplementedError('') # need to call 'pycentral showversions'
        else:
            current = sys.version[:3]
            debinfo.pycentral_showversions=current

        depends = []

        depends.append('${python:Depends}')

        if has_ext_modules:
            debinfo.architecture = 'any'
            depends.append('${shlibs:Depends}')
        else:
            debinfo.architecture = 'all'
            
        debinfo.mime_file = parse_val(cfg,module_name,'MIME-File')
        
        debinfo.shared_mime_file = parse_val(cfg,module_name,'Shared-MIME-File')

        if debinfo.mime_file == '' and debinfo.shared_mime_file == '':
            debinfo.dh_installmime_line = ''
        else:
            debinfo.dh_installmime_line = '\n        dh_installmime'
            if debinfo.architecture == 'all':
                debinfo.dh_installmime_line += ' -i'
            else:
                debinfo.dh_installmime_line += ' -a'
        
        mime_desktop_files = parse_vals(cfg,module_name,'MIME-Desktop-Files')
        if len(mime_desktop_files):
            debinfo.dh_desktop_line = '\n        dh_desktop'
            if debinfo.architecture == 'all':
                debinfo.dh_desktop_line += ' -i'
            else:
                debinfo.dh_desktop_line += ' -a'
        else:
            debinfo.dh_desktop_line = ''

            
        #    E. any mime .desktop files
        debinfo.copy_files_lines = ''
        debinfo.install_dirs = sets.Set()
        for mime_desktop_file in mime_desktop_files:
            dest_file = os.path.join('debian',
                                     debinfo.package,
                                     'usr/share/applications',
                                     os.path.split(mime_desktop_file)[-1])
            debinfo.install_dirs.add('usr/share/applications')
            debinfo.copy_files_lines += '\n\tcp %s %s'%(mime_desktop_file,dest_file)

        depends.extend(parse_vals(cfg,module_name,'Depends') )
        debinfo.depends = ', '.join(depends)
        
        debinfo.description = description
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
            
            # svn commit #50703 should make life easier (#50707 is
            # better comment), but bugs aren't all fixed yet.
            # 'python-setuptools (>= 0.6c1)',
            
            'python-setuptools',
            ]
        
        if use_pycentral:
            build_deps.extend(  [
                'debhelper (>= 5.0.37.1)',
                'python-central (>= 0.4.10)',
                ] )
        else:
            build_deps.extend(  [
                'debhelper (>=5)',
                ])


        build_deps.extend( parse_vals(cfg,module_name,'Build-Depends') )
        debinfo.build_depends = ', '.join(build_deps)

        debinfo.suggests = ', '.join( parse_vals(cfg,module_name,'Suggests') )
        debinfo.recommends = ', '.join( parse_vals(cfg,module_name,'Recommends') )

        debinfo.source_stanza_extras = ''
        
        build_conflicts = parse_vals(cfg,module_name,'Build-Conflicts')
        if len(build_conflicts):
            debinfo.source_stanza_extras += ('Build-Conflicts: '+
                                              ', '.join( build_conflicts )+'\n')

        if use_pycentral:
            debinfo.source_stanza_extras += 'XS-Python-Version: all\n'
            debinfo.package_stanza_extras = """\
XB-Python-Version: ${python:Versions}
Provides: ${python:Provides}
"""
        else:
            debinfo.package_stanza_extras = ''
            
        conflicts = parse_vals(cfg,module_name,'Conflicts')
        if len(conflicts):
            debinfo.package_stanza_extras += ('Conflicts: '+
                                              ', '.join( conflicts )+'\n')

        provides = parse_vals(cfg,module_name,'Provides')
        if len(provides):
            debinfo.package_stanza_extras += ('Provides: ' +
                                              ', '.join( provides  )+'\n')
        debinfo.dirlist = ""
        
    def _make_cfg_defaults(self,
                           module_name=NotGiven,
                           default_distribution=NotGiven,
                           default_maintainer=NotGiven,
                           ):
        defaults = {}

        defaults['Source']=debianize_name(module_name)
        defaults['Package']='python-%s'%(debianize_name(module_name),)

        defaults['Distribution']=default_distribution

        defaults['Debian-Version']='1'
        defaults['Upstream-Version-Prefix']=''
        defaults['Upstream-Version-Suffix']=''

        defaults['Maintainer'] = default_maintainer

        defaults['Build-Depends'] = ''
        defaults['Build-Conflicts'] = ''
        defaults['Depends'] = ''
        defaults['Suggests'] = ''
        defaults['Recommends'] = ''

        defaults['Conflicts'] = ''
        defaults['Provides'] = ''

        defaults['MIME-Desktop-Files'] = ''
        defaults['MIME-File'] = ''
        defaults['Shared-MIME-File'] = ''
        return defaults

def build_dsc(debinfo,dist_dir,repackaged_dirname,
              orig_tgz_no_change=None,
              remove_expanded_source_dir=0):
    """make debian source package"""
    if 1:    
        #    A. Find new dirname and delete any pre-existing contents
        fullpath_repackaged_dirname = os.path.join(dist_dir,repackaged_dirname)

            
        ###############################################
        # 3. make temporary original source tarball
        
        #    Note that, for the final tarball, best practices suggest
        #    using "dpkg-source -b".  See
        #    http://www.debian.org/doc/developers-reference/ch-best-pkging-practices.en.html

        if orig_tgz_no_change is not None:
            repackaged_orig_tarball = '%(source)s_%(upstream_version)s.orig.tar.gz'%debinfo.__dict__
            repackaged_orig_tarball_path = os.path.join(dist_dir,repackaged_orig_tarball)
            if os.path.exists(repackaged_orig_tarball_path):
                os.unlink(repackaged_orig_tarball_path)
            os.link(orig_tgz_no_change,repackaged_orig_tarball_path)
        elif 0:
            repackaged_orig_tarball = '%(source)s_%(upstream_version)s.orig.tar.gz'%debinfo.__dict__
            make_tarball(repackaged_orig_tarball,
                         repackaged_dirname,
                         cwd=dist_dir)
        else:
            repackaged_orig_tarball = 'orig.tar'
            make_tarball(repackaged_orig_tarball,
                         repackaged_dirname,
                         cwd=dist_dir)
        ###############################################
        # 4. create debian/ directory and contents
        
        debian_dir = os.path.join(fullpath_repackaged_dirname,'debian')
        if not os.path.exists(debian_dir):
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
        control = CONTROL_FILE%debinfo.__dict__
        fd = open( os.path.join(debian_dir,'control'), mode='w')
        fd.write(control)
        fd.close()
        
        #    C. debian/rules
        if debinfo.architecture == 'all':
            debinfo.rules_binary=RULES_BINARY_INDEP%debinfo.__dict__
        else:
            debinfo.rules_binary=RULES_BINARY_ARCH%debinfo.__dict__

        rules = RULES_MAIN%debinfo.__dict__

        rules = rules.replace('        ','\t')
        rules_fname = os.path.join(debian_dir,'rules')
        fd = open( rules_fname, mode='w')
        fd.write(rules)
        fd.close()
        os.chmod(rules_fname,0755)

        fd = open( os.path.join(debian_dir,
                                debinfo.package+'.dirs'),
                   mode='w')
        for install_dir in debinfo.install_dirs:
            fd.write(install_dir+'\n')
        fd.close()

        #    D. debian/compat
        fd = open( os.path.join(debian_dir,'compat'), mode='w')
        fd.write('4\n')
        fd.close()

        #    E. debian/package.mime
        if debinfo.mime_file != '':
            os.link( debinfo.mime_file,
                     os.path.join(debian_dir,debinfo.package+'.mime'))
        if debinfo.shared_mime_file != '':
            os.link( debinfo.shared_mime_file,
                     os.path.join(debian_dir,
                                  debinfo.package+'.sharedmimeinfo'))

        ###############################################
        # 5. unpack original source tarball

        #    A. move debianized tree away
        os.rename(fullpath_repackaged_dirname,
                  fullpath_repackaged_dirname+'.debianized')
        #    B. expand repackaged original tarball
        expand_tarball(repackaged_orig_tarball,cwd=dist_dir)
        #    C. move original repackaged tree to .orig
        os.rename(fullpath_repackaged_dirname,fullpath_repackaged_dirname+'.orig')
        #    D. restore debianized tree
        os.rename(fullpath_repackaged_dirname+'.debianized',
                  fullpath_repackaged_dirname)
        if orig_tgz_no_change is None:
            #    E. remove repackaged original tarball
            #       (we re-generate it using best practices below)
            os.unlink(os.path.join(dist_dir,repackaged_orig_tarball))

            ###############################################
            # 6. call "dpkg-source -b"
            # http://www.debian.org/doc/developers-reference/ch-best-pkging-practices.en.html
            dpkg_source_b(repackaged_dirname,
                          repackaged_dirname+'.orig',
                          cwd=dist_dir)
        else:
            dpkg_source_b(repackaged_dirname,
                          cwd=dist_dir)
            

        if remove_expanded_source_dir:
            shutil.rmtree(fullpath_repackaged_dirname)


CONTROL_FILE = """\
Source: %(source)s
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
"""

RULES_MAIN = """\
#!/usr/bin/make -f

# automatically generated by stdeb

PACKAGE_NAME=%(package)s

PYVERS=%(pycentral_showversions)s

build: build-stamp
build-stamp: $(PYVERS:%%=build-python%%)
        touch $@
build-python%%:
# Force setuptools, but reset sys.argv[0] to 'setup.py' because setup.py files expect that.
        python$* -c "import setuptools,sys;f='setup.py';sys.argv[0]=f;execfile(f)" build
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
# Force setuptools, but reset sys.argv[0] to 'setup.py' because setup.py files expect that.
        python$* -c "import setuptools,sys;f='setup.py';sys.argv[0]=f;execfile(f)" install \
                --no-compile --single-version-externally-managed \
                --root $(CURDIR)/debian/${PACKAGE_NAME}         # install only one Egg dir (without python's version number)

%(rules_binary)s

.PHONY: build clean binary-indep binary-arch binary install configure
"""
        
RULES_BINARY_INDEP="""\
binary-arch:
        
binary-indep: build install
        dh_testdir -i
        dh_testroot -i
        dh_python -i
        dh_installdocs -i
        dh_installdirs -i
        dh_installexamples  -i%(dh_installmime_line)s
        dh_strip -i%(copy_files_lines)s%(dh_desktop_line)s
        dh_compress -i -X.py
        dh_fixperms -i
        dh_installdeb -i
        dh_gencontrol -i
        dh_md5sums -i
        dh_builddeb -i

binary: binary-indep binary-arch
"""

RULES_BINARY_ARCH="""\
binary-indep:

binary-arch: build install
        dh_testdir -a
        dh_testroot -a
        dh_python -a
        dh_installdocs -a
        dh_installdirs -a
        dh_installexamples  -a%(dh_installmime_line)s
        dh_strip -a%(copy_files_lines)s%(dh_desktop_line)s
        dh_compress -a -X.py
        dh_fixperms -a
        dh_installdeb -a
        dh_shlibdeps -a
        dh_gencontrol -a
        dh_md5sums -a
        dh_builddeb -a

binary: binary-indep binary-arch
"""
