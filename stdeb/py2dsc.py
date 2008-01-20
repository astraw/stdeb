#!/usr/bin/env python
USAGE = """\
usage: py2dsc [options] distfile
   or: py2dsc --help

where distfile is a .zip or .tar.gz file built with the sdist command
of distutils.
"""

import sys, os, shutil, subprocess
from distutils.util import strtobool
from distutils.fancy_getopt import FancyGetopt, translate_longopt
from stdeb.util import DebianInfo, stdeb_cmdline_opts, stdeb_cmd_bool_opts
from stdeb.util import expand_sdist_file, apply_patch

class OptObj: pass

def runit():
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
        print USAGE
        parser.set_option_table(stdeb_cmdline_opts)
        parser.print_help("Options:")
        return 0

    if len(args)!=1:
        print 'not given single argument (distfile), args=%s'%repr(args)
        print USAGE
        return 1


    sdist_file = args[0]

    if not os.path.isfile(sdist_file):
        # Let's try PyPi
        print >> sys.stderr, "Package not found, trying PyPi"
        from setuptools.package_index import PackageIndex
        from pkg_resources import Requirement
        idx = PackageIndex()
        package = Requirement.parse(args[0])
        sdist_file = idx.fetch_distribution(package, '.',
                                            force_scan=True,
                                            source=True).location
        print >> sys.stderr, sdist_file

    final_dist_dir = optobj.__dict__.get('dist_dir','deb_dist')
    tmp_dist_dir = os.path.join(final_dist_dir,'tmp_py2dsc')
    if os.path.exists(tmp_dist_dir):
        shutil.rmtree(tmp_dist_dir)
    os.makedirs(tmp_dist_dir)

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
        print >> sys.stderr, 'py2dsc applying patch',patch_file
        apply_patch(patch_file,
                    posix=patch_posix,
                    level=patch_level,
                    cwd=tmp_dist_dir)
        patch_already_applied = 1
    else:
        patch_already_applied = 0
    ##############################################


    abs_dist_dir = os.path.abspath(final_dist_dir)

    extra_args = []
    for long in parser.long_opts:
        if long in ['dist-dir=','patch-file=']:
            continue # dealt with by this invocation
        attr = parser.get_attr_name(long)[:-1]
        if hasattr(optobj,attr):
            val = getattr(optobj,attr)
            extra_args.append('--'+long+str(val))

    args = [sys.executable,'-c',"import stdeb, sys; f='setup.py'; sys.argv[0]=f; execfile(f,{'__file__':f,'__name__':'__main__'})",
            'sdist_dsc','--dist-dir=%s'%abs_dist_dir,
            '--patch-already-applied=%s'%str(patch_already_applied),
            '--use-premade-distfile=%s'%os.path.abspath(sdist_file)]+extra_args

    print >> sys.stderr, '-='*20
    print >> sys.stderr, "Note that the .cfg file(s), if present, have not been "\
          "read at this stage. If options are necessary, pass them from the "\
          "command line"
    print >> sys.stderr, "running the following command in directory: %s\n%s"%(
        fullpath_repackaged_dirname,
        ' '.join(args))
    print >> sys.stderr, '-='*20

    res = subprocess.Popen(
        args,cwd=fullpath_repackaged_dirname,
        #stdout=subprocess.PIPE,
        #stderr=subprocess.PIPE,
        )
    returncode = res.wait()
    if returncode:
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
