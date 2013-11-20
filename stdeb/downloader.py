import os
import xmlrpclib
import urllib2
import hashlib
import warnings

class Urllib2Transport(xmlrpclib.Transport):
    def __init__(self, opener=None, https=False, use_datetime=0):
        xmlrpclib.Transport.__init__(self, use_datetime)
        self.opener = opener or urllib2.build_opener()
        self.https = https

    def request(self, host, handler, request_body, verbose=0):
        proto = ('http', 'https')[bool(self.https)]
        req = urllib2.Request('%s://%s%s' % (proto, host, handler), request_body)
        req.add_header('User-agent', self.user_agent)
        req.add_header('Content-Type', 'text/xml')
        self.verbose = verbose
        return self.parse_response(self.opener.open(req))

def myprint(mystr,fd=None):
    if fd is None:
        print mystr
    else:
        print >> fd, mystr

USER_AGENT = 'pypi-install/0.6.0+git ( https://github.com/astraw/stdeb )'

def find_tar_gz(package_name, pypi_url = 'https://python.org/pypi',verbose=0):
    transport = Urllib2Transport(https=pypi_url.startswith("https"))
    transport.user_agent = USER_AGENT
    pypi = xmlrpclib.ServerProxy(pypi_url, transport=transport)

    download_url = None
    expected_md5_digest = None

    if verbose >= 2:
        myprint( 'querying PyPI (%s) for package name "%s"' % (pypi_url,
                                                               package_name) )
    releases = pypi.package_releases(package_name)
    if verbose >= 2:
        myprint( 'found releases: %s' % (', '.join(releases),) )
    if len(releases) > 1:
        # XXX how to sort versions?
        raise NotImplementedError('no ability to handle more than one release')
    for version in releases:

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

def get_source_tarball(package_name,verbose=0,allow_unsafe_download=False):
    download_url, expected_md5_digest = find_tar_gz(package_name,
                                                    verbose=verbose)
    if not download_url.startswith('https://'):
        if allow_unsafe_download:
            warnings.warn('downloading from unsafe url: %s' % download_url)
        else:
            raise ValueError('PYPI returned unsafe url: %s' % download_url)

    fname = download_url.split('/')[-1]
    if expected_md5_digest is not None:
        if os.path.exists(fname):
            m = hashlib.md5()
            m.update(open(fname,mode='r').read())
            actual_md5_digest = m.hexdigest()
            if actual_md5_digest == expected_md5_digest:
                if verbose >= 1:
                    myprint( 'Download URL: %s' % download_url )
                    myprint( 'File "%s" already exists with correct checksum.' % fname )
                return fname
            else:
                raise ValueError('File "%s" exists but has wrong checksum.'%fname)
    if verbose >= 1:
        myprint( 'downloading %s' % download_url )
    request = urllib2.Request(download_url)
    request.add_header('User-Agent', USER_AGENT )
    opener = urllib2.build_opener()
    package_tar_gz = opener.open(request).read()
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
