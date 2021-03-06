"""Updates the metadata for tests from descriptions in Chromium source.

Reads this file from src/tools/perf from git.chromium.org via HTTP:

  tools/perf/unit-info.json  - Units, and improvement direction for each unit.

TODO(qyearsley): Remove this request handler when units are updated from
    metadata that is sent along with test results.
"""

import base64
import binascii
import json
import logging

from google.appengine.api import urlfetch

from dashboard import request_handler
from dashboard import units_to_direction

# Paths to the unit and test description metadata files in chromium/src.
_UNIT_JSON_PATH = 'tools/perf/unit-info.json'


class UpdateTestMetadataHandler(request_handler.RequestHandler):
  """URL endpoint for updating tests from metadata in chromium source.

  Intended to be called via a cron job, but can be updated by hand by an
  administrator (by navigating to the /update_test_metadata endpoint.)
  """

  def get(self):
    """Same as post. Parameters can also be given in the query string."""
    self.post()

  def post(self):
    """Updates the test metadata.

    Outputs:
      Nothing if successful, an error message if there was an error.
    """
    units_data = _GetAndParseChromiumJsonFile(_UNIT_JSON_PATH)
    if units_data:
      units_to_direction.UpdateFromJson(units_data)
    else:
      # TODO(qyearsley): Add test coverage. See http://crbug.com/447432
      self.ReportError('Could not fetch or parse unit data.')


def _GetAndParseChromiumJsonFile(path):
  """Fetches and parses JSON file in the chromium/src repository."""
  downloaded_json = DownloadChromiumFile(path)
  if not downloaded_json:
    # TODO(qyearsley): Add test coverage. See http://crbug.com/447432
    return None
  try:
    return json.loads(downloaded_json)
  except ValueError:
    # TODO(qyearsley): Add test coverage. See http://crbug.com/447432
    logging.error('Failed to load JSON "%s" from "%s".', downloaded_json, path)
    return None


def DownloadChromiumFile(path):
  """Downloads a file in the chromium/src repository.

  This used to be done using the gitweb interface (at git.chromium.org), but
  this changed at some point. Instead of using that, we can also use gitiles
  (at chromium.googlesource.com).

  As of August 2014, gitiles doesn't seem to support fetching files as plain
  text, but supports fetching base-64 encodings of files, so we use that.
  used. If it supports fetching plain text in the future, that could also be
  used, and may be simpler.

  Args:
    path: Path to a file in the main chromium/src repository (without a leading
        slash or a leading "src/").

  Returns:
    The contents of the file as a string or None on failure.
  """
  base_url = 'https://chromium.googlesource.com/chromium/src/+/master/'
  url = '%s%s?format=TEXT' % (base_url, path)
  response = urlfetch.fetch(url)
  if response.status_code != 200:
    # TODO(qyearsley): Add test coverage. See http://crbug.com/447432
    logging.error('Got %d fetching "%s".', response.status_code, url)
    return None
  try:
    plaintext_content = base64.decodestring(response.content)
  except binascii.Error:
    # TODO(qyearsley): Add test coverage. See http://crbug.com/447432
    logging.error('Failed to decode "%s" from "%s".', response.content, url)
    return None
  return plaintext_content
