#
# This module contains most of the code of stdeb.
#
import re, sys, os, shutil, sets, select
import ConfigParser
import subprocess
import tempfile
import stdeb
import pkg_resources
from stdeb import log, __version__ as __stdeb_version__

__all__ = ['DebianInfo','build_dsc','expand_tarball','expand_zip',
           'stdeb_cmdline_opts','stdeb_cmd_bool_opts','recursive_hardlink',
           'apply_patch','repack_tarball_with_debianized_dirname',
           'expand_sdist_file']

import exceptions
class CalledProcessError(exceptions.Exception): pass

def check_call(*popenargs, **kwargs):
    retcode = subprocess.call(*popenargs, **kwargs)
    if retcode == 0:
        return
    raise CalledProcessError(retcode)

stdeb_cmdline_opts = [
    ('dist-dir=', 'd',
     "directory to put final built distributions in (default='deb_dist')"),
    ('no-pycentral', 'C',
     'do not use pycentral (support for multiple Python versions)'),
    ('patch-already-applied','a',
     'patch was already applied (used when py2dsc calls sdist_dsc)'),
    ('default-distribution=', 'z',
     "distribution name to use if not specified in .cfg (default='unstable')"),
    ('default-maintainer=', 'm',
     'maintainer name and email to use if not specified in .cfg '
     '(default from setup.py)'),
    ('extra-cfg-file=','x',
     'additional .cfg file (in addition to .egg-info/stdeb.cfg if present)'),
    ('patch-file=','p',
     'patch file applied before setup.py called '
     '(incompatible with file specified in .cfg)'),
    ('patch-level=','l',
     'patch file applied before setup.py called '
     '(incompatible with file specified in .cfg)'),
    ('patch-posix','q',
     'apply the patch with --posix mode'),
    ('remove-expanded-source-dir','r',
     'remove the expanded source directory'),
    ('ignore-install-requires', 'i',
     'ignore the requirements from requires.txt in the egg-info directory'),
    ]

stdeb_cmd_bool_opts = [
    'patch-already-applied',
    'no-pycentral',
    'remove-expanded-source-dir',
    'patch-posix',
    'ignore-install-requires'
    ]

class NotGiven: pass

def process_command(args, cwd=None):
    if not isinstance(args, (list, tuple)):
        raise RuntimeError, "args passed must be in a list"
    check_call(args, cwd=cwd)

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
    "make name acceptable as a Debian (binary) package name"
    name = name.replace('_','')
    name = name.replace('.','-')
    name = name.lower()
    return name

def source_debianize_name(name):
    "make name acceptable as a Debian source package name"
    name = name.replace('_','')
    name = name.replace('.','-')
    name = name.lower()
    return name

def debianize_version(name):
    "make name acceptable as a Debian package name"
    name = name.replace('_','-')

    # XXX should use setuptools' version sorting and do this properly:
    name = name.replace('.dev','~dev')

    name = name.lower()
    return name

def get_date_822():
    """return output of 822-date command"""
    cmd = '/bin/date'
    if not os.path.exists(cmd):
        raise ValueError('%s command does not exist.'%cmd)
    args = [cmd,'-R']
    cmd = subprocess.Popen(args,stdout=subprocess.PIPE)
    returncode = cmd.wait()
    if returncode:
        log.error('ERROR running: %s', ' '.join(args))
        raise RuntimeError('returncode %d', returncode)
    result = cmd.stdout.read().strip()
    return result

def get_deb_depends_from_setuptools_requires(requirements):
    depends = [] # This will be the return value from this function.

    requirements = list(pkg_resources.parse_requirements(requirements))
    if not requirements:
        return depends

    if not os.path.exists('/usr/bin/apt-file'):
        raise ValueError('apt-file not in /usr/bin. Please install '
                         'with: sudo apt-get install apt-file')

    # Ask apt-file for any packages which have a .egg-info file by
    # these names.

    # Note that apt-file appears to think that some packages
    # e.g. setuptools itself have "foo.egg-info/BLAH" files but not a
    # "foo.egg-info" directory.

    egginfore=("(/(%s)(?:-[^/]+)?(?:-py[0-9]\.[0-9.]+)?\.egg-info)"
               % '|'.join(req.project_name for req in requirements))

    args = ["apt-file", "search", "--ignore-case", "--regexp", egginfore]
    try:
        cmd = subprocess.Popen(args, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    except Exception, le:
        log.error('ERROR running: %s', ' '.join(args))
        raise RuntimeError('exception %s from subprocess %s' % (le,args))
    returncode = cmd.wait()
    if returncode:
        log.error('ERROR running: %s', ' '.join(args))
        raise RuntimeError('returncode %d from subprocess %s' % (returncode,
                                                                 args))

    inlines = cmd.stdout.readlines()

    dd = {} # {pydistname: {pydist: set(debpackagename)}}
    E=re.compile(egginfore, re.I)
    D=re.compile("^([^:]*):", re.I)
    eggsndebs = set()
    for l in inlines:
        if l:
            emo = E.search(l)
            assert emo, l
            dmo = D.search(l)
            assert dmo, l
            eggsndebs.add((emo.group(1), dmo.group(1)))

    for (egginfo, debname) in eggsndebs:
        pydist = pkg_resources.Distribution.from_filename(egginfo)
        try:
            dd.setdefault(
                pydist.project_name.lower(), {}).setdefault(
                pydist, set()).add(debname)
        except ValueError, le:
            log.warn("I got an error parsing a .egg-info file named \"%s\" "
                     "from Debian package \"%s\" as a pkg_resources "
                     "Distribution: %s" % (egginfo, debname, le,))
            pass

    # Now for each requirement, see if a Debian package satisfies it.
    ops = {'<':'<<','>':'>>','==':'=','<=':'<=','>=':'>='}
    for req in requirements:
        reqname = req.project_name.lower()
        gooddebs = set()
        for pydist, debs in dd.get(reqname, {}).iteritems():
            if pydist in req:
                ## log.info("I found Debian packages \"%s\" which provides "
                ##          "Python package \"%s\", version \"%s\", which "
                ##          "satisfies our version requirements: \"%s\""
                ##          % (', '.join(debs), req.project_name, ver, req)
                gooddebs |= (debs)
            else:
                log.info("I found Debian packages \"%s\" which provides "
                         "Python package \"%s\" which "
                         "does not satisfy our version requirements: "
                         "\"%s\" -- ignoring."
                         % (', '.join(debs), req.project_name, req))
        if not gooddebs:
            log.warn("I found no Debian package which provides the required "
                     "Python package \"%s\" with version requirements "
                     "\"%s\"."% (req.project_name, req.specs))
        elif len(gooddebs) == 1:
            log.info("I found a Debian package which provides the require "
                     "Python package.  Python package: \"%s\", "
                     "Debian package: \"%s\";  adding Depends specifications "
                     "for the following version(s): \"%s\""
                     % (req.project_name, tuple(gooddebs)[0], req.specs))
        else:
            log.warn("I found multiple Debian packages which provide the "
                     "Python distribution required.  I'm listing them all "
                     "as alternates.  Candidate debs which claim to provide "
                     "the Python package \"%s\" are: \"%s\""
                     % (req.project_name, ', '.join(gooddebs),))

        alts = []
        for deb in gooddebs:
            added_any_alt = False
            for spec in req.specs:
                # Here we blithely assume that the Debian package
                # versions are enough like the Python package versions
                # that the requirement can be ported straight over...
                alts.append("%s (%s %s)" % (deb, ops[spec[0]], spec[1]))
                added_any_alt = True

            if not added_any_alt:
                # No alternates were added, but we have the name of a
                # good package.
                alts.append("%s"%deb)

        if len(alts):
            depends.append(' | '.join(alts))

    return depends

def make_tarball(tarball_fname,directory,cwd=None):
    "create a tarball from a directory"
    if tarball_fname.endswith('.gz'): opts = 'czf'
    else: opts = 'cf'
    args = ['/bin/tar',opts,tarball_fname,directory]
    process_command(args, cwd=cwd)


def expand_tarball(tarball_fname,cwd=None):
    "expand a tarball"
    if tarball_fname.endswith('.gz'): opts = 'xzf'
    elif tarball_fname.endswith('.bz2'): opts = 'xjf'
    else: opts = 'xf'
    args = ['/bin/tar',opts,tarball_fname]
    process_command(args, cwd=cwd)


def expand_zip(zip_fname,cwd=None):
    "expand a zip"
    args = ['/usr/bin/unzip',zip_fname]
    # Does it have a top dir
    res = subprocess.Popen(
        [args[0], '-l', args[1]], cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    contents = []
    for line in res.stdout.readlines()[3:-2]:
        contents.append(line.split()[-1])
    commonprefix = os.path.commonprefix(contents)
    if not commonprefix:
        extdir = os.path.join(cwd, os.path.basename(zip_fname[:-4]))
        args.extend(['-d', os.path.abspath(extdir)])

    process_command(args, cwd=cwd)


def expand_sdist_file(sdist_file,cwd=None):
    lower_sdist_file = sdist_file.lower()
    if lower_sdist_file.endswith('.zip'):
        expand_zip(sdist_file,cwd=cwd)
    elif lower_sdist_file.endswith('.tar.bz2'):
        expand_tarball(sdist_file,cwd=cwd)
    elif lower_sdist_file.endswith('.tar.gz'):
        expand_tarball(sdist_file,cwd=cwd)
    else:
        raise RuntimeError('could not guess format of original sdist file')

def repack_tarball_with_debianized_dirname( orig_sdist_file,
                                            repacked_sdist_file,
                                            debianized_dirname,
                                            original_dirname ):
    working_dir = tempfile.mkdtemp()
    expand_sdist_file( orig_sdist_file, cwd=working_dir )
    fullpath_original_dirname = os.path.join(working_dir,original_dirname)
    fullpath_debianized_dirname = os.path.join(working_dir,debianized_dirname)

    # ensure sdist looks like sdist:
    assert os.path.exists( fullpath_original_dirname )
    assert len(os.listdir(working_dir))==1

    if fullpath_original_dirname != fullpath_debianized_dirname:
        # rename original dirname to debianized dirname
        os.rename(fullpath_original_dirname,
                  fullpath_debianized_dirname)
    make_tarball(repacked_sdist_file,debianized_dirname,cwd=working_dir)
    shutil.rmtree(working_dir)

def dpkg_source(b_or_x,arg1,arg2=None,cwd=None):
    "call dpkg-source -b|x arg1 [arg2]"
    assert b_or_x in ['-b','-x']
    args = ['/usr/bin/dpkg-source',b_or_x,arg1]
    if arg2 is not None:
        args.append(arg2)

    process_command(args, cwd=cwd)

def apply_patch(patchfile,cwd=None,posix=False,level=0):
    """call 'patch -p[level] [--posix] < arg1'

    posix mode is sometimes necessary. It keeps empty files so that
    dpkg-source removes their contents.

    """
    if not os.path.exists(patchfile):
        raise RuntimeError('patchfile "%s" does not exist'%patchfile)
    fd = open(patchfile,mode='r')

    level_str = '-p%d'%level
    args = ['/usr/bin/patch',level_str]
    if posix:
        args.append('--posix')

    log.info('PATCH COMMAND: %s < %s', ' '.join(args), patchfile)
    log.info('  PATCHING in dir: %s', cwd)
#    print >> sys.stderr, 'PATCH COMMAND:',' '.join(args),'<',patchfile
#    print >> sys.stderr, '  PATCHING in dir:',cwd
    res = subprocess.Popen(
        args, cwd=cwd,
        stdin=fd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        )
    returncode=None
    while returncode is None:
        returncode = res.poll()
        ready = select.select( [res.stdout,res.stderr],[],[],0.1)
        # XXX figure out how to do this without reading byte-by-byte
        if res.stdout in ready[0]:
            sys.stdout.write(res.stdout.read(1))
            sys.stdout.flush()
        if res.stderr in ready[0]:
            sys.stderr.write(res.stderr.read(1))
            sys.stderr.flush()
    # finish outputting file
    sys.stdout.write(res.stdout.read())
    sys.stdout.flush()
    sys.stderr.write(res.stderr.read())
    sys.stderr.flush()

    if returncode:
        log.error('ERROR running: %s', ' '.join(args))
        log.error('ERROR in %s', cwd)
#        print >> sys.stderr, 'ERROR running: %s'%(' '.join(args),)
#        print >> sys.stderr, 'ERROR in',cwd
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
    vals = vals.split('#')[0]
    vals = vals.strip()
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
        assert len(vals)==1, (section, option, vals, type(vals))
    return vals[0]

class DebianInfo:
    """encapsulate information for Debian distribution system"""
    def __init__(self,
                 cfg_files=NotGiven,
                 module_name=NotGiven,
                 default_distribution=NotGiven,
                 default_maintainer=NotGiven,
                 upstream_version=NotGiven,
                 egg_module_name=NotGiven,
                 no_pycentral=NotGiven,
                 has_ext_modules=NotGiven,
                 description=NotGiven,
                 long_description=NotGiven,
                 patch_file=None,
                 patch_level=None,
                 install_requires=None,
                 setup_requires=None,
                 ):
        if cfg_files is NotGiven: raise ValueError("cfg_files must be supplied")
        if module_name is NotGiven: raise ValueError(
            "module_name must be supplied")
        if default_distribution is NotGiven: raise ValueError(
            "default_distribution must be supplied")
        if default_maintainer is NotGiven: raise ValueError(
            "default_maintainer must be supplied")
        if upstream_version is NotGiven: raise ValueError(
            "upstream_version must be supplied")
        if no_pycentral is NotGiven: raise ValueError(
            "no_pycentral must be supplied")
        if has_ext_modules is NotGiven: raise ValueError(
            "has_ext_modules must be supplied")
        if description is NotGiven: raise ValueError(
            "description must be supplied")
        if long_description is NotGiven: raise ValueError(
            "long_description must be supplied")

        cfg_defaults = self._make_cfg_defaults(
            module_name=module_name,
            default_distribution=default_distribution,
            default_maintainer=default_maintainer,
            )

        cfg = ConfigParser.SafeConfigParser(cfg_defaults)
        cfg.read(cfg_files)

        self.stdeb_version = __stdeb_version__
        self.module_name = module_name
        self.source = parse_val(cfg,module_name,'Source')
        self.package = parse_val(cfg,module_name,'Package')
        forced_upstream_version = parse_val(cfg,module_name,
                                            'Forced-Upstream-Version')
        if forced_upstream_version == '':
            upstream_version_prefix = parse_val(cfg,module_name,
                                                'Upstream-Version-Prefix')
            upstream_version_suffix = parse_val(cfg,module_name,
                                                'Upstream-Version-Suffix')
            self.upstream_version = (upstream_version_prefix+
                                        debianize_version(upstream_version)+
                                        upstream_version_suffix)
        else:
            if (debianize_version(forced_upstream_version) !=
                forced_upstream_version):
                raise ValueError('forced upstream version ("%s") not a '
                                 'Debian-compatible version (e.g. "%s")'%(
                    forced_upstream_version,
                    debianize_version(forced_upstream_version)))
            self.upstream_version = forced_upstream_version
        self.egg_module_name = egg_module_name
        self.epoch = parse_val(cfg,module_name,'Epoch')
        if self.epoch != '' and not self.epoch.endswith(':'):
            self.epoch = self.epoch + ':'
        self.packaging_version = parse_val(cfg,module_name,'Debian-Version')
        self.dsc_version = '%s-%s'%(
            self.upstream_version,
            self.packaging_version)
        self.full_version = '%s%s-%s'%(
            self.epoch,
            self.upstream_version,
            self.packaging_version)
        self.distname = parse_val(cfg,module_name,'Distribution')
        self.maintainer = ', '.join(parse_vals(cfg,module_name,'Maintainer'))
        self.uploaders = parse_vals(cfg,module_name,'Uploaders')
        self.date822 = get_date_822()
        if not no_pycentral:
            self.pycentral_showversions='$(shell pyversions -vr)'
        else:
            current = sys.version[:3]
            self.pycentral_showversions=current


        build_deps = ['python-setuptools (>= 0.6b3)']
        build_deps.extend(
            get_deb_depends_from_setuptools_requires(setup_requires))

        depends = []

        depends.append('${python:Depends}')

        if has_ext_modules:
            self.architecture = 'any'
            depends.append('${shlibs:Depends}')
        else:
            self.architecture = 'all'

        self.copyright_file = parse_val(cfg,module_name,'Copyright-File')
        self.mime_file = parse_val(cfg,module_name,'MIME-File')

        self.shared_mime_file = parse_val(cfg,module_name,'Shared-MIME-File')

        if self.mime_file == '' and self.shared_mime_file == '':
            self.dh_installmime_line = ''
        else:
            self.dh_installmime_line = '\n        dh_installmime'
            if self.architecture == 'all':
                self.dh_installmime_line += ' -i'
            else:
                self.dh_installmime_line += ' -a'

        mime_desktop_files = parse_vals(cfg,module_name,'MIME-Desktop-Files')
        if len(mime_desktop_files):
            self.dh_desktop_line = '\n        dh_desktop'
            if self.architecture == 'all':
                self.dh_desktop_line += ' -i'
            else:
                self.dh_desktop_line += ' -a'
        else:
            self.dh_desktop_line = ''

        self.fix_scripts = RULES_FIX_SCRIPTS%self.__dict__

        #    E. any mime .desktop files
        self.copy_files_lines = ''
        self.install_dirs = sets.Set()
        for mime_desktop_file in mime_desktop_files:
            dest_file = os.path.join('debian',
                                     self.package,
                                     'usr/share/applications',
                                     os.path.split(mime_desktop_file)[-1])
            self.install_dirs.add('usr/share/applications')
            self.copy_files_lines += '\n\tcp %s %s'%(
                mime_desktop_file,dest_file)

        depends.extend(parse_vals(cfg,module_name,'Depends') )
        depends.extend(get_deb_depends_from_setuptools_requires(
            install_requires))
        self.depends = ', '.join(depends)

        self.description = description
        if long_description != 'UNKNOWN':
            ld2=[]
            for line in long_description.split('\n'):
                ls = line.strip()
                if len(ls):
                    ld2.append(' '+line)
                else:
                    ld2.append(' .')
            self.long_description = '\n'.join(ld2)
        else:
            self.long_description = ''

        if not no_pycentral:
            build_deps.extend(  [
                'python-all-dev (>= 2.3.5-11)',
                'debhelper (>= 5.0.38)',
                'python-central (>= 0.5.6)',
                ] )
        else:
            build_deps.extend(  [
                'python-all-dev',
                'debhelper (>=5)',
                ])

        build_deps.extend( parse_vals(cfg,module_name,'Build-Depends') )
        self.build_depends = ', '.join(build_deps)

        self.suggests = ', '.join( parse_vals(cfg,module_name,'Suggests') )
        self.recommends = ', '.join( parse_vals(cfg,module_name,'Recommends') )

        self.source_stanza_extras = ''

        build_conflicts = parse_vals(cfg,module_name,'Build-Conflicts')
        if len(build_conflicts):
            self.source_stanza_extras += ('Build-Conflicts: '+
                                              ', '.join( build_conflicts )+'\n')

        self.patch_file = parse_val(cfg,module_name,'Stdeb-Patch-File')

        if patch_file is not None:
            if self.patch_file != '':
                raise RuntimeError('A patch file was specified on the command '
                                   'line and in .cfg file.')
            else:
                self.patch_file = patch_file

        self.patch_level = parse_val(cfg,module_name,'Stdeb-Patch-Level')
        if self.patch_level != '':
            if patch_level is not None:
                raise RuntimeError('A patch level was specified on the command '
                                   'line and in .cfg file.')
            else:
                self.patch_level = int(self.patch_level)
        else:
            if patch_level is not None:
                self.patch_level = patch_level
            else:
                self.patch_level = 0

        xs_python_version = parse_vals(cfg,module_name,'XS-Python-Version')
        if not no_pycentral:
            self.source_stanza_extras += ('XS-Python-Version: '+
                                             ', '.join(xs_python_version)+'\n')
            self.package_stanza_extras = """\
XB-Python-Version: ${python:Versions}
"""
            self.debhelper_command = 'dh_pycentral'
        else:
            self.package_stanza_extras = ''
            self.debhelper_command = 'dh_python'

        dpkg_shlibdeps_params = parse_val(
            cfg,module_name,'dpkg-shlibdeps-params')
        if dpkg_shlibdeps_params:
            self.dh_shlibdeps_line = ('dh_shlibdeps -a '
                                     '--dpkg-shlibdeps-params=%s' %
                                      dpkg_shlibdeps_params)
        else:
            self.dh_shlibdeps_line = 'dh_shlibdeps -a'
        print >> sys.stderr,'self.dh_shlibdeps_line',self.dh_shlibdeps_line

        conflicts = parse_vals(cfg,module_name,'Conflicts')
        if len(conflicts):
            self.package_stanza_extras += ('Conflicts: '+
                                              ', '.join( conflicts )+'\n')

        provides = parse_vals(cfg,module_name,'Provides')
        provides.insert(0, 'Provides: ${python:Provides}')
        self.package_stanza_extras += ', '.join( provides  )+'\n'

        replaces = parse_vals(cfg,module_name,'Replaces')
        if len(replaces):
            self.package_stanza_extras += ('Replaces: ' +
                                              ', '.join( replaces  )+'\n')
        self.dirlist = ""

        self.setup_env_vars = parse_val(cfg,module_name,'Setup-Env-Vars')

        if self.setup_env_vars != '' and not self.setup_env_vars.endswith(' '):
            # end with a space if not empty
            self.setup_env_vars = self.setup_env_vars + ' '

    def _make_cfg_defaults(self,
                           module_name=NotGiven,
                           default_distribution=NotGiven,
                           default_maintainer=NotGiven,
                           ):
        defaults = {}

        defaults['Source']=source_debianize_name(module_name)
        #defaults['Source']='python-%s'%(debianize_name(module_name),)
        defaults['Package']='python-%s'%(debianize_name(module_name),)

        defaults['Distribution']=default_distribution

        defaults['Epoch']=''
        defaults['Debian-Version']='1'
        defaults['Forced-Upstream-Version']=''

        defaults['Upstream-Version-Prefix']=''
        defaults['Upstream-Version-Suffix']=''

        defaults['Maintainer'] = default_maintainer
        defaults['Uploaders'] = ''

        defaults['Copyright-File'] = ''

        defaults['Build-Depends'] = ''
        defaults['Build-Conflicts'] = ''
        defaults['Stdeb-Patch-File'] = ''
        defaults['Stdeb-Patch-Level'] = ''
        defaults['Depends'] = ''
        defaults['Suggests'] = ''
        defaults['Recommends'] = ''

        defaults['XS-Python-Version'] = 'all'

        defaults['dpkg-shlibdeps-params'] = ''

        defaults['Conflicts'] = ''
        defaults['Provides'] = ''
        defaults['Replaces'] = ''

        defaults['MIME-Desktop-Files'] = ''
        defaults['MIME-File'] = ''
        defaults['Shared-MIME-File'] = ''

        defaults['Setup-Env-Vars'] = ''
        return defaults

def build_dsc(debinfo,
              dist_dir,
              repackaged_dirname,
              orig_sdist=None,
              patch_posix=0,
              remove_expanded_source_dir=0):
    """make debian source package"""
    #    A. Find new dirname and delete any pre-existing contents

    # dist_dir is usually 'deb_dist'

    # the location of the copied original source package (it was
    # re-recreated in dist_dir)
    fullpath_repackaged_dirname = os.path.join(dist_dir,repackaged_dirname)

    ###############################################
    # 1. make temporary original source tarball

    #    Note that, for the final tarball, best practices suggest
    #    using "dpkg-source -b".  See
    #    http://www.debian.org/doc/developers-reference/ch-best-pkging-practices.en.html

    # Create the name of the tarball that qualifies as the upstream
    # source. If the original was specified, we'll link to
    # it. Otherwise, we generate our own .tar.gz file from the output
    # of "python setup.py sdist" (done above) so that we avoid
    # packaging .svn directories, for example.

    repackaged_orig_tarball = ('%(source)s_%(upstream_version)s.orig.tar.gz'%
                               debinfo.__dict__)
    repackaged_orig_tarball_path = os.path.join(dist_dir,
                                                repackaged_orig_tarball)
    if orig_sdist is not None:
        if os.path.exists(repackaged_orig_tarball_path):
            os.unlink(repackaged_orig_tarball_path)
        os.link(orig_sdist,repackaged_orig_tarball_path)
    else:
        make_tarball(repackaged_orig_tarball,
                     repackaged_dirname,
                     cwd=dist_dir)

    # apply patch
    if debinfo.patch_file != '':
        apply_patch(debinfo.patch_file,
                    posix=patch_posix,
                    level=debinfo.patch_level,
                    cwd=fullpath_repackaged_dirname)

    ###############################################
    # 2. create debian/ directory and contents
    debian_dir = os.path.join(fullpath_repackaged_dirname,'debian')
    if not os.path.exists(debian_dir):
        os.mkdir(debian_dir)

    #    A. debian/changelog
    fd = open( os.path.join(debian_dir,'changelog'), mode='w')
    fd.write("""\
%(source)s (%(full_version)s) %(distname)s; urgency=low

  * source package automatically created by stdeb %(stdeb_version)s

 -- %(maintainer)s  %(date822)s\n"""%debinfo.__dict__)
    fd.close()

    #    B. debian/control
    if debinfo.uploaders:
        debinfo.uploaders = 'Uploaders: %s\n' % ', '.join(debinfo.uploaders)
    else:
        debinfo.uploaders = ''
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

    #    F. debian/copyright
    if debinfo.copyright_file != '':
        os.link( debinfo.copyright_file,
                 os.path.join(debian_dir,'copyright'))

    ###############################################
    # 3. unpack original source tarball

    debianized_package_dirname = fullpath_repackaged_dirname+'.debianized'
    if os.path.exists(debianized_package_dirname):
        raise RuntimeError('debianized_package_dirname exists: %s' %
                           debianized_package_dirname)
    #    A. move debianized tree away
    os.rename(fullpath_repackaged_dirname, debianized_package_dirname )
    if orig_sdist is not None:
        #    B. expand repackaged original tarball
        tmp_dir = os.path.join(dist_dir,'tmp-expand')
        os.mkdir(tmp_dir)
        try:
            expand_tarball(orig_sdist,cwd=tmp_dir)
            orig_tarball_top_contents = os.listdir(tmp_dir)

            # make sure original tarball has exactly one directory
            assert len(orig_tarball_top_contents)==1
            orig_dirname = orig_tarball_top_contents[0]
            fullpath_orig_dirname = os.path.join(tmp_dir,orig_dirname)

            #    C. move original repackaged tree to .orig
            target = fullpath_repackaged_dirname+'.orig'
            if os.path.exists(target):
                # here from previous invocation, probably
                shutil.rmtree(target)
            os.rename(fullpath_orig_dirname,target)

        finally:
            shutil.rmtree(tmp_dir)

    #    D. restore debianized tree
    os.rename(fullpath_repackaged_dirname+'.debianized',
              fullpath_repackaged_dirname)

    #    Re-generate tarball using best practices see
    #    http://www.debian.org/doc/developers-reference/ch-best-pkging-practices.en.html
    #    call "dpkg-source -b new_dirname orig_dirname"
    log.info('CALLING dpkg-source -b %s %s (in dir %s)'%(
        repackaged_dirname,
        repackaged_orig_tarball,
        dist_dir))

    dpkg_source('-b',repackaged_dirname,
                repackaged_orig_tarball,
                cwd=dist_dir)

    if 1:
        shutil.rmtree(fullpath_repackaged_dirname)

    if not remove_expanded_source_dir:
        # expand the debian source package
        dsc_name = debinfo.source + '_' + debinfo.dsc_version + '.dsc'
        dpkg_source('-x',dsc_name,
                    cwd=dist_dir)

CONTROL_FILE = """\
Source: %(source)s
Maintainer: %(maintainer)s
%(uploaders)sSection: python
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

# This file was automatically generated by stdeb %(stdeb_version)s at
# %(date822)s

PACKAGE_NAME=%(package)s
MODULE_NAME=%(module_name)s
EGG_MODULE_NAME=%(egg_module_name)s

PYVERS=%(pycentral_showversions)s

build: build-stamp
build-stamp: $(PYVERS:%%=build-python%%)
        touch $@
build-python%%:
# Force setuptools, but reset sys.argv[0] to 'setup.py' because setup.py
# files expect that.
        %(setup_env_vars)spython$* -c "import setuptools,sys;f='setup.py';sys.argv[0]=f;execfile(f,{'__file__':f,'__name__':'__main__'})" build
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
# Force setuptools, but reset sys.argv[0] to 'setup.py' because
# setup.py files expect that.

# Python 2.6 or greater in Jaunty have a patch to install in
# /usr/local/lib. This if statement avoids that when necessary.
        if test "$*" = "2.5" -o "$*" = "2.4"; then \\
          %(setup_env_vars)spython$* -c "import setuptools,sys;f='setup.py';sys.argv[0]=f;execfile(f,{'__file__':f,'__name__':'__main__'})" install \\
            --no-compile --single-version-externally-managed \\
            --root $(CURDIR)/debian/${PACKAGE_NAME}; \\
          mv debian/${PACKAGE_NAME}/usr/lib/python$*/site-packages/*.egg-info \\
                debian/${PACKAGE_NAME}/usr/lib/python$*/site-packages/${EGG_MODULE_NAME}.egg-info; \\
        else \\
          %(setup_env_vars)spython$* -c "import setuptools,sys;f='setup.py';sys.argv[0]=f;execfile(f,{'__file__':f,'__name__':'__main__'})" install \\
            --no-compile --single-version-externally-managed --install-layout=deb \\
            --root $(CURDIR)/debian/${PACKAGE_NAME}; \\
          mv debian/${PACKAGE_NAME}/usr/lib/python$*/dist-packages/*.egg-info \\
                debian/${PACKAGE_NAME}/usr/lib/python$*/dist-packages/${EGG_MODULE_NAME}.egg-info; \\
	fi

%(rules_binary)s

.PHONY: build clean binary-indep binary-arch binary install configure
"""

RULES_BINARY_INDEP="""\
binary-arch:

binary-indep: build install
        dh_testdir -i
        dh_testroot -i
        %(debhelper_command)s -i
        dh_installdocs -i
        dh_installdirs -i
        dh_installexamples  -i%(dh_installmime_line)s
        dh_strip -i%(copy_files_lines)s%(dh_desktop_line)s
        dh_compress -i -X.py
        dh_fixperms -i
%(fix_scripts)s
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
        %(debhelper_command)s -a
        dh_installdocs -a
        dh_installdirs -a
        dh_installexamples  -a%(dh_installmime_line)s
        dh_strip -a%(copy_files_lines)s%(dh_desktop_line)s
        dh_compress -a -X.py
        dh_fixperms -a
%(fix_scripts)s
        dh_installdeb -a
        %(dh_shlibdeps_line)s
        dh_gencontrol -a
        dh_md5sums -a
        dh_builddeb -a

binary: binary-indep binary-arch
"""

RULES_FIX_SCRIPTS = r"""        : # Replace all '#!' calls to python with $(PYTHON)
        : # and make them executable
        for i in \
          `find debian/%(package)s/usr/bin -type f` \
          `find debian/%(package)s/usr/lib -type f`; \
        do \
          case "$$i" in *-[0-9].[0-9]) continue; esac; \
          sed '1s,#!.*python[^ ]*\(.*\),#! /usr/bin/python\1,' \
                $$i > $$i.temp; \
          if cmp --quiet $$i $$i.temp; then \
            rm -f $$i.temp; \
          else \
            mv -f $$i.temp $$i; \
            chmod 755 $$i; \
            echo "fixed interpreter: $$i"; \
          fi; \
        done"""
