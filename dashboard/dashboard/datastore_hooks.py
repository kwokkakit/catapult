"""Adds pre hook to data store queries to hide internal-only data.

Checks if the user has a google.com address, and hides data with the
internal_only property set if not.
"""

import webapp2

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import users
from google.appengine.datastore import datastore_pb

from dashboard import check_whitelisted_ip
from dashboard import request_handler

# The list below contains all kinds that have an internal_only property.
# IMPORTANT: any new data types with internal_only properties must be added
# here in order to be restricted to internal users.
_INTERNAL_ONLY_KINDS = [
    'Bot',
    'Test',
    'Row',
    'Sheriff',
    'Anomaly',
]

# Permissions namespaces.
EXTERNAL = 'externally_visible'
INTERNAL = 'internal_only'


def InstallHooks():
  """Installs datastore pre hook to add access checks to queries.

  This only needs to be called once, when doing config (currently in
  appengine_config.py).
  """
  apiproxy_stub_map.apiproxy.GetPreCallHooks().Push(
      '_DatastorePreHook', _DatastorePreHook, 'datastore_v3')


def SetPrivilegedRequest():
  """Allows the current request to act as a privileged user.

  This should ONLY be called for handlers that are restricted from end users
  by some other mechanism (IP whitelisting, admin-only pages).

  This should be set once per request, before accessing the data store.
  """
  request = webapp2.get_request()
  request.registry['privileged'] = True


def _IsServicingPrivilegedRequest():
  """Checks whether the request is considered privileged."""
  try:
    request = webapp2.get_request()
  except AssertionError:
    # This only happens in unit tests, when the code gets called outside of
    # a request.
    return False
  if not request or (
      hasattr(request, 'path') and request.path.startswith('/mapreduce')):
    # Running a mapreduce.
    return True
  if request.registry.get('privileged', False):
    return True
  if hasattr(request, 'remote_addr'):
    return check_whitelisted_ip.CheckWhiteListedIp(request.remote_addr)
  return False


def IsUnalteredQueryPermitted():
  """Checks if the current user is internal, or the request is privileged.

  Google users are assumed to be internal; privileged requests allow for task
  queue tasks like find_anomalies to work correctly.

  Returns:
    True for users with google.com emails and privileged requests.
  """
  if request_handler.IsLoggedInWithGoogleAccount():
    return True
  if users.is_current_user_admin():
    # It's only possible to be an admin with a non-google.com account on a dev
    # box. But the default login on dev boxes is test@example.com, so it's
    # confusing when people run locally and can't see their data.
    return True
  return _IsServicingPrivilegedRequest()


def GetNamespace():
  if IsUnalteredQueryPermitted():
    return 'internal_only'
  return 'externally_visible'


def _DatastorePreHook(service, call, request, unused_response):
  """Adds a filter which checks whether to return internal data for queries.

  If the user is not privileged, we don't want to return any entities that
  have internal_only set to True. That is done here in a datastore hook.
  See: https://developers.google.com/appengine/articles/hooks

  Args:
    service: Service name, must be 'datastore_v3'.
    call: String representing function to call. One of 'Put', Get', 'Delete',
        or 'RunQuery'.
    request: Request protobuf.
    unused_response: Response protobuf (not used).
  """
  assert service == 'datastore_v3'
  if call != 'RunQuery':
    return
  if request.kind() not in _INTERNAL_ONLY_KINDS:
    return
  if IsUnalteredQueryPermitted():
    return

  # Queries should always check "internal_only = False" since the user is
  # external.
  try:
    # Production and unit tests use proto2
    external_filter = request.filter_list().add()
  except AttributeError:
    # The app.sh framework uses dev_appserver_internal_main, which uses the old
    # dev_appserver, which uses proto1. This should go away when it switches to
    # devappserver2_internal_main, which is tracked in http://b/8449518
    external_filter = request.add_filter()
  external_filter.set_op(datastore_pb.Query_Filter.EQUAL)
  new_property = external_filter.add_property()
  new_property.set_name('internal_only')
  new_property.mutable_value().set_booleanvalue(False)
  new_property.set_multiple(False)
