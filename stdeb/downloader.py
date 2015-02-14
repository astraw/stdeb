from __future__ import print_function
import os
try:
    # Python 2.x
    import xmlrpclib
except ImportError:
    # Python 3.x
    import xmlrpc.client as xmlrpclib
from functools import partial
import requests
import hashlib
import warnings
import stdeb
from stdeb.transport import RequestsTransport

myprint=print

USER_AGENT = 'pypi-install/%s ( https://github.com/astraw/stdeb )'%stdeb.__version__

def find_tar_gz(package_name, pypi_url = 'https://pypi.python.org/pypi',
                verbose=0, release=None):
    transport = RequestsTransport()
    transport.user_agent = USER_AGENT
    if pypi_url.startswith('https://'):
        transport.use_https = True
    pypi = xmlrpclib.ServerProxy(pypi_url, transport=transport)

    download_url = None
    expected_md5_digest = None

    if verbose >= 2:
        myprint( 'querying PyPI (%s) for package name "%s"' % (pypi_url,
                                                               package_name) )

    show_hidden=True
    all_releases = pypi.package_releases(package_name,show_hidden)
    if release is not None:
        # A specific release is requested.
        if verbose >= 2:
            myprint( 'found all available releases: %s' % (', '.join(all_releases),) )

        if release not in all_releases:
            raise ValueError('your desired release %r is not among available '
                             'releases %r'%(release,all_releases))
        version = release
    else:
        default_releases = pypi.package_releases(package_name)
        if len(default_releases)!=1:
            raise RuntimeError('Expected one and only one release. '
                               'Non-hidden: %r. All: %r'%(
                default_releases,all_releases))
        default_release = default_releases[0]
        if verbose >= 2:
            myprint( 'found default release: %s' % (', '.join(default_releases),) )

        version = default_release

    urls = pypi.release_urls( package_name,version)
    for url in urls:
        if url['packagetype']=='sdist':
            assert url['python_version']=='source', 'how can an sdist not be a source?'
            if url['url'].endswith('.tar.gz'):
                download_url = url['url']
                if 'md5_digest' in url:
                    expected_md5_digest = url['md5_digest']
                break

    if download_url is None:
        # PyPI doesn't have package. Is download URL provided?
        result = pypi.release_data(package_name,version)
        if result['download_url'] != 'UNKNOWN':
            download_url = result['download_url']
            # no download URL provided, see if PyPI itself has download
            urls = pypi.release_urls( result['name'], result['version'] )
    if download_url is None:
        raise ValueError('no package "%s" was found'%package_name)
    return download_url, expected_md5_digest

def md5sum(filename):
    # from http://stackoverflow.com/questions/7829499/using-hashlib-to-compute-md5-digest-of-a-file-in-python-3
    with open(filename, mode='rb') as f:
        d = hashlib.md5()
        for buf in iter(partial(f.read, 128), b''):
            d.update(buf)
    return d.hexdigest()

def get_source_tarball(package_name,verbose=0,allow_unsafe_download=False,
                       release=None):
    download_url, expected_md5_digest = find_tar_gz(package_name,
                                                    verbose=verbose,
                                                    release=release)
    if not download_url.startswith('https://'):
        if allow_unsafe_download:
            warnings.warn('downloading from unsafe url: %r' % download_url)
        else:
            raise ValueError('PYPI returned unsafe url: %r' % download_url)

    fname = download_url.split('/')[-1]
    if expected_md5_digest is not None:
        if os.path.exists(fname):
            actual_md5_digest = md5sum(fname)
            if actual_md5_digest == expected_md5_digest:
                if verbose >= 1:
                    myprint( 'Download URL: %s' % download_url )
                    myprint( 'File "%s" already exists with correct checksum.' % fname )
                return fname
            else:
                raise ValueError('File "%s" exists but has wrong checksum.'%fname)
    if verbose >= 1:
        myprint( 'downloading %s' % download_url )
    headers = {'User-Agent': USER_AGENT }
    r = requests.get(download_url, headers=headers)
    r.raise_for_status()
    package_tar_gz = r.content
    if verbose >= 1:
        myprint( 'done downloading %d bytes.' % ( len(package_tar_gz), ) )
    if expected_md5_digest is not None:
        m = hashlib.md5()
        m.update(package_tar_gz)
        actual_md5_digest = m.hexdigest()
        if verbose >= 2:
            myprint( 'md5:   actual %s\n     expected %s' % (actual_md5_digest,
                                                             expected_md5_digest))
        if actual_md5_digest != expected_md5_digest:
            raise ValueError('actual and expected md5 digests do not match')
    else:
        warnings.warn('no md5 digest found -- cannot verify source file')

    fd = open(fname,mode='wb')
    fd.write( package_tar_gz )
    fd.close()
    return fname
