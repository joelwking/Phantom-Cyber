#!/usr/bin/env python
"""

   PhantomIngest.py 

   This is a modification to the sample REST API Ingest routing published in the 
   Phantom REST APIs https://127.0.0.1/docs/rest/overview documentation.
   It was modified to be imported as a python class for consumption.

   Copyright (c) 2016 World Wide Technology, Inc.
   All rights reserved.

   author: joel.king@wwt.com

   Revision history:
     5 August 2016  |  1.0 - initial release

"""

import sys, os
import time
import getpass
import requests
import json


class PhantomIngest(object):
    "Ingest data to Phantom via the REST API"

    def __init__(self, phantom_host, token):
        " The container and artifact common fields can be overridden by using kwargs when calling the method."

        requests.packages.urllib3.disable_warnings()
        self.headers = {"ph-auth-token": token}
        self.url =  "https://%s/rest" % phantom_host
        self.container_id = None
        self.content = None
        self.message = None

        self.container_common = {"description": "A brief useful description of the behavior tracked by this container",
                                 "name": "A short friendly name for the container",
                                 "label":"intelligence",
                                 "sensitivity": "red",
                                 "severity": "high",
                                 "tags": ['atomic_counters']
                                }

        self.artifact_common = {"description": "A textual description of the artifact",
                                "name": "A human friendly name for the artifact",
                                "tags": ['atomic_counters'],
                                "type": "network",
                                "source_data_identifier": "APIC_atomic_counters",
                                "label": "event"
                                }
 

    def add_container(self, **kwargs):
        """Containers are objects which document incidents, specify updates or additions to the
         JSON object in the data field through kwargs."""

        url = "%s/container" % self.url

        data = self.container_common.copy()
        for key, value in kwargs.items():                  # add or update container common fields
            data[key] = value

        try:        
            r = requests.post(url, data=json.dumps(data), headers=self.headers, verify=False)
        except requests.ConnectionError as e: 
            raise Exception, e

        self.store_requests_status(r)
        assert (r.status_code is requests.codes.ok), "Failure to communicate: %s" % r.status_code

        self.container_id = r.json().get('id')

        return self.container_id

    def add_artifact(self, container_id, cef, meta_data, **kwargs):
        "Artifacts provde supporting information for their container object"

        url = "%s/artifact" % self.url

        data = self.artifact_common.copy()
        for key, value in kwargs.items():                  # add or update artifact common fields
            data[key] = value

        data['cef'] = cef                                  # Common Event Format (CEF) fields
        data['data'] = meta_data                           # The "data" key can contain arbitrary json data.
        data['container_id'] = container_id

        try:
            r = requests.post(url, data=json.dumps(data), headers=self.headers, verify=False)
        except requests.ConnectionError as e: 
            raise Exception, e

        self.store_requests_status(r)
        assert (r.status_code is requests.codes.ok), "Failure to communicate: %s" % r.status_code

        self.artifact_id = r.json().get('id')              # '{"id": 24, "success": true}'
        
        return self.artifact_id

    def store_requests_status(self, response):
        "Store off the requests fields for consumption by the calling application."

        self.status_code = response.status_code
        self.content = response.content
        try:
            self.message = json.loads(response.text)['message']
        except KeyError:
            self.message = None

        return
