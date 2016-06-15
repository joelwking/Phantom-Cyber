#
"""
     Copyright (c) 2016 World Wide Technology, Inc.
     All rights reserved.

     Revision history:
     21 April 2016  |  1.0 - initial release
     28 April 2016  |  1.1 - added __init__
     29 April 2016  |  1.2 - tested connectivity successfully from UI
     4  May   2016  |  1.3 - Running under UI with output
     5  May   2016  |  1.4 - Added output formatting and search string logic
     12 June  2016  |  1.5 - Documentation
     15 June  2016  |  1.6 - W292 no newline at end of file and W291 trailing whitespace

     module: meraki_connector.py
     author: Joel W. King, World Wide Technology
     short_description: This Phantom app connects to the Cisco Meraki cloud managment platform

"""
#
# Phantom App imports
#
import phantom.app as phantom
from phantom.base_connector import BaseConnector
from phantom.action_result import ActionResult
#
#  system imports
#
import simplejson as json
import time
import requests
import httplib

from meraki_connector_consts import *                  # file name would be ./meraki_connector_consts.py

# ========================================================
# AppConnector
# ========================================================


class Meraki_Connector(BaseConnector):

    BANNER = "MERAKI"

    def __init__(self):
        """
        Instance variables
        """
        # Call the BaseConnectors init first
        super(Meraki_Connector, self).__init__()

        self.HEADER = {"Content-Type": "application/json"}
        self.status_code = []

    def initialize(self):
        """
        This is an optional function that can be implemented by the AppConnector derived class. Since the configuration
        dictionary is already validated by the time this function is called, it's a good place to do any extra initialization
        of any internal modules. This function MUST return a value of either phantom.APP_SUCCESS or phantom.APP_ERROR.
        If this function returns phantom.APP_ERROR, then AppConnector::handle_action will not get called.
        """
        self.debug_print("%s INITIALIZE %s" % (Meraki_Connector.BANNER, time.asctime()))
        return phantom.APP_SUCCESS

    def finalize(self):
        """
        This function gets called once all the param dictionary elements are looped over and no more handle_action calls
        are left to be made. It gives the AppConnector a chance to loop through all the results that were accumulated by
        multiple handle_action function calls and create any summary if required. Another usage is cleanup, disconnect
        from remote devices etc.
        """
        self.debug_print("%s FINALIZE Status: %s" % (Meraki_Connector.BANNER, self.get_status()))
        return

    def handle_exception(self, exception_object):
        """
        All the code within BaseConnector::_handle_action is within a 'try: except:' clause. Thus if an exception occurs
        during the execution of this code it is caught at a single place. The resulting exception object is passed to the
        AppConnector::handle_exception() to do any cleanup of it's own if required. This exception is then added to the
        connector run result and passed back to spawn, which gets displayed in the Phantom UI.
        """
        self.debug_print("%s HANDLE_EXCEPTION %s" % (Meraki_Connector.BANNER, exception_object))
        return

    def get_configuration(self, key):
        """
        Return the API Key and dashboard hostname. As these are mandatory configuration keys, assume keys are populated
        The user can override the default dashboard.meraki.com
        """
        config = self.get_config()

        if key == "dashboard":
            if config.get("dashboard"):
                return config.get("dashboard")
            else:
                return DASHBOARD

        return config.get(key)

    def _test_connectivity(self, param):
        """
        Called when the user depresses the test connectivity button on the Phantom UI.
        Use a basic query of your organizations to determine if the authentication token is correct

        Meraki will send back a 3xx Redirect when you hit the first API. The requests module will
        handle the redirect for you, but it would be nice to know the actual server processing your
        request, so I will output the URL in the message.

            curl -k  -H "X-Cisco-Meraki-API-Key: redacted"
                -X GET -H "Content-Type: application/json" https://dashboard.meraki.com/api/v0/organizations

        """
        self.debug_print("%s TEST_CONNECTIVITY %s" % (Meraki_Connector.BANNER, param))

        header = self.HEADER
        header["X-Cisco-Meraki-API-Key"] = self.get_configuration("Meraki-API-Key")
        URI = "https://" + self.get_configuration("dashboard") + "/api/v0/organizations"

        try:
            r = requests.get(URI, headers=header, verify=False)
        except requests.ConnectionError as e:
            return self.set_status_save_progress(phantom.APP_ERROR, str(e))

        organizations = ""                                 # It is possible to have multiple organizations per user account
        try:                                               # It is the API Key which determines the orgs this admin owns.
            response = r.json()                            # r.json() provides the results of r.content as a list rather than string
        except ValueError:                                 # If you get a 404 error, throws a ValueError exception
            response = []

        for item in response:
            try:
                organizations += "%s, %s" % (item['id'], item["name"])
            except KeyError:
                return self.set_status_save_progress(phantom.APP_ERROR, "KeyError attempting to parse organization ID and name")

        msg = "Test connectivity to %s, organization(s) %s, status_code: %s %s" % (r.url, organizations, r.status_code, httplib.responses[r.status_code])

        if r.status_code == requests.codes.ok:             # evaluates True for good status (e.g. 200)
            return self.set_status_save_progress(phantom.APP_SUCCESS, msg)
        else:
            return self.set_status_save_progress(phantom.APP_ERROR, msg)

    def locate_device(self, param):
        """
        Locating client devices means walking a tree based on the API Key. The key is associated with one or more organizations,
        an organization can have one or more networks, each network can have multiple devices, and each device can have one or
        more client machines. Depending on the timespan specified, you may see differing results. Larger timespans may show the same
        client connected to multiple devices. Small timespans, may not return any results.
        """
        self.debug_print("%s LOCATE_DEVICE parameters:\n%s" % (Meraki_Connector.BANNER, param))

        action_result = ActionResult(dict(param))          # Add an action result to the App Run
        self.add_action_result(action_result)

        try:
            param["search_string"]                         # User left search_string empty
        except KeyError:
            param["search_string"] = "*"

        org_id_list = self.get_org_ids()
        for organization in org_id_list:
            networks_list = self.get_networks(organization["id"])
            for network in networks_list:
                device_list = self.get_devices(network["id"])
                for device in device_list:
                    client_list = self.get_clients(device["serial"], param["timespan"])
                    for client in client_list:
                        response = self.build_output_record(param["search_string"], organization, network, device, client)
                        if response:
                            action_result.add_data(response)

        if action_result.get_data_size() > 0:
            action_result.set_status(phantom.APP_SUCCESS)
            self.set_status_save_progress(phantom.APP_SUCCESS, "Returned: %s clients" % action_result.get_data_size())
        else:
            action_result.set_status(phantom.APP_ERROR)
            self.set_status_save_progress(phantom.APP_ERROR, "Returned: %s clients" % action_result.get_data_size())

        self.debug_print("%s Data size: %s" % (Meraki_Connector.BANNER, action_result.get_data_size()))
        return action_result.get_status()

    def build_output_record(self, search_string, organization, network, device, client):
        """
        Match the search string against the client MAC and description, if there is a match return a dictionary to add to
        the Action Result data field. A search string of "*" means to return everything.
        """

        self.debug_print("%s BUILD_OUTPUT_RECORD for: %s %s %s" % (Meraki_Connector.BANNER, device["serial"], client['description'], client['mac']))

        if client['description'] is None:                  # Description could be NoneType
            client['description'] = ""

        if search_string == "*" or search_string in client['description'] or search_string in client['mac']:
            return {'client': {'mac': client['mac'], 'description': client['description']},
                'device': device['name'], 'network': network['name'], 'organization': organization['name']}
        return None

    def get_org_ids(self):
        """
        Return a list of organization IDs for this account
        URI = "https://dashboard.meraki.com/api/v0/organizations"
        return [{"id":530205,"name":"WWT"}]
        """
        return self.query_api("/api/v0/organizations")

    def get_networks(self, organization_id):
        """
        Return a list of network IDs for this organization
        URI = "https://dashboard.meraki.com/api/v0/organizations/530205/networks"
        return [{u'id': u'L_629378047925028460', u'name': u'SWISSWOOD', u'organizationId': u'530205', u'tags': u'',
                 u'timeZone': u'America/New_York',  u'type': u'combined'}]
        """
        return self.query_api("/api/v0/organizations/" + str(organization_id) + "/networks")

    def get_devices(self, network_id):
        """
        Return a list of devices in this network
        URI = "https://dashboard.meraki.com/api/v0/networks/L_629378047925028460/devices"
        return [{u'address': u'swisswood dr, Denton, NC 16713', u'lat': 34.9543899, u'lng': -77.721312,
                 u'mac': u'88:15:44:08:ad:08',  u'model': u'MX64',  u'name': u'SWISSWOOD-MX64', u'serial': u'Q2KN-R9P3-3U6X',
                 u'tags': u' recently-added ', u'wan1Ip': u'192.168.0.3', u'wan2Ip': None}]
        """
        return self.query_api("/api/v0/networks/" + network_id + "/devices")

    def get_clients(self, serial, timespan):
        """
        Return a list of clients associated with this device serial number.
        URI = "https://dashboard.meraki.com/api/v0/devices/Q2HP-NAY7-A2WH/clients?timespan=86400"
        return [{u'description': u'alpha_b-THINK-7', u'dhcpHostname': u'alpha_b-THINK-7', u'id': u'k7c0271',
                 u'mac': u'60:6c:77:01:22:42',
                 u'mdnsName': None, u'switchport': u'3', u'usage': {u'recv': 14168.0, u'sent': 124917.00000000001}}]
        """
        if timespan > 2592000:
            timespan = 2592000
        timespan = str(timespan)
        return self.query_api("/api/v0/devices/" + serial + "/clients?timespan=" + timespan)

    def query_api(self, URL):
        """
        Method to query and return results, return an empty list if there are connection error(s).
        """
        header = self.HEADER
        header["X-Cisco-Meraki-API-Key"] = self.get_configuration("Meraki-API-Key")
        URI = "https://" + self.get_configuration("dashboard") + URL
        try:
            r = requests.get(URI, headers=header, verify=False)
        except requests.ConnectionError as e:
            self.set_status_save_progress(phantom.APP_ERROR, str(e))
            return []
        self.status_code.append(r.status_code)

        try:
            return r.json()
        except ValueError:                                 # If you get a 404 error, throws a ValueError exception
            return []

    def handle_action(self, param):
        """
        This function implements the main functionality of the AppConnector. It gets called for every param dictionary element
        in the parameters array. In it's simplest form it gets the current action identifier and then calls a member function
        of it's own to handle the action. This function is expected to create the results of the action run that get added
        to the connector run. The return value of this function is mostly ignored by the BaseConnector. Instead it will
        just loop over the next param element in the parameters array and call handle_action again.

        We create a case structure in Python to allow for any number of actions to be easily added.
        """

        action_id = self.get_action_identifier()           # action_id determines what function to execute
        self.debug_print("%s HANDLE_ACTION action_id:%s parameters:\n%s" % (Meraki_Connector.BANNER, action_id, param))

        supported_actions = {"test connectivity": self._test_connectivity,
                            "locate device": self.locate_device}

        run_action = supported_actions[action_id]

        return run_action(param)


# =============================================================================================
# Logic for testing interactively e.g. python2.7 ./meraki_connector.py ./test_jsons/test.json
# If you don't reference your module with a "./" you will encounter a 'failed to load app json'
# =============================================================================================

if __name__ == '__main__':

    import sys

    if (len(sys.argv) < 2):
        print "No test json specified as input"
        exit(0)

    with open(sys.argv[1]) as f:                           # input a json file that contains data like the configuration and action parameters,
        in_json = f.read()
        in_json = json.loads(in_json)
        print ("%s %s" % (sys.argv[1], json.dumps(in_json, indent=4)))

        connector = Meraki_Connector()
        connector.print_progress_message = True
        ret_val = connector._handle_action(json.dumps(in_json), None)
        print ("%s %s" % (connector.BANNER, json.dumps(json.loads(ret_val), indent=4)))

    exit(0)
