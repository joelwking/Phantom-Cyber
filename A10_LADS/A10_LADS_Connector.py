#
"""
     Copyright (c) 2016 World Wide Technology, Inc.
     All rights reserved.

     Revision history:
     28 November 2016  |  1.0 - initial release

     module: A10_LADS_Connector.py
     author: Joel W. King, World Wide Technology
     short_description: "This app supports containment actions like 'block ip' or 'unblock ip' using the A10 Lightning Application Delivery System (LADS).

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
import httplib
#
#  application imports
#
import A10_LADS_REST_interface as a10

# ========================================================
# AppConnector
# ========================================================


class A10_LADS_Connector(BaseConnector):
    "AppConnector"

    BANNER = "A10_LADS"
    DASHBOARD = "api.a10networks.com"

    def initialize(self):
        """
        This is an optional function that can be implemented by the AppConnector derived class. Since the configuration
        dictionary is already validated by the time this function is called, it's a good place to do any extra initialization
        of any internal modules. This function MUST return a value of either phantom.APP_SUCCESS or phantom.APP_ERROR.
        If this function returns phantom.APP_ERROR, then AppConnector::handle_action will not get called.
        """
        self.debug_print("%s INITIALIZE %s" % (A10_LADS_Connector.BANNER, time.asctime()))
        return phantom.APP_SUCCESS

    def finalize(self):
        """
        This function gets called once all the param dictionary elements are looped over and no more handle_action calls
        are left to be made. It gives the AppConnector a chance to loop through all the results that were accumulated by
        multiple handle_action function calls and create any summary if required. Another usage is cleanup, disconnect
        from remote devices etc.
        """
        self.debug_print("%s FINALIZE" % A10_LADS_Connector.BANNER)
        return

    def handle_exception(self, exception_object):
        """
        All the code within BaseConnector::_handle_action is within a 'try: except:' clause. Thus if an exception occurs
        during the execution of this code it is caught at a single place. The resulting exception object is passed to the
        AppConnector::handle_exception() to do any cleanup of it's own if required. This exception is then added to the
        connector run result and passed back to spawn, which gets displayed in the Phantom UI.
        """
        self.debug_print("%s HANDLE_EXCEPTION %s" % (A10_LADS_Connector.BANNER, exception_object))
        return

    def get_cfg(self, key):
        """
        Logic to handle optional parameters, like the dashboard name.
        """
        config = self.get_config()

        if key == "dashboard":
            if config.get("dashboard"):
                return config.get("dashboard")
            else:
                return A10_LADS_Connector.DASHBOARD

        return config.get(key)

    def normalize_ip(self, ipaddress):
        "Include netmask of /32 if no mask exists"
        if "/" not in ipaddress:
            ipaddress += "/32"
        return ipaddress

    def _test_connectivity(self, param, LADS):
        """
        Called when the user depresses the test connectivity button on the Phantom UI.
        This query returns a list of configured applications
            https://api.a10networks.com/api/v2/applications
        """
        self.debug_print("%s _test_connectivity %s" % (A10_LADS_Connector.BANNER, param))

        msg = "test connectivity to %s status_code: " % (LADS.dashboard)

        if LADS.genericGET(uri="/api/v2/applications"):
            # True is success
            return self.set_status_save_progress(phantom.APP_SUCCESS, msg + "%s %s apps: %s" %
                   (LADS.status_code, httplib.responses[LADS.status_code], LADS.get_names(LADS.response)))
        else:
            # None or False, is a failure based on incorrect IP address, username, passords
            return self.set_status_save_progress(phantom.APP_ERROR, msg + "%s %s" % (LADS.status_code, LADS.response))

    def handle_action(self, param):
        """
        This function implements the main functionality of the AppConnector. It gets called for every param dictionary element
        in the parameters array. In it's simplest form it gets the current action identifier and then calls a member function
        of it's own to handle the action. This function is expected to create the results of the action run that get added
        to the connector run. The return value of this function is mostly ignored by the BaseConnector. Instead it will
        just loop over the next param element in the parameters array and call handle_action again.

        We create a case structure in Python to allow for any number of actions to be easily added.
        """

        config = self.get_config()
        action_id = self.get_action_identifier()           # action_id determines what function to execute
        self.debug_print("%s handle_action action_id:%s parameters:\n%s config:\n%s" % (A10_LADS_Connector.BANNER, action_id, param, config))

        LADS = a10.Lightning(dashboard=self.get_cfg("dashboard"),
                             username=self.get_cfg("username"),
                             password=self.get_cfg("password"),
                             provider=self.get_cfg("provider"),
                             tenant=self.get_cfg("tenant"))

        supported_actions = {"test connectivity": self._test_connectivity,
                            "block ip": self.block_ip,
                            "unblock ip": self.unblock_ip}

        run_action = supported_actions[action_id]

        return run_action(param, LADS)

    def unblock_ip(self, param, LADS):
        "Delete the rule which originally blocked the source IP address or network"

        self.debug_print("%s unblock_ip parameters:\n%s " % (A10_LADS_Connector.BANNER, param))
        self.modify_smartflow_policy(param, LADS, 'delete')
        return

    def block_ip(self, param, LADS):
        " Block a source IP address or network "

        self.debug_print("%s block_ip parameters:\n%s " % (A10_LADS_Connector.BANNER, param))
        self.modify_smartflow_policy(param, LADS, 'add')
        return

    def modify_smartflow_policy(self, param, LADS, CRUD):
        " Modify the Smartflow Policy "

        action_result = ActionResult(dict(param))          # Add an action result to the App Run
        self.add_action_result(action_result)

        source_ip = self.normalize_ip(param["source"])     # 8.8.8.8/32 or 192.0.2.0/24 or 4.4.4.4
        app_name = param["application"]                    # WWT-API
        host_name = param["host"]                          # default-host
        service_name = param["service"]                    # default-service
        smartflow_name = param["smartflow"]                # default-smartflow
        try:
            rule_action = param["action"]                  # 'deny' or 'allow', not specified for unblock
        except KeyError:
            rule_action = None

        uri = "/api/v2/applications/%s/hosts/%s/services/%s/smartflows/%s/policies" % (app_name, host_name, service_name, smartflow_name)

        if LADS.genericGET(uri=uri):                       # Successfully retrieved the Smartflow policy
            LADS.separate_access_policy(LADS.response)
            if LADS.modify_access_policy(CRUD, rule_action, source_ip):
                LADS.include_access_policy()
                uri += "/_import"
                if LADS.genericPOST(uri=uri, body=json.dumps(LADS.smartflow_policies)):
                    action_result.set_status(phantom.APP_SUCCESS)
                else:
                    action_result.set_status(phantom.APP_ERROR)
            else:
                action_result.set_status(phantom.APP_ERROR)   # Failure in modifying access policy
        else:
            action_result.set_status(phantom.APP_ERROR)   # Failed to retrieve Smartflow policy

        action_result.add_data(LADS.response)
        self.debug_print("%s modify_smartflow_policy code: %s \nresponse: %s" % (A10_LADS_Connector.BANNER, LADS.status_code, LADS.response))
        return


# ==========================================================================================
# Logic for testing interactively e.g. python2.7 ./A10_LADS_Connector.py ./test_jsons/reject.json
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

        connector = A10_LADS_Connector()
        connector.print_progress_message = True
        ret_val = connector._handle_action(json.dumps(in_json), None)
        print ("%s %s" % (connector.BANNER, json.dumps(json.loads(ret_val), indent=4)))

    exit(0)
