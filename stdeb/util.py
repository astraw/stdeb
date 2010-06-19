#
# This module contains most of the code of stdeb.
#
import re, sys, os, shutil, select
import ConfigParser
import subprocess
import tempfile
import stdeb
from stdeb import log, __version__ as __stdeb_version__

if hasattr(os,'link'):
    link_func = os.link
else:
    # matplotlib deletes link from os namespace, expected distutils workaround
    link_func = shutil.copyfile

__all__ = ['DebianInfo','build_dsc','expand_tarball','expand_zip',
           'stdeb_cmdline_opts','stdeb_cmd_bool_opts','recursive_hardlink',
           'apply_patch','repack_tarball_with_debianized_dirname',
           'expand_sdist_file','stdeb_cfg_options']

DH_MIN_VERS = '7'       # Fundamental to stdeb >= 0.4
DH_IDEAL_VERS = '7.4.3' # fixes Debian bug 548392

PYSUPPORT_MIN_VERS = '0.8.4' # Namespace package support was added
                             # sometime between 0.7.5ubuntu1 and
                             # 0.8.4lenny1 (Lenny). Might be able to
                             # back this down.

import exceptions
class CalledProcessError(exceptions.Exception): pass
class CantSatisfyRequirement(exceptions.Exception): pass

def check_call(*popenargs, **kwargs):
    retcode = subprocess.call(*popenargs, **kwargs)
    if retcode == 0:
        return
    raise CalledProcessError(retcode)

stdeb_cmdline_opts = [
    ('dist-dir=', 'd',
     "directory to put final built distributions in (default='deb_dist')"),
    ('patch-already-applied','a',
     'patch was already applied (used when py2dsc calls sdist_dsc)'),
    ('default-distribution=', None,
     "deprecated (see --suite)"),
    ('suite=', 'z',
     "distribution name to use if not specified in .cfg (default='unstable')"),
    ('default-maintainer=', None,
     'deprecated (see --maintainer)'),
    ('maintainer=', 'm',
     'maintainer name and email to use if not specified in .cfg '
     '(default from setup.py)'),
    ('extra-cfg-file=','x',
     'additional .cfg file (in addition to stdeb.cfg if present)'),
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
    ('pycentral-backwards-compatibility=',None,
     'If True (currently the default), enable migration from old stdeb '
     'that used pycentral'),
    ('workaround-548392=',None,
     'If True (currently the default), limit binary package to single Python '
     'version, working around Debian bug 548392 of debhelper'),
    ('force-buildsystem=',None,
     "If True (the default), set 'DH_OPTIONS=--buildsystem=python_distutils'"),
    ('no-backwards-compatibility',None,
     'If True, set --pycentral-backwards-compatibility=False and '
     '--workaround-548392=False. (Default=False).'),
    ('guess-conflicts-provides-replaces=',None,
     'If True, attempt to guess Conflicts/Provides/Replaces in debian/control '
     'based on apt-cache output. (Default=False).'),
    ]

# old entries from stdeb.cfg:

# These should be settable as distutils command options, but in case
# we want to support other packaging methods, they should also be
# settable outside distutils. Consequently, we keep the ability to
# parse ConfigParser files (specified with --extra-cfg-file). TODO:
# Also, some (most, in fact) of the above options should also be
# settable in the ConfigParser file.

stdeb_cfg_options = [
    # With defaults
    ('source=',None,
     'debian/control Source: (Default: <source-debianized-setup-name>)'),
    ('package=',None,
     'debian/control Package: (Default: python-<debianized-setup-name>)'),
    ('suite=',None,
     'suite (e.g. stable, lucid) in changelog (Default: unstable)'),
    ('maintainer=',None,
     'debian/control Maintainer: (Default: <setup-maintainer-or-author>)'),
    ('debian-version=',None,'debian version (Default: 1)'),
    ('section=',None,'debian/control Section: (Default: python)'),

    # With no defaults
    ('epoch=',None,'version epoch'),
    ('forced-upstream-version=',None,'forced upstream version'),
    ('upstream-version-prefix=',None,'upstream version prefix'),
    ('upstream-version-suffix=',None,'upstream version suffix'),
    ('uploaders=',None,'uploaders'),
    ('copyright-file=',None,'copyright file'),
    ('build-depends=',None,'debian/control Build-Depends:'),
    ('build-conflicts=',None,'debian/control Build-Conflicts:'),
    ('stdeb-patch-file=',None,'file containing patches for stdeb to apply'),
    ('stdeb-patch-level=',None,'patch level provided to patch command'),
    ('depends=',None,'debian/control Depends:'),
    ('suggests=',None,'debian/control Suggests:'),
    ('recommends=',None,'debian/control Recommends:'),
    ('xs-python-version=',None,'debian/control XS-Python-Version:'),
    ('dpkg-shlibdeps-params=',None,'parameters passed to dpkg-shlibdeps'),
    ('conflicts=',None,'debian/control Conflicts:'),
    ('provides=',None,'debian/control Provides:'),
    ('replaces=',None,'debian/control Replaces:'),
    ('mime-desktop-files=',None,'MIME desktop files'),
    ('mime-file=',None,'MIME file'),
    ('shared-mime-file=',None,'shared MIME file'),
    ('setup-env-vars=',None,'environment variables passed to setup.py'),
    ('udev-rules=',None,'file with rules to install to udev'),
    ]

stdeb_cmd_bool_opts = [
    'patch-already-applied',
    'remove-expanded-source-dir',
    'patch-posix',
    'ignore-install-requires',
    'no-backwards-compatibility',
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
                link_func(fullpath,newpath)
    finally:
        os.chdir(orig_dir)

def debianize_name(name):
    "make name acceptable as a Debian (binary) package name"
    name = name.replace('_','')
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

def dpkg_compare_versions(v1,op,v2):
    args = ['/usr/bin/dpkg','--compare-versions',v1,op,v2]
    cmd = subprocess.Popen(args)
    returncode = cmd.wait()
    if returncode:
        return False
    else:
        return True

def get_cmd_stdout(args):
    cmd = subprocess.Popen(args,stdout=subprocess.PIPE)
    returncode = cmd.wait()
    if returncode:
        log.error('ERROR running: %s', ' '.join(args))
        raise RuntimeError('returncode %d', returncode)
    return cmd.stdout.read()

def get_date_822():
    """return output of 822-date command"""
    cmd = '/bin/date'
    if not os.path.exists(cmd):
        raise ValueError('%s command does not exist.'%cmd)
    args = [cmd,'-R']
    result = get_cmd_stdout(args).strip()
    return result

def get_version_str(pkg):
    args = ['/usr/bin/dpkg-query','--show',
           '--showformat=${Version}',pkg]
    stdout = get_cmd_stdout(args)
    return stdout.strip()

def load_module(name,fname):
    import imp

    suffix = '.py'
    found = False
    for description in imp.get_suffixes():
        if description[0]==suffix:
            found = True
            break
    assert found

    fd = open(fname,mode='r')
    try:
        module = imp.load_module(name,fd,fname,description)
    finally:
        fd.close()
    return module

def get_deb_depends_from_setuptools_requires(requirements, on_failure="warn"):
    """
    Suppose you can't confidently figure out a .deb which satisfies a given
    requirement.  If on_failure == 'warn', then log a warning.  If on_failure
    == 'raise' then raise CantSatisfyRequirement exception.  If on_failure ==
    'guess' then guess that python-$FOO will satisfy the dependency and that
    the Python version numbers will apply to the Debian packages (in addition
    to logging a warning message).
    """
    assert on_failure in ("raise", "warn", "guess"), on_failure

    import pkg_resources

    depends = [] # This will be the return value from this function.

    parsed_reqs=[]

    for extra,reqs in pkg_resources.split_sections(requirements):
        if extra: continue
        parsed_reqs.extend(pkg_resources.parse_requirements(reqs))

    if not parsed_reqs:
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
               % '|'.join(req.project_name.replace('-', '_') for req in parsed_reqs))

    args = ["apt-file", "search", "--ignore-case", "--regexp", egginfore]

    if 1:
        # do dry run on apt-file
        dry_run_args = args[:] + ['--dummy','--non-interactive']
        cmd = subprocess.Popen(dry_run_args,stderr=subprocess.PIPE)
        returncode = cmd.wait()
        if returncode:
            err_output = cmd.stderr.read()
            raise RuntimeError('Error running "apt-file search": ' +
                               err_output.strip())

    try:
        cmd = subprocess.Popen(args, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    except Exception, le:
        # TODO: catch rc=1 and "E: The cache directory is empty. You need to
        # run 'apt-file update' first.", and tell the user to follow those
        # instructions.
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
    for req in parsed_reqs:
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
            if on_failure == 'warn':
                log.warn(
                    "I found no Debian package which provides the required "
                    "Python package \"%s\" with version requirements "
                    "\"%s\"."% (req.project_name, req.specs))
            elif on_failure == "raise":
                raise CantSatisfyRequirement(
                    "I found no Debian package which "
                    "provides the required Python package \"%s\" with version "
                    "requirements \"%s\"." % (req.project_name, req.specs), req)
            elif on_failure == "guess":
                log.warn("I found no Debian package which provides the "
                         "required Python package \"%s\" with version "
                         "requirements \"%s\".  Guessing blindly that the "
                         "name \"python-%s\" will be it, and that the Python "
                         "package version number requirements will apply to "
                         "the Debian package." % (req.project_name,
                                                  req.specs, reqname))
                gooddebs.add("python-" + reqname)
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

def apt_cache_info(apt_cache_cmd,package_name):
    if apt_cache_cmd not in ('showsrc','show'):
        raise NotImplementedError(
            "don't know how to run apt-cache command '%s'"%apt_cache_cmd)

    result_list = []
    args = ["apt-cache", apt_cache_cmd, package_name]
    cmd = subprocess.Popen(args,
                           stdin=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           stdout=subprocess.PIPE)
    returncode = cmd.wait()
    if returncode:
        errline = cmd.stderr.read()
        if not (returncode == 100 and errline == "E: You must put some 'source' URIs in your sources.list\n"):
            log.error('ERROR running: %s', ' '.join(args))
            raise RuntimeError('returncode %d from subprocess %s' % (returncode,
                                                                 args))
    inlines = cmd.stdout.read()
    version_blocks = inlines.split('\n\n')
    for version_block in version_blocks:
        block_dict = {}

        if len(version_block)==0:
            continue
        version_lines = version_block.split('\n')
        assert version_lines[0].startswith('Package: ')
        block_dict['Package'] = version_lines[0][ len('Package: '): ]

        if apt_cache_cmd == 'showsrc':
            assert version_lines[1].startswith('Binary: ')
            block_dict['Binary'] = version_lines[1][ len('Binary: '): ]
            block_dict['Binary'] = block_dict['Binary'].split(', ')

        elif apt_cache_cmd == 'show':
            for start in ('Provides: ','Conflicts: ','Replaces: '):
                key = start[:-2]
                for line in version_lines[2:]:
                    if line.startswith(start):
                        unsplit_line_result = line[ len(start): ]
                        split_result = unsplit_line_result.split(', ')
                        block_dict[key] = split_result
                if key not in block_dict:
                    block_dict[key] = []
        result_list.append(block_dict)
    return result_list

def check_cfg_files(cfg_files,module_name):
    """check if the configuration files actually specify something

    If config files are given, give warning if they don't contain
    information. This may indicate a wrong module name name, for
    example.
    """

    cfg = ConfigParser.SafeConfigParser()
    cfg.read(cfg_files)
    if cfg.has_section(module_name):
        section_items = cfg.items(module_name)
    else:
        section_items = []
    default_items = cfg.items('DEFAULT')

    n_items = len(section_items) + len(default_items)
    if n_items==0:
        log.warn('configuration files were specified, but no options were '
                 'found in "%s" or "DEFAULT" sections.' % (module_name,) )

class DebianInfo:
    """encapsulate information for Debian distribution system"""
    def __init__(self,
                 cfg_files=NotGiven,
                 module_name=NotGiven,
                 default_distribution=NotGiven,
                 guess_maintainer=NotGiven,
                 upstream_version=NotGiven,
                 has_ext_modules=NotGiven,
                 description=NotGiven,
                 long_description=NotGiven,
                 patch_file=None,
                 patch_level=None,
                 install_requires=None,
                 setup_requires=None,
                 debian_version=None,
                 workaround_548392=None,
                 force_buildsystem=None,
                 have_script_entry_points = None,
                 pycentral_backwards_compatibility=None,
                 use_setuptools = False,
                 guess_conflicts_provides_replaces = False,
                 sdist_dsc_command = None,
                 ):
        if cfg_files is NotGiven: raise ValueError("cfg_files must be supplied")
        if module_name is NotGiven: raise ValueError(
            "module_name must be supplied")
        if default_distribution is NotGiven: raise ValueError(
            "default_distribution must be supplied")
        if guess_maintainer is NotGiven: raise ValueError(
            "guess_maintainer must be supplied")
        if upstream_version is NotGiven: raise ValueError(
            "upstream_version must be supplied")
        if has_ext_modules is NotGiven: raise ValueError(
            "has_ext_modules must be supplied")
        if description is NotGiven: raise ValueError(
            "description must be supplied")
        if long_description is NotGiven: raise ValueError(
            "long_description must be supplied")

        cfg_defaults = self._make_cfg_defaults(
            module_name=module_name,
            default_distribution=default_distribution,
            guess_maintainer=guess_maintainer,
            )

        if len(cfg_files):
            check_cfg_files(cfg_files,module_name)

        cfg = ConfigParser.SafeConfigParser(cfg_defaults)
        cfg.read(cfg_files)

        if sdist_dsc_command is not None:
            # Allow distutils commands to override config files (this lets
            # command line options beat file options).
            for longopt, shortopt, desc in stdeb_cfg_options:
                name = longopt[:-1]
                name = name.replace('-','_')
                value = getattr( sdist_dsc_command, name )
                if value is not None:
                    if not cfg.has_section(module_name):
                        cfg.add_section(module_name)
                    cfg.set( module_name, name, value )

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
        self.epoch = parse_val(cfg,module_name,'Epoch')
        if self.epoch != '' and not self.epoch.endswith(':'):
            self.epoch = self.epoch + ':'
        self.packaging_version = parse_val(cfg,module_name,'Debian-Version')
        if debian_version is not None:
            # command-line arg overrides file
            self.packaging_version = debian_version
        self.dsc_version = '%s-%s'%(
            self.upstream_version,
            self.packaging_version)
        self.full_version = '%s%s-%s'%(
            self.epoch,
            self.upstream_version,
            self.packaging_version)
        self.distname = parse_val(cfg,module_name,'Suite')
        self.maintainer = ', '.join(parse_vals(cfg,module_name,'Maintainer'))
        self.uploaders = parse_vals(cfg,module_name,'Uploaders')
        self.date822 = get_date_822()

        build_deps = []
        if use_setuptools:
            build_deps.append('python-setuptools (>= 0.6b3)')
	if setup_requires is not None and len(setup_requires):
            build_deps.extend(
                get_deb_depends_from_setuptools_requires(setup_requires))

        depends = ['${misc:Depends}', '${python:Depends}']
        need_custom_binary_target = False

        self.do_pycentral_removal_preinst = pycentral_backwards_compatibility

        if has_ext_modules:
            self.architecture = 'any'
            depends.append('${shlibs:Depends}')
            build_deps.append('python-all-dev')
        else:
            self.architecture = 'all'

        self.copyright_file = parse_val(cfg,module_name,'Copyright-File')
        self.mime_file = parse_val(cfg,module_name,'MIME-File')

        self.shared_mime_file = parse_val(cfg,module_name,'Shared-MIME-File')

        if self.mime_file == '' and self.shared_mime_file == '':
            self.dh_installmime_indep_line = ''
        else:
            need_custom_binary_target = True
            self.dh_installmime_indep_line = '\tdh_installmime'

        mime_desktop_files = parse_vals(cfg,module_name,'MIME-Desktop-Files')
        if len(mime_desktop_files):
            need_custom_binary_target = True
            self.dh_desktop_indep_line = '\tdh_desktop'
        else:
            self.dh_desktop_indep_line = ''

        #    E. any mime .desktop files
        self.install_file_lines = []
        for mime_desktop_file in mime_desktop_files:
            self.install_file_lines.append(
                '%s usr/share/applications'%mime_desktop_file)

        depends.extend(parse_vals(cfg,module_name,'Depends') )
	if install_requires is not None and len(install_requires):
            depends.extend(get_deb_depends_from_setuptools_requires(
                install_requires))
        self.depends = ', '.join(depends)

        self.debian_section = parse_val(cfg,module_name,'Section')

        self.description = description
        if long_description != 'UNKNOWN':
            ld2=[]
            for line in long_description.split('\n'):
                ls = line.strip()
                if len(ls):
                    ld2.append(' '+line)
                else:
                    ld2.append(' .')
            ld2 = ld2[:20]
            self.long_description = '\n'.join(ld2)
        else:
            self.long_description = ''

        if have_script_entry_points:
            if workaround_548392:
                build_deps.append( 'debhelper (>= %s)'%DH_MIN_VERS)
            else:
                build_deps.append( 'debhelper (>= %s)'%DH_IDEAL_VERS )
        else:
            build_deps.append( 'debhelper (>= %s)'%DH_MIN_VERS )

        build_deps.append('python-support (>= %s)'%PYSUPPORT_MIN_VERS)

        build_deps.extend( parse_vals(cfg,module_name,'Build-Depends') )
        self.build_depends = ', '.join(build_deps)

        suggests = ', '.join( parse_vals(cfg,module_name,'Suggests') )
        recommends = ', '.join( parse_vals(cfg,module_name,'Recommends') )

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
        if have_script_entry_points and workaround_548392:

            # Trap cases that might trigger Debian bug #548392 and
            # workaround. Disable this block once the bugfix has
            # become widespread and change Build-Depends: to include
            # sufficiently recent debhelper.

            if len(xs_python_version)==0:
                # No Python version specified. For now, just use default Python
                log.warn('working around Debian #548392, changing '
                         'XS-Python-Version: to \'current\'')
                xs_python_version = ['current']
            else:

                # The user specified a Python version. Check if s/he
                # specified more than one. (Specifying a single
                # version won't trigger the bug.)

                pyversions_fname = '/usr/bin/pyversions'
                assert os.path.exists(pyversions_fname)
                pyversions = load_module('pyversions',pyversions_fname)
                vstring = ', '.join(xs_python_version)
                pyversions_result = pyversions.parse_versions(vstring)
                if ('versions' in pyversions_result and
                    len(pyversions_result['versions'])>1):

                    vers = list(pyversions_result['versions'])
                    # More than one Python version specified.

                    # This is dubious as the following comparison
                    # happens at source build time, but what matters
                    # is what runs when building the binary package.

                    default_vers = pyversions.default_version(version_only=True)
                    if default_vers in vers:
                        log.warn('working around Debian #548392, changing '
                                 'XS-Python-Version: to \'current\'')
                        xs_python_version = ['current']
                    else:
                        vers.sort()
                        log.warn('working around Debian #548392, changing '
                                 'XS-Python-Version: to \'%s\''%vers[-1])
                        xs_python_version = [vers[-1]]
                elif 'all' in pyversions_result:
                    log.warn('working around Debian #548392, changing '
                             'XS-Python-Version: to \'current\'')
                    xs_python_version = ['current']

        if len(xs_python_version)!=0:
            self.source_stanza_extras += ('XS-Python-Version: '+
                                          ', '.join(xs_python_version)+'\n')
        self.package_stanza_extras = """\
XB-Python-Version: ${python:Versions}
"""

        dpkg_shlibdeps_params = parse_val(
            cfg,module_name,'dpkg-shlibdeps-params')
        if dpkg_shlibdeps_params:
            need_custom_binary_target = True
            self.dh_binary_arch_lines = """\tdh binary-arch --before dh_shlibdeps
\tdh_shlibdeps -a --dpkg-shlibdeps-params=%s
\tdh binary --after dh_shlibdeps"""%dpkg_shlibdeps_params
        else:
            self.dh_binary_arch_lines = '\tdh binary-arch'
        self.dh_binary_indep_lines = '\tdh binary-indep'

        conflicts = parse_vals(cfg,module_name,'Conflicts')
        provides = parse_vals(cfg,module_name,'Provides')
        replaces = parse_vals(cfg,module_name,'Replaces')

        if guess_conflicts_provides_replaces:
            # Find list of binaries which we will conflict/provide/replace.

            cpr_binaries = set()

            # Get original Debian information for the package named the same.
            for version_info in apt_cache_info('showsrc',self.package):

                # Remember each of the binary packages produced by the Debian source
                for binary in version_info['Binary']:
                    cpr_binaries.add(binary)

                # TODO: do this for every version available , just the
                # first, or ???
                break

            # Descend each of the original binaries and see what
            # packages they conflict/ provide/ replace:
            for orig_binary in cpr_binaries:
                for version_info in apt_cache_info('show',orig_binary):
                    provides.extend( version_info['Provides'])
                    conflicts.extend(version_info['Conflicts'])
                    replaces.extend( version_info['Replaces'])

            if self.package in cpr_binaries:
                cpr_binaries.remove(self.package) # don't include ourself

            cpr_binaries = list(cpr_binaries) # convert to list

            conflicts.extend( cpr_binaries )
            provides.extend( cpr_binaries )
            replaces.extend( cpr_binaries )

            # round-trip through set to get unique entries
            conflicts = list(set(conflicts))
            provides = list(set(provides))
            replaces = list(set(replaces))

        if len(conflicts):
            self.package_stanza_extras += ('Conflicts: '+
                                              ', '.join( conflicts )+'\n')

        provides.insert(0, 'Provides: ${python:Provides}')
        self.package_stanza_extras += ', '.join( provides  )+'\n'

        if len(replaces):
            self.package_stanza_extras += ('Replaces: ' +
                                              ', '.join( replaces  )+'\n')
        if len(recommends):
            self.package_stanza_extras += ('Recommends: '+recommends+'\n')

        if len(suggests):
            self.package_stanza_extras += ('Suggests: '+suggests+'\n')

        self.dirlist = ""

        setup_env_vars = parse_vals(cfg,module_name,'Setup-Env-Vars')
        if force_buildsystem:
            setup_env_vars.append('DH_OPTIONS=--buildsystem=python_distutils')
        self.force_buildsystem = force_buildsystem
        self.exports = ""
        if len(setup_env_vars):
            self.exports += '\n'
            self.exports += '#exports specified using stdeb Setup-Env-Vars:\n'
            self.exports += '\n'.join(['export %s'%v for v in setup_env_vars])
            self.exports += '\n'
        self.udev_rules = parse_val(cfg,module_name,'Udev-Rules')

        if need_custom_binary_target:
            if self.architecture == 'all':
                self.binary_target_lines = ( \
                    RULES_BINARY_ALL_TARGET%self.__dict__ + \
                    RULES_BINARY_INDEP_TARGET%self.__dict__ )
            else:
                self.binary_target_lines = ( \
                    RULES_BINARY_TARGET%self.__dict__ + \
                    RULES_BINARY_INDEP_TARGET%self.__dict__ + \
                    RULES_BINARY_ARCH_TARGET%self.__dict__ )
        else:
            self.binary_target_lines = ''

    def _make_cfg_defaults(self,
                           module_name=NotGiven,
                           default_distribution=NotGiven,
                           guess_maintainer=NotGiven,
                           ):
        defaults = {}
        default_re = re.compile(r'^.* \(Default: (.*)\)$')
        for longopt,shortopt,description in stdeb_cfg_options:
            assert longopt.endswith('=')
            assert longopt.lower() == longopt
            key = longopt[:-1]
            matchobj = default_re.search( description )
            if matchobj is not None:
                # has a default value
                groups = matchobj.groups()
                assert len(groups)==1
                value = groups[0]
                # A few special cases
                if value == '<source-debianized-setup-name>':
                    assert key=='source'
                    value = source_debianize_name(module_name)
                elif value == 'python-<debianized-setup-name>':
                    assert key=='package'
                    value = 'python-' + debianize_name(module_name)
                elif value == '<setup-maintainer-or-author>':
                    assert key=='maintainer'
                    value = guess_maintainer
                if key=='suite':
                    if default_distribution is not None:
                        value = default_distribution
                        log.warn('Deprecation warning: you are using the '
                                 '--default-distribution option. '
                                 'Switch to the --suite option.')
            else:
                # no default value
                value = ''
            defaults[key] = value
        return defaults

def build_dsc(debinfo,
              dist_dir,
              repackaged_dirname,
              orig_sdist=None,
              patch_posix=0,
              remove_expanded_source_dir=0,
              debian_dir_only=False,
              ):
    """make debian source package"""
    #    A. Find new dirname and delete any pre-existing contents

    # dist_dir is usually 'deb_dist'

    # the location of the copied original source package (it was
    # re-recreated in dist_dir)
    if debian_dir_only:
        fullpath_repackaged_dirname = os.path.abspath(os.curdir)
    else:
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

    if not debian_dir_only:
        repackaged_orig_tarball = ('%(source)s_%(upstream_version)s.orig.tar.gz'%
                                   debinfo.__dict__)
        repackaged_orig_tarball_path = os.path.join(dist_dir,
                                                    repackaged_orig_tarball)
        if orig_sdist is not None:
            if os.path.exists(repackaged_orig_tarball_path):
                os.unlink(repackaged_orig_tarball_path)
            link_func(orig_sdist,repackaged_orig_tarball_path)
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

    for fname in ['Makefile','makefile']:
        if os.path.exists(os.path.join(fullpath_repackaged_dirname,fname)):
            sys.stderr.write('*'*1000 + '\n')
            if debinfo.force_buildsystem:
                sys.stderr.write('WARNING: a Makefile exists in this package. '
                                 'stdeb will tell debhelper 7 to use setup.py '
                                 'to build and install the package, and the '
                                 'Makefile will be ignored. You can disable '
                                 'this behavior with the '
                                 '--force-buildsystem=False argument to the '
                                 'stdeb command.\n')
            else:
                sys.stderr.write('WARNING: a Makefile exists in this package. '
                                 'debhelper 7 will attempt to use this rather '
                                 'than setup.py to build and install the '
                                 'package. You can disable this behavior with '
                                 'the --force-buildsystem=True argument to the '
                                 'stdeb command.\n')
            sys.stderr.write('*'*1000 + '\n')


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
    debinfo.percent_symbol = '%'
    rules = RULES_MAIN%debinfo.__dict__

    rules = rules.replace('        ','\t')
    rules_fname = os.path.join(debian_dir,'rules')
    fd = open( rules_fname, mode='w')
    fd.write(rules)
    fd.close()
    os.chmod(rules_fname,0755)

    #    D. debian/compat
    fd = open( os.path.join(debian_dir,'compat'), mode='w')
    fd.write('7\n')
    fd.close()

    #    E. debian/package.mime
    if debinfo.mime_file != '':
        if not os.path.exists(debinfo.mime_file):
            raise ValueError(
                'a MIME file was specified, but does not exist: %s'%(
                debinfo.mime_file,))
        link_func( debinfo.mime_file,
                 os.path.join(debian_dir,debinfo.package+'.mime'))
    if debinfo.shared_mime_file != '':
        if not os.path.exists(debinfo.shared_mime_file):
            raise ValueError(
                'a shared MIME file was specified, but does not exist: %s'%(
                debinfo.shared_mime_file,))
        link_func( debinfo.shared_mime_file,
                 os.path.join(debian_dir,
                              debinfo.package+'.sharedmimeinfo'))

    #    F. debian/copyright
    if debinfo.copyright_file != '':
        link_func( debinfo.copyright_file,
                 os.path.join(debian_dir,'copyright'))

    #    G. debian/<package>.preinst
    if debinfo.do_pycentral_removal_preinst:
        preinst = PREINST%debinfo.__dict__
        fd = open( os.path.join(debian_dir,'%s.preinst'%debinfo.package), mode='w')
        fd.write(preinst)
        fd.close()

    #    H. debian/<package>.install
    if len(debinfo.install_file_lines):
        fd = open( os.path.join(debian_dir,'%s.install'%debinfo.package), mode='w')
        fd.write('\n'.join(debinfo.install_file_lines)+'\n')
        fd.close()

    #    I. debian/<package>.udev
    if debinfo.udev_rules != '':
        fname = debinfo.udev_rules
        if not os.path.exists(fname):
            raise ValueError('udev rules file specified, but does not exist')
        link_func(fname,
                  os.path.join(debian_dir,'%s.udev'%debinfo.package))

    #    J. debian/source/format
    os.mkdir(os.path.join(debian_dir,'source'))
    fd = open( os.path.join(debian_dir,'source','format'), mode='w')
    fd.write('1.0\n')
    fd.close()

    if debian_dir_only:
        return

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

    if 1:
        # check versions of debhelper and python-support
        debhelper_version_str = get_version_str('debhelper')
        if len(debhelper_version_str)==0:
            log.warn('This version of stdeb requires debhelper >= %s, but you '
                     'do not have debhelper installed. '
                     'Could not check compatibility.'%DH_MIN_VERS)
        else:
            if not dpkg_compare_versions(
                debhelper_version_str, 'ge', DH_MIN_VERS ):
                log.warn('This version of stdeb requires debhelper >= %s. '
                         'Use stdeb 0.3.x to generate source packages '
                         'compatible with older versions of debhelper.'%(
                    DH_MIN_VERS,))

        pysupport_version_str = get_version_str('python-support')
        if len(pysupport_version_str)==0:
            log.warn('This version of stdeb requires python-support >= %s, '
                     'but you do not have python-support installed. '
                     'Could not check compatibility.'%PYSUPPORT_MIN_VERS)
        else:
            if not dpkg_compare_versions(
                pysupport_version_str, 'ge', PYSUPPORT_MIN_VERS ):
                log.warn('This version of stdeb requires python-support >= %s. '
                         'Use stdeb 0.3.x to generate source packages '
                         'compatible with older versions of python-support.'%(
                    PYSUPPORT_MIN_VERS,))

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
%(uploaders)sSection: %(debian_section)s
Priority: optional
Build-Depends: %(build_depends)s
Standards-Version: 3.8.4
%(source_stanza_extras)s
Package: %(package)s
Architecture: %(architecture)s
Depends: %(depends)s
%(package_stanza_extras)sDescription: %(description)s
%(long_description)s
"""

RULES_MAIN = """\
#!/usr/bin/make -f

# This file was automatically generated by stdeb %(stdeb_version)s at
# %(date822)s

# Unset the environment variables set by dpkg-buildpackage. (This is
# necessary because distutils is brittle with compiler/linker flags
# set. Specifically, packages using f2py will break without this.)
unexport CPPFLAGS
unexport CFLAGS
unexport CXXFLAGS
unexport FFLAGS
unexport LDFLAGS
%(exports)s

%(percent_symbol)s:
        dh $@

%(binary_target_lines)s
"""

RULES_BINARY_TARGET = """
binary: binary-arch binary-indep
"""

RULES_BINARY_ALL_TARGET = """
binary: binary-indep
"""

RULES_BINARY_ARCH_TARGET = """
binary-arch: build
%(dh_binary_arch_lines)s
"""

RULES_BINARY_INDEP_TARGET = """
binary-indep: build
%(dh_binary_indep_lines)s
%(dh_installmime_indep_line)s
%(dh_desktop_indep_line)s
"""

PREINST = """#! /bin/sh

set -e

# This was added by stdeb to workaround Debian #479852. In a nutshell,
# pycentral does not remove normally remove its symlinks on an
# upgrade. Since we're using python-support, however, those symlinks
# will be broken. This tells python-central to clean up any symlinks.
if [ -e /var/lib/dpkg/info/%(package)s.list ] && which pycentral >/dev/null 2>&1
then
    pycentral pkgremove %(package)s
fi

#DEBHELPER#
"""
