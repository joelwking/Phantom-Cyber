#
"""
     Copyright (c) 2016 World Wide Technology, Inc.
     All rights reserved.

     Revision history:
     8 November 2016  |  1.0 Initial release.

     module: A10_LADS_REST_interface.py
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


class Lightning(object):
    "Connection class for Python to A10 LADC REST calls"

    # tenant and provider values to be specified before invocation
    HEADER = {'Content-Type': 'application/json',
              'tenant': None,
              'provider': None}

    TRANSPORT = "https://"
    BANNER = "A10_LADC"
    VALID_GET_STATUS = (200,)
    VALID_POST_STATUS = (200,)
    ACCESS_POLICY_NAME = "access"
    ACTIVE = "active"
    VALID_RULE_ACTIONS = ("deny", "allow")

    def __init__(self, dashboard="api.a10networks.com", username="admin", password="redacted", provider=None, tenant=None):
        """
        Instance variables
        """
        self.HEADER = Lightning.HEADER
        self.HEADER["tenant"] = tenant
        self.HEADER["provider"] = provider
        self.dashboard = dashboard
        self.username = username
        self.password = password
        self.debug = False
        #  output from the last call to requests
        self.response = None
        self.status_code = None
        #  smartflow policies
        self.smartflow_policies = None
        self.access_policy = None

        try:
            requests.packages.urllib3.disable_warnings()
        except AttributeError:
            # Older versions of Requests do not support 'disable_warnings'
            pass

    def validate_uri(self, uri):
        " Make certain the uri has a leading and trailing slash"

        if uri[0] != "/":                                  # check leading slash
            uri = "/" + uri

        if uri[-1] != "/":                                 # check trailing slash
            uri = uri + "/"

        return uri

    def debug_print(self, message):
        "Check if debug enabled and print accordingly"
        if self.debug:
            print "\n%s" % message,
        return

    def set_header_parameters(self, **kwargs):
        " If the kwargs is an empty dictionary, use the default values."
        for key, value in kwargs.items():
           self.HEADER[key] = value

        self.debug_print("%s set_header_parameters: %s" % (Lightning.BANNER, self.HEADER))
        return

    def get_names(self, result):
        """ Input variable result is a list of dictionaries, we return the names found.
            One use case is a query for all applications, returning a list all application names.
        """
        name = []
        if isinstance(result, list):
            for item in result:
                try:
                    name.append(item["name"])
                except:
                    pass
        return name

    def reset_status(self):
        "Reset response, status codes"
        self.debug_print("%s reset_status:" % Lightning.BANNER)
        self.status_code = self.response = None
        return

    def genericGET(self, uri=None):
        " Issue a GET request, storing the results"

        self.debug_print("%s genericGET: %s" % (Lightning.BANNER, uri))
        self.reset_status()
        if not uri:
            return None

        URI = "%s%s%s" % (Lightning.TRANSPORT, self.dashboard, self.validate_uri(uri))
        try:
            r = requests.get(URI, auth=(self.username, self.password), headers=self.HEADER, verify=False)
        except requests.ConnectionError as e:
            self.status_code = 599
            self.response = str(e)
            return None
        self.status_code = r.status_code
        try:
            self.response = r.json()                       # r.json() returns a dictionary
        except ValueError:
            self.response = None

        if r.status_code in Lightning.VALID_GET_STATUS:
            return True
        return False

    def genericPOST(self, uri=None, body=None):
        "Issue a POST request, storing the results"

        self.debug_print("%s genericPUT: %s %s" % (Lightning.BANNER, uri, body))
        self.reset_status()
        if not (uri and body):
            return None

        URI = "%s%s%s" % (Lightning.TRANSPORT, self.dashboard, self.validate_uri(uri))
        try:
            r = requests.post(URI, auth=(self.username, self.password), data=body, headers=self.HEADER, verify=False)
        except requests.ConnectionError as e:
            self.status_code = 599
            self.response = str(e)
            return None
        self.status_code = r.status_code
        try:
            self.response = r.json()                       # r.json() returns a dictionary
        except ValueError:
            self.response = None

        if r.status_code in Lightning.VALID_POST_STATUS:
            return True
        return False

    def separate_access_policy(self, smartflow_policies):
        "The access policy is one policy in a list of policies. Segrate it from the list."

        self.debug_print("%s separate_access_policy: %s" % (Lightning.BANNER, smartflow_policies))

        self.smartflow_policies = self.access_policy = None

        for index, policy in enumerate(smartflow_policies):
            if policy['name'].lower() == Lightning.ACCESS_POLICY_NAME:
               self.access_policy = policy
               break

        if not self.access_policy:
            self.debug_print("%s separate_access_policy: NOT FOUND!" % Lightning.BANNER)
            return False

        if not self.access_policy['state'].lower() == Lightning.ACTIVE:
            self.debug_print("%s separate_access_policy: %s" % ("WARNING POLICY IS NOT ACTIVE!"))

        del smartflow_policies[index]                      # delete the access policy from the list
        self.smartflow_policies = smartflow_policies

        return True

    def modify_access_policy(self, CRUD, action, network):
        """Add, Update or Delete Policy
               "rules": [
                            {
                            "status": true,
                            "action": "deny",
                            "network": "192.0.2.1/24"
                            }
                        ],
               "id": "access"
        """

        found = False
        index = 0                                          # Set index in the event the list is empty
        for index, policy in enumerate(self.access_policy["rules"]):
            if network == policy["network"]:
                found = True
                break
        if CRUD.lower() == "delete":
            if found:
                del self.access_policy["rules"][index]
                return True
            else:
                return None                                # Asked to delete a rule which doesn't exist

        if action not in Lightning.VALID_RULE_ACTIONS:     # Invalid rule action
            return False

        if found:
            del self.access_policy["rules"][index]

        # Assume we are adding or updating
        self.access_policy["rules"].insert(index, dict(status=True, action=action, network=network))
        return True

    def include_access_policy(self):
        "Put the access policy back into the smartflow policy list"
        self.smartflow_policies.append(self.access_policy)
        return
