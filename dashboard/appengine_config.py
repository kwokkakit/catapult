"""App Engine config.

This module is loaded before others and can be used to set up the
App Engine environment. See:
  https://cloud.google.com/appengine/docs/python/tools/appengineconfig
"""

import logging
import os
import sys

from google.appengine.ext import vendor

# The path to the symlink to the third_party directory.
_THIRD_PARTY_LINK = os.path.join(os.path.dirname(__file__), 'third_party')

# Third-party library directories inside the third_party directory.
_THIRD_PARTY_LIBRARIES = [
    'beautifulsoup4',
    'google-api-python-client-1.4.0',
    'mock-1.0.1',
    'oauth2client-1.4.11',
    'six-1.9.0',
    'uritemplate-0.6',
    'webtest',
]


def _AddThirdPartyLibraries():
  """Registers the third party libraries with App Engine.

  In order for third-party libraries to be available in the App Engine
  runtime environment, they must be added with vendor.add. The directories
  added this way must be inside the App Engine project directory.
  In order to do this, a link can be made to the real third_party
  directory. Unfortunately, this doesn't work on Windows.
  """
  if os.name == 'nt':
    logging.error('Can not use the symlink to ../third_party on Windows.')
    return
  for library_dir in _THIRD_PARTY_LIBRARIES:
    vendor.add(os.path.join(_THIRD_PARTY_LINK, library_dir))


_AddThirdPartyLibraries()
