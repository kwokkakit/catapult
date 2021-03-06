"""Unit tests for anomaly_config module."""

import unittest

import mock

from google.appengine.ext import ndb

from dashboard import testing_common
from dashboard import utils
from dashboard.models import anomaly_config


class AnomalyConfigTest(testing_common.TestCase):

  def testGetAnomalyConfigDict(self):
    testing_common.AddDataToMockDataStore(['M'], ['b'], {'foo': {'bar': {}}})
    test = utils.TestKey('M/b/foo/bar').get()

    # The sample test has no overridden config.
    self.assertEqual({}, anomaly_config.GetAnomalyConfigDict(test))

    # Override the config for the test added above.
    # The overridden config is set in the pre-put hook of the Test.
    my_config = {
        '_comment': 'Very particular segment sizes.',
        'max_window_size': 721,
        'min_segment_size': 123,
    }
    my_patterns = [test.test_path]
    anomaly_config.AnomalyConfig(config=my_config, patterns=my_patterns).put()
    test.put()

    # The sample test now has an overridden config which is used.
    # Extraneous "comment" keys are ignored.
    expected = {
        'max_window_size': 721,
        'min_segment_size': 123,
    }
    self.assertEqual(expected, anomaly_config.GetAnomalyConfigDict(test))

  @mock.patch('logging.warning')
  def testGetAnomalyConfigDict_OverriddenConfigNotFound(
      self, mock_logging_warning):
    testing_common.AddDataToMockDataStore(['M'], ['b'], {'foo': {'bar': {}}})
    test = utils.TestKey('M/b/foo/bar').get()
    test.overridden_anomaly_config = ndb.Key('AnomalyConfig', 'Non-existent')
    self.assertEqual({}, anomaly_config.GetAnomalyConfigDict(test))
    mock_logging_warning.assert_called_once_with(
        'No AnomalyConfig fetched from key %s for test %s',
        ndb.Key('AnomalyConfig', 'Non-existent'), 'M/b/foo/bar')
    self.assertIsNone(test.key.get().overridden_anomaly_config)


if __name__ == '__main__':
  unittest.main()
