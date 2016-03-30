#
"""
     Copyright (c) 2016 World Wide Technology, Inc.
     All rights reserved.

     Revision history:
     28 March 2016  |  1.0 - initial release
     29 March 2016  |  1.1 - comments and style modifications
     30 March 2016  |  1.2 - documentation update

     module: F5_connector.py
     author: Joel W. King, World Wide Technology
     short_description: This Phantom app supports containment actions like 'block ip' on an F5 BIG-IP appliance.

    remarks: The appdev tutorial is at  https://10.255.78.71/docs/appdev/tutorial

             ssh phantom@10.255.78.71
             export PYTHONPATH=/opt/phantom/lib/:/opt/phantom/www/
             export REQUESTS_CA_BUNDLE=/opt/phantom/etc/cacerts.pem
             cd ./app_dev/f5_firewall
             touch __init__.py
             ../compile_app.py -i

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
#
#  application imports
#
import icontrol_install_config as iControl                 # https://github.com/joelwking/ansible-f5/blob/master/icontrol_install_config.py
try:
    from F5_Connector_consts import *                      # file name would be ./F5_Connector_consts.py
except ImportError:
    pass                                                   # this is an optional file, used to bring in constants

# ========================================================
# AppConnector
# ========================================================


class F5_Connector(BaseConnector):
    " "
    BANNER = "F5"
    HEADER = {"Content-Type": "application/json"}

    def initialize(self):
        """
        This is an optional function that can be implemented by the AppConnector derived class. Since the configuration
        dictionary is already validated by the time this function is called, it's a good place to do any extra initialization
        of any internal modules. This function MUST return a value of either phantom.APP_SUCCESS or phantom.APP_ERROR.
        If this function returns phantom.APP_ERROR, then AppConnector::handle_action will not get called.
        """
        self.debug_print("%s INITIALIZE %s" % (self.BANNER, time.asctime()))
        return phantom.APP_SUCCESS

    def finalize(self):
        """
        This function gets called once all the param dictionary elements are looped over and no more handle_action calls
        are left to be made. It gives the AppConnector a chance to loop through all the results that were accumulated by
        multiple handle_action function calls and create any summary if required. Another usage is cleanup, disconnect
        from remote devices etc.
        """
        self.debug_print("%s FINALIZE" % self.BANNER)
        return

    def handle_exception(self, exception_object):
        """
        All the code within BaseConnector::_handle_action is within a 'try: except:' clause. Thus if an exception occurs
        during the execution of this code it is caught at a single place. The resulting exception object is passed to the
        AppConnector::handle_exception() to do any cleanup of it's own if required. This exception is then added to the
        connector run result and passed back to spawn, which gets displayed in the Phantom UI.
        """
        self.debug_print("%s HANDLE_EXCEPTION %s" % (self.BANNER, exception_object))
        return

    def _test_connectivity(self, param):
        """
        Called when the user depresses the test connectivity button on the Phantom UI.
        Use a basic query to determine if the IP address, username and password is correct,
            curl -k -u admin:redacted -X GET https://192.0.2.1/mgmt/tm/ltm/
        """
        self.debug_print("%s TEST_CONNECTIVITY %s" % (self.BANNER, param))

        config = self.get_config()
        username = config.get("username")
        password = self._normalize_password(config.get("password"))
        appliance = config.get("device")
        URI = "%s%s%s" % ("https://", appliance, "/mgmt/tm/ltm")

        try:
            r = requests.get(URI, auth=(username, password), headers=self.HEADER, verify=False)
        except requests.ConnectionError as e:
            return self.set_status_save_progress(phantom.APP_ERROR, str(e))

        msg = "test connectivity to %s status_code: %s %s" % (appliance, r.status_code, httplib.responses[r.status_code])

        if r.status_code == 200:
            return self.set_status_save_progress(phantom.APP_SUCCESS, msg)
        else:
            return self.set_status_save_progress(phantom.APP_ERROR, msg)

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
        self.debug_print("%s HANDLE_ACTION action_id:%s parameters:\n%s" % (self.BANNER, action_id, param))

        supported_actions = {"test connectivity": self._test_connectivity,
                            "block ip": self.block_ip}

        run_action = supported_actions[action_id]

        return run_action(param)

    def block_ip(self, param):
        """
        Block a source IP address,  a simple call to update a security policy in place.
        The firewall policy is called "Phantom_Inbound" which currently is tied to an inbound VIP in the "Common" partition.

        POST
        URL https://10.255.111.100/mgmt/tm/security/firewall/policy/~Common~Phantom_Inbound/rules
        body {"name":"DYNAMIC_BLOCK_NAME","action":"reject","place-after":"first","source":{"addresses":[{"name": "8.8.8.8/32"}"

        """
        config = self.get_config()
        self.debug_print("%s BLOCK_IP parameters:\n%s config:\n%s" % (self.BANNER, param, config))

        action_result = ActionResult(dict(param))          # Add an action result to the App Run
        self.add_action_result(action_result)

        URL = "/mgmt/tm/security/firewall/policy/~%s~%s/rules" % (param["partition"], param["policy"])
        body = '{"name":"%s","action":"%s","place-after":"first","source":{"addresses":[{"name":"%s/32"}]}}' \
               % (param["rule name"], param["action"], param["source"])

        self.debug_print("%s BLOCK_IP URL:\n%s body:\n%s" % (self.BANNER, URL, body))

        password = self._normalize_password(config.get("password"))
        F5 = iControl.Connection(host=config.get("device"), username=config.get("username"), password=password)

        uri, body = F5.standarize_body_url(URL, body)
        code, changed, response = iControl.install_config(F5, uri, body)
        self.debug_print("%s BLOCK_IP code:\n%s changed:\n%s response:\n%s" % (self.BANNER, code, changed, response))

        if code == 0:
           action_result.set_status(phantom.APP_SUCCESS)
        else:
            action_result.set_status(phantom.APP_ERROR)

        action_result.add_data(response)
        return

    def _normalize_password(self, password):
        """
        To prevent our passwords from showing on the screen in demos, we import the password of the asset
        from the optional constants file, and then if the password is 'redacted' we substitute the correct password
        If there is no global variable called REDACTED, then we assume the suplied password is what they want to use
        """

        if password.upper() == "REDACTED":
            try:
                type(REDACTED)
            except NameError:
                pass                                       # password might actually be the string 'redacted'
            else:
                password = REDACTED

        return password

# ==========================================================================================
# Logic for testing interactively e.g. python2.7 ./F5_connector.py ./test_jsons/reject.json
# ==========================================================================================

if __name__ == '__main__':

    import sys
    # import pudb                                          # executes a runtime breakpoint and brings up the pudb debugger.
    # pudb.set_trace()

    if (len(sys.argv) < 2):
        print "No test json specified as input"
        exit(0)

    with open(sys.argv[1]) as f:                           # input a json file that contains data like the configuration and action parameters,
        in_json = f.read()
        in_json = json.loads(in_json)
        print ("%s %s" % (sys.argv[1], json.dumps(in_json, indent=4)))

        connector = F5_Connector()
        connector.print_progress_message = True
        ret_val = connector._handle_action(json.dumps(in_json), None)
        print ("%s %s" % (connector.BANNER, json.dumps(json.loads(ret_val), indent=4)))

    exit(0)