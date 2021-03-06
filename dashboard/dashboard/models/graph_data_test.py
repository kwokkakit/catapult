"""Unit tests for graph_data module."""

import unittest

from dashboard import testing_common
from dashboard.models import graph_data


class GraphDataTest(testing_common.TestCase):

  def testPutTestTruncatesDescription(self):
    master = graph_data.Master(id='M').put()
    bot = graph_data.Bot(parent=master, id='b').put()
    long_string = 500 * 'x'
    too_long = long_string + 'y'
    key = graph_data.Test(id='a', parent=bot, description=too_long).put()
    self.assertEqual(long_string, key.get().description)


if __name__ == '__main__':
  unittest.main()
