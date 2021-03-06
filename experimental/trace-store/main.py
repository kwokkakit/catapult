# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import sys
import webapp2
import uuid

import trace_info

sys.path.append('third_party')
import cloudstorage as gcs

from google.appengine.api import app_identity

default_retry_params = gcs.RetryParams(initial_delay=0.2,
                                       max_delay=5.0,
                                       backoff_factor=2,
                                       max_retry_period=15)
gcs.set_default_retry_params(default_retry_params)


class UploadPage(webapp2.RequestHandler):
  def post(self):
    trace_uuid = str(uuid.uuid4())
    bucket_name = ('/' + app_identity.get_default_gcs_bucket_name() + '/' +
                   trace_uuid)
    gcs_file = gcs.open(bucket_name,
                        'w',
                        content_type='application/octet-stream',
                        options={},
                        retry_params=default_retry_params)
    gcs_file.write(self.request.get('trace'))
    gcs_file.close()

    trace_object = trace_info.TraceInfo(id=trace_uuid)
    trace_object.prod = self.request.get('prod')
    trace_object.ver = self.request.get('product_version')
    trace_object.remote_addr = os.environ["REMOTE_ADDR"]
    trace_object.put()


class MainPage(webapp2.RequestHandler):
  def get(self):
    self.response.out.write("""
          <form action="/upload" enctype="multipart/form-data" method="post">
            <div><input type="file" name="trace"/></div>
            <div><input type="submit" value="Upload"></div>
          </form>
          <hr>
        </body>
      </html>""")

app = webapp2.WSGIApplication([('/', MainPage), ('/upload', UploadPage)])
