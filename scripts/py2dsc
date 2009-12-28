#!/usr/bin/env python
USAGE = """\
usage: py2dsc [options] distfile
   or: py2dsc --help

where distfile is a .zip or .tar.gz file built with the sdist command
of distutils.
"""

import sys, os, shutil, subprocess
from ConfigParser import SafeConfigParser
from distutils.util import strtobool
from distutils.fancy_getopt import FancyGetopt, translate_longopt
from stdeb.util import stdeb_cmdline_opts, stdeb_cmd_bool_opts
from stdeb.util import expand_sdist_file, apply_patch
from stdeb import log

from setuptools.package_index import PackageIndex, distros_for_filename, \
                                     EXTENSIONS
from pkg_resources import Requirement, Distribution

EXTRA_OPTS = [('process-dependencies', 'D', "process package dependencies")]


class OptObj: pass

def runit():
    # process command-line options
    bool_opts = map(translate_longopt, stdeb_cmd_bool_opts)
    bool_opts.append('process-dependencies')
    parser = FancyGetopt(stdeb_cmdline_opts+[
        ('help', 'h', "show detailed help message"),
        ]+EXTRA_OPTS)
    optobj = OptObj()
    args = parser.getopt(object=optobj)
    idx = PackageIndex()
    for option in optobj.__dict__:
        value = getattr(optobj,option)
        is_string = type(value) == str
        if option in bool_opts and is_string:
            setattr(optobj, option, strtobool(value))

    if hasattr(optobj,'help'):
        print USAGE
        parser.set_option_table(stdeb_cmdline_opts + EXTRA_OPTS)
        parser.print_help("Options:")
        return 0

    if len(args)!=1:
        log.error('not given single argument (distfile), args=%r', args)
        print USAGE
        return 1


    sdist_file = args[0]

    package = None

    final_dist_dir = optobj.__dict__.get('dist_dir','deb_dist')
    tmp_dist_dir = os.path.join(final_dist_dir,'tmp_py2dsc')
    if os.path.exists(tmp_dist_dir):
        shutil.rmtree(tmp_dist_dir)
    os.makedirs(tmp_dist_dir)

    if not os.path.isfile(sdist_file):
        for ext in EXTENSIONS:
            if sdist_file.endswith(ext):
                raise IOError, "File not found"
        package = Requirement.parse(sdist_file)
        log.info("Package %s not found, trying PyPI..." % sdist_file)
        dist = idx.fetch_distribution(package, final_dist_dir,
                                            force_scan=True,
                                            source=True)
        if hasattr(dist, 'location'):
            sdist_file = dist.location
        else:
            raise Exception, "Distribution not found on PyPi"
        log.info("Got %s", sdist_file)

    dist = list(distros_for_filename(sdist_file))[0]
    idx.scan_egg_links(dist.location)
    package = idx.obtain(Requirement.parse(dist.project_name))

    if hasattr(optobj, 'process_dependencies'):
        if bool(int(getattr(optobj, 'process_dependencies'))):
            backup_argv = sys.argv[:]
            oldargv = sys.argv[:]
            oldargv.pop(-1)

            if package.requires():
                log.info("Processing package dependencies for %s", package)
            for req in package.requires():
#                print >> sys.stderr
                new_argv = oldargv + ["%s" % req]
                log.info("Bulding dependency package %s", req)
                log.info("  running '%s'", ' '.join(new_argv))
                sys.argv = new_argv
                runit()
#                print >> sys.stderr
            if package.requires():
                log.info("Completed building dependencies "
                         "for %s, continuing...", package)
        sys.argv = backup_argv

    if package is not None and hasattr(optobj, 'extra_cfg_file'):
        # Allow one to have patch-files setup on config file for example
        local_parser = SafeConfigParser()
        local_parser.readfp(open(optobj.__dict__.get('extra_cfg_file')))
        if local_parser.has_section(package.project_name):
            for opt in local_parser.options(package.project_name):
                _opt = opt.replace('_', '-')
                if parser.has_option(_opt) or parser.has_option(_opt+'='):
                    setattr(optobj, opt,
                            local_parser.get(package.project_name, opt))

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
        if long in ['dist-dir=','patch-file=', 'process-dependencies']:
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

    args = [sys.executable,'-c',"import stdeb, sys; f='setup.py'; " + \
            "sys.argv[0]=f; execfile(f,{'__file__':f,'__name__':'__main__'})",
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

def main():
    sys.exit(runit())

if __name__=='__main__':
    main()
