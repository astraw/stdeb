# setuptools is required for distutils.commands plugin we use
import logging
import setuptools
__version__ = '0.4.3'

log = logging.getLogger('stdeb')
log.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
