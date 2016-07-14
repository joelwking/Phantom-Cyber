#!/usr/bin/env python
"""
     Copyright (c) 2016 World Wide Technology, Inc.
     All rights reserved.

     Revision history:
     16 May   2016  |  1.0 - initial release
     21 June  2016  |  1.1 - Changes for discussion with Naasief on BGP Remote Trigger Black Hole
     14 July  2017  |  1.2 - migrated unit test code into Phantom format

     module: ansible_tower_connector.py
     author: Joel W. King, World Wide Technology
     short_description: This Phantom app launches a job template in Ansible Tower
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
import time
import json
import httplib
import requests
requests.packages.urllib3.disable_warnings()

try:
    from ansible_tower_connector_consts import *
except:
    pass                                                   # File ./ansible_tower_connector_consts.py is optional

# ---------------------------------------------------------------------------
# Ansible Tower Connection Class
# ---------------------------------------------------------------------------


class Tower_Connector(BaseConnector):
    """
      Connection class for Python to Ansible Tower REST Calls
    """
    BANNER = "ANSIBLE_TOWER"
    ACTIVE_JOB_STATES = ("running", "waiting", "pending")
    SLEEP_TIME = 10

    def __init__(self):
        """
        Instance variables
        """
        # Call the BaseConnectors init first
        super(Tower_Connector, self).__init__()

        self.HEADER = {"Content-Type": "application/json"}
        self.token = None
        self.tower_instance = '192.0.2.1'
        self.alive = 300
        self.username = None
        self.password = None
        self.job_id = None

    def initialize(self):
        """
        This is an optional function that can be implemented by the AppConnector derived class. Since the configuration
        dictionary is already validated by the time this function is called, it's a good place to do any extra initialization
        of any internal modules. This function MUST return a value of either phantom.APP_SUCCESS or phantom.APP_ERROR.
        If this function returns phantom.APP_ERROR, then AppConnector::handle_action will not get called.
        """
        self.debug_print("%s INITIALIZE %s" % (Tower_Connector.BANNER, time.asctime()))
        # Populate the class instance variables with configuration data, get_config returns a dictionary
        config = self.get_config()
        self.tower_instance = config.get("tower_instance")
        self.username = config.get("username")
        self.password = config.get("password")
        return phantom.APP_SUCCESS

    def finalize(self):
        """
        This function gets called once all the param dictionary elements are looped over and no more handle_action calls
        are left to be made. It gives the AppConnector a chance to loop through all the results that were accumulated by
        multiple handle_action function calls and create any summary if required. Another usage is cleanup, disconnect
        from remote devices etc.
        """
        self.debug_print("%s FINALIZE Status: %s" % (Tower_Connector.BANNER, self.get_status()))
        return

    def handle_exception(self, exception_object):
        """
        All the code within BaseConnector::_handle_action is within a 'try: except:' clause. Thus if an exception occurs
        during the execution of this code it is caught at a single place. The resulting exception object is passed to the
        AppConnector::handle_exception() to do any cleanup of it's own if required. This exception is then added to the
        connector run result and passed back to spawn, which gets displayed in the Phantom UI.
        """
        self.debug_print("%s HANDLE_EXCEPTION %s" % (Tower_Connector.BANNER, exception_object))
        return

    def aaaLogin(self):
        """
        Logon the controller, need to pass the userid and password, and in return we get a token.
        """

        URL = "https://%s/api/v1/authtoken/" % self.tower_instance
        DATA = {"username": self.username, "password": self.password}
        try:
            r = requests.post(URL, data=json.dumps(DATA), headers=self.HEADER, verify=False)
        except requests.ConnectionError as e:
            return str(e)
        else:
            try:
                self.token = r.json()["token"]
            except KeyError:
                self.token = None
            return r.status_code

    def _test_connectivity(self, param):
        """
        Called when the user depresses the test connectivity button on the Phantom UI.
        """
        self.debug_print("%s TEST_CONNECTIVITY %s" % (Tower_Connector.BANNER, param))

        status_code = self.aaaLogin()
        msg = "Test connectivity to %s, status_code: %s %s" % (self.tower_instance, status_code, httplib.responses[status_code])

        if status_code == requests.codes.ok:             # evaluates True for good status (e.g. 200)
            return self.set_status_save_progress(phantom.APP_SUCCESS, msg)
        else:
            return self.set_status_save_progress(phantom.APP_ERROR, msg)

    def query_api(self, URL):
        """
        Method to query and return results as a dictionary, return an empty dictionary if there are connection error(s).
        """
        header = self.HEADER
        header["Authorization"] = "Token %s" % self.token
        URI = "https://" + self.tower_instance + URL
        try:
            r = requests.get(URI, headers=header, verify=False)
        except requests.ConnectionError as e:
            self.set_status_save_progress(phantom.APP_ERROR, str(e))
            return dict()

        self.send_progress("query_api: %s" % r.status_code)
        try:
            return r.json()
        except ValueError:                                 # If you get a 404 error, throws a ValueError exception
            return dict()
        return dict()

    def get_job_template_id(self, job_to_run, jobs):
        "User specified the job name, we need to get the corresponding job template id"

        for job in jobs:
            print "get_jobid: %s %s" % (job["name"], job["id"])
            if job["name"] == job_to_run:
                return job["id"]
        return None

    def launch_job(self, param, job_template_id):
        """launch the job specified by its job_template_id

        """
        self.debug_print("%s LOCATE_DEVICE parameters:\n%s" % (Tower_Connector.BANNER, param))

        action_result = ActionResult(dict(param))          # Add an action result to the App Run
        self.add_action_result(action_result)

        URI = "https://%s/api/v1/job_templates/%s/launch/" % (self.tower_instance, job_template_id)
        header = self.HEADER
        header["Authorization"] = "Token %s" % self.token
        try:
            r = requests.post(URI, headers=header, verify=False)
        except requests.ConnectionError as e:
            self.set_status_save_progress(phantom.APP_ERROR, str(e))
            return "ConnectionError"

        if r.status_code is 202:                           # 202 'Accepted'
            self.job_id = r.json()['job']

        return httplib.responses[r.status_code]

    def wait_for_completion(self):
        "Check the status of the job and report ongoing status."

        while self.timer_ticking():
            job_stats = self.query_api("/api/v1/jobs/%s/" % self.job_id)
            try:
                if job_stats["status"] in Tower_Connector.ACTIVE_JOB_STATES:
                    self.send_progress("Job Status: %s" % job_stats["status"])
                else:
                    return job_stats
            except KeyError:
                self.set_status_save_progress(phantom.APP_ERROR, status_message="KeyError occured in wait_for_completion.")
                return None
        self.set_status_save_progress(phantom.APP_ERROR, status_message="Job did not complete within specified dead interval.")
        return None

    def timer_ticking(self):
        "Checks to make certain we don't query forever"
        if self.alive:
            time.sleep(Tower_Connector.SLEEP_TIME)
            self.alive -= 1
            return True
        return False

    def run_job(self, param):
        """ Optionally set the dead interval, logon, determine if the user specified a job template name or the numeric id.
            Launch the job template. If the job was accepted (202 status_code), wait up to the dead interval for the job to
            complete and report back the job id. This numeric job id is specified on the Jobs tab in Ansible Tower.
        """
        if param["dead interval"]:                         # optional, expecting None of not present
            self.alive = param["dead interval"]

        self.aaaLogin()
        if not self.token:
            pass                                           # token will be null if we failed to login

        # determine if supplied a numeric job or a string representing the job to run
        try:
            job_template_id = int(param["job template id"])
        except ValueError:
            # user specified a string, attempt to obtain the job_id from the text specified
            job_template_id = self.get_job_template_id(param["job template id"], self.query_api("/api/v1/job_templates/")["results"])

        # attempt to launch the job specified
        status = self.launch_job(param, job_template_id)
        if status is "Accepted":
            results = self.wait_for_completion()
            if results:
                msg = "job id: %s status: %s name: %s elapsed time: %s sec ended: %s" % (self.job_id, results["status"], results["name"], results["elapsed"], results["finished"])
                self.set_status(phantom.APP_SUCCESS, status_message=msg)
            else:
                # nothing to do here, results are None due to an error which has been reported
                pass
        else:
            self.set_status_save_progress(phantom.APP_ERROR, status_message="Job failed to launch: %s" % status)
        return

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
        self.debug_print("%s HANDLE_ACTION action_id:%s parameters:\n%s" % (Tower_Connector.BANNER, action_id, param))

        supported_actions = {"test connectivity": self._test_connectivity,
                             "run job": self.run_job}

        run_action = supported_actions[action_id]

        return run_action(param)

# ===================================================================================================
# Logic for testing interactively e.g. python2.7 ./ansible_tower_connector.py ./test_jsons/test.json
# If you don't reference your module with a "./" you will encounter a 'failed to load app json'
# ===================================================================================================

if __name__ == '__main__':

    import sys

    if (len(sys.argv) < 2):
        print "No test json specified as input"
        exit(0)

    with open(sys.argv[1]) as f:                           # input a json file that contains data like the configuration and action parameters,
        in_json = f.read()
        in_json = json.loads(in_json)
        print ("%s %s" % (sys.argv[1], json.dumps(in_json, indent=4)))

        connector = Tower_Connector()
        connector.print_progress_message = True
        ret_val = connector._handle_action(json.dumps(in_json), None)
        print ("%s %s" % (connector.BANNER, json.dumps(json.loads(ret_val), indent=4)))

    exit(0)
