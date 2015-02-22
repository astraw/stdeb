#
# This module contains most of the code of stdeb.
#
import re, sys, os, shutil, select
import codecs
try:
    # Python 2.x
    import ConfigParser
except ImportError:
    # Python 3.x
    import configparser as ConfigParser
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

PYTHON_ALL_MIN_VERS = '2.6.6-3'

try:
    # Python 2.x
    from exceptions import Exception
except ImportError:
    # Python 3.x
    pass
class CalledProcessError(Exception): pass
class CantSatisfyRequirement(Exception): pass

def check_call(*popenargs, **kwargs):
    retcode = subprocess.call(*popenargs, **kwargs)
    if retcode == 0:
        return
    raise CalledProcessError(retcode)

if sys.version_info[0]==2:
    help_str_py2='If True, build package for python 2. (Default=True).'
    help_str_py3='If True, build package for python 3. (Default=False).'
else:
    assert sys.version_info[0]==3
    help_str_py2='If True, build package for python 2. (Default=False).'
    help_str_py3='If True, build package for python 3. (Default=True).'

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
     'This option has no effect, is here for backwards compatibility, and may '
     'be removed someday.'),
    ('workaround-548392=',None,
     'This option has no effect, is here for backwards compatibility, and may '
     'be removed someday.'),
    ('no-backwards-compatibility',None,
     'This option has no effect, is here for backwards compatibility, and may '
     'be removed someday.'),
    ('guess-conflicts-provides-replaces=',None,
     'If True, attempt to guess Conflicts/Provides/Replaces in debian/control '
     'based on apt-cache output. (Default=False).'),
    ('with-python2=',None,
     help_str_py2),
    ('with-python3=',None,
     help_str_py3),
    ('no-python2-scripts=',None,
     'If True, do not install scripts for python 2. (Default=False).'),
    ('no-python3-scripts=',None,
     'If True, do not install scripts for python 3. (Default=False).'),
    ('force-x-python3-version',None,
     'Override default minimum python3:any dependency with value from '
     'x-python3-version'),
    ('allow-virtualenv-install-location',None,
     'Allow installing into /some/random/virtualenv-path'),
    ('sign-results',None,
     'Use gpg to sign the resulting .dsc and .changes file'),
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
    ('package3=',None,
     'debian/control Package: (Default: python3-<debianized-setup-name>)'),
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
    ('depends3=',None,'debian/control Depends:'),
    ('suggests=',None,'debian/control Suggests:'),
    ('suggests3=',None,'debian/control Suggests:'),
    ('recommends=',None,'debian/control Recommends:'),
    ('recommends3=',None,'debian/control Recommends:'),
    ('xs-python-version=',None,'debian/control XS-Python-Version:'),
    ('x-python3-version=',None,'debian/control X-Python3-Version:'),
    ('dpkg-shlibdeps-params=',None,'parameters passed to dpkg-shlibdeps'),
    ('conflicts=',None,'debian/control Conflicts:'),
    ('conflicts3=',None,'debian/control Conflicts:'),
    ('provides=',None,'debian/control Provides:'),
    ('provides3=',None,'debian/control Provides3:'),
    ('replaces=',None,'debian/control Replaces:'),
    ('replaces3=',None,'debian/control Replaces3:'),
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
    'force-x-python3-version',
    'allow-virtualenv-install-location',
    'sign-results',
    ]

class NotGiven: pass

def process_command(args, cwd=None):
    if not isinstance(args, (list, tuple)):
        raise RuntimeError("args passed must be in a list")
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
    name = name.replace('_','-')
    name = name.lower()
    return name

def source_debianize_name(name):
    "make name acceptable as a Debian source package name"
    name = name.replace('_','-')
    name = name.replace('.','-')
    name = name.lower()
    return name

def debianize_version(name):
    "make name acceptable as a Debian package name"
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

def normstr(s):
    try:
        # Python 3.x
        result = str(s,'utf-8')
    except TypeError:
        # Python 2.x
        result = s
    return result

def get_date_822():
    """return output of 822-date command"""
    cmd = '/bin/date'
    if not os.path.exists(cmd):
        raise ValueError('%s command does not exist.'%cmd)
    args = [cmd,'-R']
    result = get_cmd_stdout(args).strip()
    result = normstr(result)
    return result

def get_version_str(pkg):
    args = ['/usr/bin/dpkg-query','--show',
           '--showformat=${Version}',pkg]
    stdout = get_cmd_stdout(args)
    return stdout.strip().decode('ascii')

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
    except Exception as le:
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
        except ValueError as le:
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
    unzip_path = '/usr/bin/unzip'
    if not os.path.exists(unzip_path):
        log.error('ERROR: {} does not exist'.format(unzip_path))
        sys.exit(1)
    args = [unzip_path, zip_fname]
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

def dpkg_buildpackage(*args,**kwargs):
    cwd=kwargs.pop('cwd',None)
    if len(kwargs)!=0:
        raise ValueError('only kwarg can be "cwd"')
    "call dpkg-buildpackage [arg1] [...] [argN]"
    args = ['/usr/bin/dpkg-buildpackage']+list(args)
    process_command(args, cwd=cwd)

def dpkg_source(b_or_x,arg1,cwd=None):
    "call dpkg-source -b|x arg1 [arg2]"
    assert b_or_x in ['-b','-x']
    args = ['/usr/bin/dpkg-source',b_or_x,arg1]
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
    except ConfigParser.NoSectionError as err:
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
                 setup_requires=None,
                 debian_version=None,
                 have_script_entry_points = None,
                 use_setuptools = False,
                 guess_conflicts_provides_replaces = False,
                 sdist_dsc_command = None,
                 with_python2 = None,
                 with_python3 = None,
                 no_python2_scripts = None,
                 no_python3_scripts = None,
                 force_x_python3_version=False,
                 allow_virtualenv_install_location=False,
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
        for cfg_file in cfg_files:
            with codecs.open( cfg_file, mode='r', encoding='utf-8') as fd:
                cfg.readfp(fd)

        if sdist_dsc_command is not None:
            # Allow distutils commands to override config files (this lets
            # command line options beat file options).
            for longopt, shortopt, desc in stdeb_cfg_options:
                opt_name = longopt[:-1]
                name = opt_name.replace('-','_')
                value = getattr( sdist_dsc_command, name )
                if value is not None:
                    if not cfg.has_section(module_name):
                        cfg.add_section(module_name)
                    cfg.set( module_name, opt_name, value )

        self.stdeb_version = __stdeb_version__
        self.module_name = module_name
        self.source = parse_val(cfg,module_name,'Source')
        self.package = parse_val(cfg,module_name,'Package')
        self.package3 = parse_val(cfg,module_name,'Package3')
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
            if with_python2:
                build_deps.append('python-setuptools (>= 0.6b3)')
            if with_python3:
                build_deps.append('python3-setuptools')
        if setup_requires is not None and len(setup_requires):
            build_deps.extend(
                get_deb_depends_from_setuptools_requires(setup_requires))

        depends = ['${misc:Depends}', '${python:Depends}']
        depends3 = ['${misc:Depends}', '${python3:Depends}']
        need_custom_binary_target = False

        if has_ext_modules:
            self.architecture = 'any'
            if with_python2:
                build_deps.append('python-all-dev (>= %s)'%PYTHON_ALL_MIN_VERS)
            depends.append('${shlibs:Depends}')

            self.architecture3 = 'any'
            if with_python3:
                build_deps.append('python3-all-dev')
            depends3.append('${shlibs:Depends}')

        else:
            self.architecture = 'all'
            if with_python2:
                build_deps.append('python-all (>= %s)'%PYTHON_ALL_MIN_VERS)

            self.architecture3 = 'all'
            if with_python3:
                build_deps.append('python3-all')

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
        depends3.extend(parse_vals(cfg,module_name,'Depends3') )
        self.depends = ', '.join(depends)
        self.depends3 = ', '.join(depends3)

        self.debian_section = parse_val(cfg,module_name,'Section')

        self.description = re.sub('\s+', ' ', description).strip()
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
            build_deps.append( 'debhelper (>= %s)'%DH_IDEAL_VERS )
        else:
            build_deps.append( 'debhelper (>= %s)'%DH_MIN_VERS )

        build_deps.extend( parse_vals(cfg,module_name,'Build-Depends') )
        self.build_depends = ', '.join(build_deps)

        suggests = ', '.join( parse_vals(cfg,module_name,'Suggests') )
        suggests3 = ', '.join( parse_vals(cfg,module_name,'Suggests3') )
        recommends = ', '.join( parse_vals(cfg,module_name,'Recommends') )
        recommends3 = ', '.join( parse_vals(cfg,module_name,'Recommends3') )

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

        if len(xs_python_version)!=0:
            self.source_stanza_extras += ('X-Python-Version: '+
                                          ', '.join(xs_python_version)+'\n')

        x_python3_version = parse_vals(cfg,module_name,'X-Python3-Version')
        x_python3_version = [v.strip('"') for v in x_python3_version]

        if len(x_python3_version)!=0:
            self.source_stanza_extras += ('X-Python3-Version: '+
                                          ', '.join(x_python3_version)+'\n')

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
        conflicts3 = parse_vals(cfg,module_name,'Conflicts3')
        provides = parse_vals(cfg,module_name,'Provides')
        provides3 = parse_vals(cfg,module_name,'Provides3')
        replaces = parse_vals(cfg,module_name,'Replaces')
        replaces3 = parse_vals(cfg,module_name,'Replaces3')

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
                    provides3.extend( version_info['Provides'])
                    conflicts.extend(version_info['Conflicts'])
                    conflicts3.extend(version_info['Conflicts'])
                    replaces.extend( version_info['Replaces'])
                    replaces3.extend( version_info['Replaces'])

            if self.package in cpr_binaries:
                cpr_binaries.remove(self.package) # don't include ourself

            cpr_binaries = list(cpr_binaries) # convert to list

            conflicts.extend( cpr_binaries )
            conflicts3.extend( cpr_binaries )
            provides.extend( cpr_binaries )
            provides3.extend( cpr_binaries )
            replaces.extend( cpr_binaries )
            replaces3.extend( cpr_binaries )

            # round-trip through set to get unique entries
            conflicts = list(set(conflicts))
            conflicts3 = list(set(conflicts3))
            provides = list(set(provides))
            provides3 = list(set(provides3))
            replaces = list(set(replaces))
            replaces3 = list(set(replaces3))

        self.package_stanza_extras = ''
        self.package_stanza_extras3 = ''

        if len(conflicts):
            self.package_stanza_extras += ('Conflicts: '+
                                              ', '.join( conflicts )+'\n')
        if len(conflicts3):
            self.package_stanza_extras3 += ('Conflicts: '+
                                              ', '.join( conflicts3 )+'\n')

        if len(provides):
            self.package_stanza_extras += ('Provides: '+
                                             ', '.join( provides  )+'\n')

        if len(provides3):
            self.package_stanza_extras3 += ('Provides: '+
                                             ', '.join( provides3  )+'\n')

        if len(replaces):
            self.package_stanza_extras += ('Replaces: ' +
                                              ', '.join( replaces  )+'\n')
        if len(replaces3):
            self.package_stanza_extras3 += ('Replaces: ' +
                                              ', '.join( replaces3 )+'\n')
        if len(recommends):
            self.package_stanza_extras += ('Recommends: '+recommends+'\n')

        if len(recommends3):
            self.package_stanza_extras3 += ('Recommends: '+recommends3+'\n')

        if len(suggests):
            self.package_stanza_extras += ('Suggests: '+suggests+'\n')

        if len(suggests3):
            self.package_stanza_extras3 += ('Suggests: '+suggests3+'\n')

        self.dirlist = ""

        if not (with_python2 or with_python3):
            raise RuntimeError('nothing to do - neither Python 2 or 3.')
        sequencer_with = []
        if with_python2:
            sequencer_with.append('python2')
        if with_python3:
            sequencer_with.append('python3')
        num_binary_packages = len(sequencer_with)

        no_script_lines=[]

        if no_python2_scripts:
            # install to a location where debian tools do not find them
            self.no_python2_scripts_cli_args = '--install-scripts=/trash'
            no_script_lines.append(
                'rm -rf debian/%s/trash'%(self.package,))
        else:
            self.no_python2_scripts_cli_args = ''
        if no_python3_scripts:
            # install to a location where debian tools do not find them
            self.no_python3_scripts_cli_args = '--install-scripts=/trash'
            no_script_lines.append(
                'rm -rf debian/%s/trash'%(self.package3,))
        else:
            self.no_python3_scripts_cli_args = ''

        self.scripts_cleanup = '\n'.join(['        '+s for s in no_script_lines])

        if sys.prefix != '/usr':
            if not allow_virtualenv_install_location:
                # virtualenv will set distutils
                # --prefix=/path/to/virtualenv, but unless explicitly
                # requested, we want to install into /usr.
                self.install_prefix = '--prefix=/usr'
            else:
                self.install_prefix = '--prefix=%s' % sys.prefix
        else:
            self.install_prefix = ''

        rules_override_clean_target_pythons = []
        rules_override_build_target_pythons = []
        rules_override_install_target_pythons = []
        if with_python2:
            rules_override_clean_target_pythons.append(
                RULES_OVERRIDE_CLEAN_TARGET_PY2%self.__dict__
                )
            rules_override_build_target_pythons.append(
                RULES_OVERRIDE_BUILD_TARGET_PY2%self.__dict__
                )
            rules_override_install_target_pythons.append(
                RULES_OVERRIDE_INSTALL_TARGET_PY2%self.__dict__
                )
        if with_python3:
            rules_override_clean_target_pythons.append(
                RULES_OVERRIDE_CLEAN_TARGET_PY3%self.__dict__
                )
            rules_override_build_target_pythons.append(
                RULES_OVERRIDE_BUILD_TARGET_PY3%self.__dict__
                )
            rules_override_install_target_pythons.append(
                RULES_OVERRIDE_INSTALL_TARGET_PY3%self.__dict__
                )
        self.rules_override_clean_target_pythons = '\n'.join(rules_override_clean_target_pythons)
        self.rules_override_build_target_pythons = '\n'.join(rules_override_build_target_pythons)
        self.rules_override_install_target_pythons = '\n'.join(rules_override_install_target_pythons)

        self.override_dh_auto_clean = RULES_OVERRIDE_CLEAN_TARGET%self.__dict__
        self.override_dh_auto_build = RULES_OVERRIDE_BUILD_TARGET%self.__dict__
        self.override_dh_auto_install = RULES_OVERRIDE_INSTALL_TARGET%self.__dict__

        if force_x_python3_version and with_python3 and x_python3_version and \
                x_python3_version[0]:
            # override dh_python3 target to modify the dependencies
            # to ensure that the passed minimum X-Python3-Version is usedby
            version = x_python3_version[0]
            if not version.endswith('~'):
                version += '~'
            self.override_dh_python3 = RULES_OVERRIDE_PYTHON3%{
                'scripts': (
                    '        sed -i ' +
                    '"s/\([ =]python3:any (\)>= [^)]*\()\)/\\1%s\\2/g" ' +
                    'debian/%s.substvars') % (version, self.package3)
            }
        else:
            self.override_dh_python3 = ''

        sequencer_options = ['--with '+','.join(sequencer_with)]
        sequencer_options.append('--buildsystem=python_distutils')
        self.sequencer_options = ' '.join(sequencer_options)

        setup_env_vars = parse_vals(cfg,module_name,'Setup-Env-Vars')
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

        if with_python2:
            self.control_py2_stanza = CONTROL_PY2_STANZA%self.__dict__
        else:
            self.control_py2_stanza = ''

        if with_python3:
            self.control_py3_stanza = CONTROL_PY3_STANZA%self.__dict__
        else:
            self.control_py3_stanza = ''

        self.with_python2 = with_python2
        self.with_python3 = with_python3
        self.no_python2_scripts = no_python2_scripts
        self.no_python3_scripts = no_python3_scripts

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
                elif value == 'python3-<debianized-setup-name>':
                    assert key=='package3'
                    value = 'python3-' + debianize_name(module_name)
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
              sign_dsc=False,
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
            sys.stderr.write('WARNING: a Makefile exists in this package. '
                             'stdeb will tell debhelper 7 to use setup.py '
                             'to build and install the package, and the '
                             'Makefile will be ignored.\n')
            sys.stderr.write('*'*1000 + '\n')


    ###############################################
    # 2. create debian/ directory and contents
    debian_dir = os.path.join(fullpath_repackaged_dirname,'debian')
    if not os.path.exists(debian_dir):
        os.mkdir(debian_dir)

    #    A. debian/changelog
    changelog = CHANGELOG_FILE%debinfo.__dict__
    with codecs.open( os.path.join(debian_dir,'changelog'),
                 mode='w', encoding='utf-8') as fd:
        fd.write(changelog)

    #    B. debian/control
    if debinfo.uploaders:
        debinfo.uploaders = 'Uploaders: %s\n' % ', '.join(debinfo.uploaders)
    else:
        debinfo.uploaders = ''
    control = CONTROL_FILE%debinfo.__dict__
    with codecs.open( os.path.join(debian_dir,'control'),
                      mode='w', encoding='utf-8') as fd:
        fd.write(control)

    #    C. debian/rules
    debinfo.percent_symbol = '%'
    rules = RULES_MAIN%debinfo.__dict__

    rules = rules.replace('        ','\t')
    rules_fname = os.path.join(debian_dir,'rules')
    with codecs.open( rules_fname,
                      mode='w', encoding='utf-8') as fd:
        fd.write(rules)
    os.chmod(rules_fname,0o755)

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
    fd.write('3.0 (quilt)\n')
    fd.close()

    fd = open( os.path.join(debian_dir,'source','options'), mode='w')
    fd.write('extend-diff-ignore="\.egg-info$"')
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

            #    C. remove original repackaged tree
            shutil.rmtree(fullpath_orig_dirname)

        finally:
            shutil.rmtree(tmp_dir)

    if 1:
        # check versions of debhelper and python-all
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

        python_defaults_version_str = get_version_str('python-all')
        if len(python_defaults_version_str)==0:
            log.warn('This version of stdeb requires python-all >= %s, '
                     'but you do not have this package installed. '
                     'Could not check compatibility.'%PYTHON_ALL_MIN_VERS)
        else:
            if not dpkg_compare_versions(
                python_defaults_version_str, 'ge', PYTHON_ALL_MIN_VERS):
                log.warn('This version of stdeb requires python-all >= %s. '
                         'Use stdeb 0.6.0 or older to generate source packages '
                         'that use python-support.'%(
                    PYTHON_ALL_MIN_VERS,))

    #    D. restore debianized tree
    os.rename(fullpath_repackaged_dirname+'.debianized',
              fullpath_repackaged_dirname)

    #    Re-generate tarball using best practices see
    #    http://www.debian.org/doc/developers-reference/ch-best-pkging-practices.en.html

    if sign_dsc:
        args = ()
    else:
        args = ('-uc','-us')

    dpkg_buildpackage('-S','-sa',*args,cwd=fullpath_repackaged_dirname)

    if 1:
        shutil.rmtree(fullpath_repackaged_dirname)

    if not remove_expanded_source_dir:
        # expand the debian source package
        dsc_name = debinfo.source + '_' + debinfo.dsc_version + '.dsc'
        dpkg_source('-x',dsc_name,
                    cwd=dist_dir)

CHANGELOG_FILE = """\
%(source)s (%(full_version)s) %(distname)s; urgency=low

  * source package automatically created by stdeb %(stdeb_version)s

 -- %(maintainer)s  %(date822)s\n"""

CONTROL_FILE = """\
Source: %(source)s
Maintainer: %(maintainer)s
%(uploaders)sSection: %(debian_section)s
Priority: optional
Build-Depends: %(build_depends)s
Standards-Version: 3.9.1
%(source_stanza_extras)s

%(control_py2_stanza)s

%(control_py3_stanza)s
"""

CONTROL_PY2_STANZA = """
Package: %(package)s
Architecture: %(architecture)s
Depends: %(depends)s
%(package_stanza_extras)sDescription: %(description)s
%(long_description)s
"""

CONTROL_PY3_STANZA = """
Package: %(package3)s
Architecture: %(architecture3)s
Depends: %(depends3)s
%(package_stanza_extras3)sDescription: %(description)s
%(long_description)s
"""

RULES_MAIN = """\
#!/usr/bin/make -f

# This file was automatically generated by stdeb %(stdeb_version)s at
# %(date822)s
%(exports)s
%(percent_symbol)s:
        dh $@ %(sequencer_options)s

%(override_dh_auto_clean)s

%(override_dh_auto_build)s

%(override_dh_auto_install)s

override_dh_python2:
        dh_python2 --no-guessing-versions

%(override_dh_python3)s

%(binary_target_lines)s
"""

RULES_OVERRIDE_CLEAN_TARGET_PY2 = "        python setup.py clean -a"
RULES_OVERRIDE_CLEAN_TARGET_PY3 = "        python3 setup.py clean -a"
RULES_OVERRIDE_CLEAN_TARGET = """
override_dh_auto_clean:
%(rules_override_clean_target_pythons)s
        find . -name \*.pyc -exec rm {} \;
"""

RULES_OVERRIDE_BUILD_TARGET_PY2 = "        python setup.py build --force"
RULES_OVERRIDE_BUILD_TARGET_PY3 = "        python3 setup.py build --force"
RULES_OVERRIDE_BUILD_TARGET = """
override_dh_auto_build:
%(rules_override_build_target_pythons)s
"""

RULES_OVERRIDE_INSTALL_TARGET_PY2 = "        python setup.py install --force --root=debian/%(package)s --no-compile -O0 --install-layout=deb %(install_prefix)s %(no_python2_scripts_cli_args)s"

RULES_OVERRIDE_INSTALL_TARGET_PY3 = "        python3 setup.py install --force --root=debian/%(package3)s --no-compile -O0 --install-layout=deb %(install_prefix)s %(no_python3_scripts_cli_args)s"

RULES_OVERRIDE_INSTALL_TARGET = """
override_dh_auto_install:
%(rules_override_install_target_pythons)s
%(scripts_cleanup)s
"""

RULES_OVERRIDE_PYTHON3 = """
override_dh_python3:
        dh_python3
%(scripts)s
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
