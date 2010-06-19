import logging
__version__ = '0.6.0' # keep in sync with ../setup.py

log = logging.getLogger('stdeb')
log.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
