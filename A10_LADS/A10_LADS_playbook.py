#
"""
     Copyright (c) 2016 World Wide Technology, Inc.
     All rights reserved.

     Revision history:
     28 November 2016  |  1.0 - initial release

     module: A10_LADS_playbook.py
     author: Joel W. King, World Wide Technology
     short_description: Sample playbook for the A10_LADS_Connector
"""
import phantom.rules as phantom
import json
from datetime import datetime, timedelta

def on_start(container):
    
    # call 'block_ip_1' block
    block_ip_1(container=container)

    return

def block_ip_1(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):

    # collect data for 'block_ip_1' call
    container_data = phantom.collect2(container=container, datapath=['artifact:*.cef.sourceAddress', 'artifact:*.id'])

    parameters = []
    
    # build parameters list for 'block_ip_1' call
    for container_item in container_data:
        if container_item[0]:
            parameters.append({
                'smartflow': "default-smartflow",
                'service': "default-service",
                'application': "WWT-API",
                'source': container_item[0],
                'host': "default-host",
                'action': "deny",
                # context (artifact id) is added to associate results with the artifact
                'context': {'artifact_id': container_item[1]},
            })

    if parameters:
        phantom.act("block ip", parameters=parameters, assets=['a10 lightning controller'], name="block_ip_1")    
    else:
        phantom.error("'block_ip_1' will not be executed due to lack of parameters")
    
    return

def on_finish(container, summary):

    # This function is called after all actions are completed.
    # summary of all the action and/or all detals of actions 
    # can be collected here.

    # summary_json = phantom.get_summary()
    # if 'result' in summary_json:
        # for action_result in summary_json['result']:
            # if 'action_run_id' in action_result:
                # action_results = phantom.get_action_results(action_run_id=action_result['action_run_id'], result_data=False, flatten=False)
                # phantom.debug(action_results)

    return