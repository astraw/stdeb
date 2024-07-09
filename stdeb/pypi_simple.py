import re
import requests
import stdeb

USER_AGENT = 'pypi-install/%s ( https://github.com/astraw/stdeb )' % \
    stdeb.__version__


def normalize_package_name(package_name):
    return re.sub(r"[-_.]+", "-", package_name).lower()


class PyPIClient(object):
    def __init__(self, pypi_url="https://pypi.org", user_agent=USER_AGENT):
        self.pypi_url = pypi_url
        self._http_session = requests.Session()
        self._http_session.headers["User-Agent"] = user_agent

    def release_version(self, package_name):
        package_name = normalize_package_name(package_name)
        response = self._http_session.get("%s/pypi/%s/json" % (self.pypi_url, package_name))
        data = response.json()
        return data["info"]["version"]

    def release_versions(self, package_name):
        package_name = normalize_package_name(package_name)
        response = self._http_session.get(
            "%s/simple/%s" % (self.pypi_url, package_name),
            headers={"Accept": "application/vnd.pypi.simple.latest+json"})
        data = response.json()
        return data["versions"]

    def download_url(self, package_name, version):
        download_url = None
        md5_digest = None
        package_name = normalize_package_name(package_name)
        response = self._http_session.get(
            "%s/pypi/%s/%s/json" % (self.pypi_url, package_name, version))
        data = response.json()
        for url in data["urls"]:
            if url["packagetype"] == "sdist" and \
                    url["python_version"] == "source" and \
                    url["url"].endswith((".tar.gz", ".zip")):
                download_url = url["url"]
                md5_digest = url["digests"]["md5"]
                break

        return download_url, md5_digest
