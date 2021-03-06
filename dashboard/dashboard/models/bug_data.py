"""The database models for bug data."""

import logging

from google.appengine.ext import ndb


BUG_STATUS_OPENED = 'opened'
BUG_STATUS_CLOSED = 'closed'
BUG_STATUS_RECOVERED = 'recovered'

BISECT_STATUS_STARTED = 'started'
BISECT_STATUS_COMPLETED = 'completed'
BISECT_STATUS_FAILED = 'failed'


class Bug(ndb.Model):
  """Information about a bug created in issue tracker.

  Keys for Bug entities will be in the form ndb.Key('Bug', <bug_id>).
  """
  status = ndb.StringProperty(
      default=BUG_STATUS_OPENED,
      choices=[
          BUG_STATUS_OPENED,
          BUG_STATUS_CLOSED,
          BUG_STATUS_RECOVERED,
      ],
      indexed=True)

  # Status of the latest bisect run for this bug
  # (e.g., started, failed, completed).
  latest_bisect_status = ndb.StringProperty(
      default=None,
      choices=[
          BISECT_STATUS_STARTED,
          BISECT_STATUS_COMPLETED,
          BISECT_STATUS_FAILED,
      ],
      indexed=True)

  # List of owner's email that was cced.
  cced_owners = ndb.StringProperty(repeated=True)

  # The time that the Bug entity was created.
  timestamp = ndb.DateTimeProperty(indexed=True, auto_now_add=True)


def SetBisectStatus(bug_id, status):
  """Sets bisect status for bug with bug_id."""
  if bug_id is None or bug_id < 0:
    return
  bug = ndb.Key('Bug', int(bug_id)).get()
  if bug:
    bug.latest_bisect_status = status
    bug.put()
  else:
    logging.error('Bug %s does not exist.', bug_id)
