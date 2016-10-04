from __future__ import print_function
import sys, os, shutil, subprocess
try:
    # python 2.x
    from ConfigParser import SafeConfigParser
except ImportError as err:
    # python 3.x
    from configparser import SafeConfigParser
from distutils.util import strtobool
from distutils.fancy_getopt import FancyGetopt, translate_longopt
from stdeb.util import stdeb_cmdline_opts, stdeb_cmd_bool_opts
from stdeb.util import expand_sdist_file, apply_patch
from stdeb import log

from pkg_resources import Requirement, Distribution

class OptObj: pass

def runit(cmd,usage):
    if cmd not in ['sdist_dsc','bdist_deb']:
        raise ValueError('unknown command %r'%cmd)
    # process command-line options
    bool_opts = map(translate_longopt, stdeb_cmd_bool_opts)
    parser = FancyGetopt(stdeb_cmdline_opts+[
        ('help', 'h', "show detailed help message"),
        ])
    optobj = OptObj()
    args = parser.getopt(object=optobj)
    for option in optobj.__dict__:
        value = getattr(optobj,option)
        is_string = type(value) == str
        if option in bool_opts and is_string:
            setattr(optobj, option, strtobool(value))

    if hasattr(optobj,'help'):
        print(usage)
        parser.set_option_table(stdeb_cmdline_opts)
        parser.print_help("Options:")
        return 0

    if len(args)!=1:
        log.error('not given single argument (distfile), args=%r', args)
        print(usage)
        return 1

    sdist_file = args[0]

    final_dist_dir = optobj.__dict__.get('dist_dir','deb_dist')
    tmp_dist_dir = os.path.join(final_dist_dir,'tmp_py2dsc')
    if os.path.exists(tmp_dist_dir):
        shutil.rmtree(tmp_dist_dir)
    os.makedirs(tmp_dist_dir)

    if not os.path.isfile(sdist_file):
        log.error("Package %s not found."%sdist_file)
        sys.exit(1)

    patch_file = optobj.__dict__.get('patch_file',None)
    patch_level = int(optobj.__dict__.get('patch_level',0))
    patch_posix = int(optobj.__dict__.get('patch_posix',0))

    expand_dir = os.path.join(tmp_dist_dir,'stdeb_tmp')
    if os.path.exists(expand_dir):
        shutil.rmtree(expand_dir)
    if not os.path.exists(tmp_dist_dir):
        os.mkdir(tmp_dist_dir)
    os.mkdir(expand_dir)

    expand_sdist_file(os.path.abspath(sdist_file),cwd=expand_dir)



    # now the sdist package is expanded in expand_dir
    expanded_root_files = os.listdir(expand_dir)
    assert len(expanded_root_files)==1
    repackaged_dirname = expanded_root_files[0]
    fullpath_repackaged_dirname = os.path.join(tmp_dist_dir,repackaged_dirname)
    base_dir = os.path.join(expand_dir,expanded_root_files[0])
    if os.path.exists(fullpath_repackaged_dirname):
        # prevent weird build errors if this dir exists
        shutil.rmtree(fullpath_repackaged_dirname)
    os.renames(base_dir, fullpath_repackaged_dirname)
    del base_dir # no longer useful

    ##############################################
    if patch_file is not None:
        log.info('py2dsc applying patch %s', patch_file)
        apply_patch(patch_file,
                    posix=patch_posix,
                    level=patch_level,
                    cwd=fullpath_repackaged_dirname)
        patch_already_applied = 1
    else:
        patch_already_applied = 0
    ##############################################


    abs_dist_dir = os.path.abspath(final_dist_dir)

    extra_args = []
    for long in parser.long_opts:
        if long in ['dist-dir=','patch-file=']:
            continue # dealt with by this invocation
        attr = parser.get_attr_name(long).rstrip('=')
        if hasattr(optobj,attr):
            val = getattr(optobj,attr)
            if attr=='extra_cfg_file':
                val = os.path.abspath(val)
            if long in bool_opts or long.replace('-', '_') in bool_opts:
                extra_args.append('--%s' % long)
            else:
                extra_args.append('--'+long+str(val))

    if patch_already_applied == 1:
        extra_args.append('--patch-already-applied')

    if cmd=='bdist_deb':
        extra_args.append('bdist_deb')

    args = [sys.executable,'setup.py','--command-packages','stdeb.command',
            'sdist_dsc','--dist-dir=%s'%abs_dist_dir,
            '--use-premade-distfile=%s'%os.path.abspath(sdist_file)]+extra_args

    log.info('-='*35 + '-')
#    print >> sys.stderr, '-='*20
#    print >> sys.stderr, "Note that the .cfg file(s), if present, have not "\
#          "been read at this stage. If options are necessary, pass them from "\
#          "the command line"
    log.info("running the following command in directory: %s\n%s",
             fullpath_repackaged_dirname, ' '.join(args))
    log.info('-='*35 + '-')

    try:
        returncode = subprocess.call(
            args,cwd=fullpath_repackaged_dirname,
            )
    except:
        log.error('ERROR running: %s', ' '.join(args))
        log.error('ERROR in %s', fullpath_repackaged_dirname)
        raise

    if returncode:
        log.error('ERROR running: %s', ' '.join(args))
        log.error('ERROR in %s', fullpath_repackaged_dirname)
        #log.error('   stderr: %s'res.stderr.read())
        #print >> sys.stderr, 'ERROR running: %s'%(' '.join(args),)
        #print >> sys.stderr, res.stderr.read()
        return returncode
        #raise RuntimeError('returncode %d'%returncode)
    #result = res.stdout.read().strip()

    shutil.rmtree(tmp_dist_dir)
    return returncode
