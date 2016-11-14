#
"""
     Copyright (c) 2016 World Wide Technology, Inc.
     All rights reserved.

     Revision history:
     8 November 2016  |  1.0 Initial release. 

     module: A10_LADS_Connector.py
     author: Joel W. King, World Wide Technology
     short_description: Class to manage the connection to A10 Lightning Application Delivery Controller (LADC) Cloud

"""
#
#  system imports
#
import json
import time
import requests
import httplib

# ========================================================
# AppConnector
# ========================================================

class A10_LADS_Connector(object):

    BANNER = "A10_LADS"
    APP_ERROR = 0
    APP_SUCCESS = 1


    def __init__(self, dashboard="api.a10networks.com"):
        """
        Instance variables
        """
        self.HEADER = {"provider": None, "tenant": None, "Content-Type": "application/json"}
        self.status_codes = []
        self.progress = []                 
        self.app_run_status = Connector.APP_SUCCESS

        # Configuration variables

        self.configuration = dict()
        self.configuration["username"] = API_key
        self.configuration["dashboard"] = dashboard
        self.configuration["provider"] = "root"
        self.configuration["tenant"] = "WWT-Joel-King"

        # Parameters

        self.param = dict()
        self.param[""]
        

        try:
            requests.packages.urllib3.disable_warnings()
        except AttributeError:
            # Older versions of Requests do not support 'disable_warnings'
            pass
        

    def debug_print(self, message):
        "Not implemented"
        return None

    def set_status_save_progress(self, status, message):
        "Set status and append to the progress message, for debugging"
        self.app_run_status = status
        self.progress.append(message)
        return

    def get_configuration(self, requested_key):
        "Return requested key or None if the key does not exist."
        try:
            return self.configuration[requested_key]
        except:
            return None

    def set_parameters(self, **kwargs):
        " If the parameters is an empty dictionary, use the default values."
        for key, value in kwargs.items():
           self.param[key] = value

        self.debug_print("%s SET_PARAMETERS parameters:\n%s" % (Connector.BANNER, self.param))
        return


    def query_api(self, URL):
        """
        Method to query and return results, return an empty list if there are connection error(s).
        """

        URI = "https://" + self.get_configuration("dashboard") + URL
        try:
            r = requests.get(URI, headers=self.HEADER, verify=False)
        except requests.ConnectionError as e:
            self.set_status_save_progress(Connector.APP_ERROR, str(e))
            return []
        self.status_codes.append(r.status_code)

        try:
            return r.json()
        except ValueError:                                 # If you get a 404 error, throws a ValueError exception
            return []

