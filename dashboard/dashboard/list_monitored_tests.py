"""Provides the web interface for listing monitored tests."""

import json

from google.appengine.ext import ndb

from dashboard import request_handler
from dashboard.models import graph_data


class ListMonitoredTestsHandler(request_handler.RequestHandler):
  """An endpoint to list the tests monitored by a given sheriff."""

  def get(self):
    """Returns a JSON list of tests for a sheriff.

    Request parameters:
      get-sheriffed-by: A sheriff name.
    """
    sheriff = self.request.get('get-sheriffed-by')
    if not sheriff:
      self.ReportError('No value for get-sheriffed-by.', status=400)
      return
    self.response.out.write(json.dumps(_ListMonitoredTests(sheriff)))


def _ListMonitoredTests(sheriff_name):
  """Outputs a sorted list of test paths for Tests sheriffed by a user."""
  sheriff = ndb.Key('Sheriff', sheriff_name)
  sheriffed_query = graph_data.Test.query(
      graph_data.Test.sheriff == sheriff,
      graph_data.Test.has_rows == True)
  sheriffed = sorted(t.test_path for t in sheriffed_query.fetch())
  return sheriffed
