import phantom.rules as phantom
import json
#
#      Meraki sample playbook
#
#      Copyright (c) 2016 World Wide Technology, Inc. 
#      All rights reserved. 
#
#      author: Joel W. King,  World Wide Technology
#
#
def locate_device_cb(action, success, container, results, handle):
    
    if not success:
        return
        
    paths = ['action_result.data.*.client.mac', 
             'action_result.data.*.client.description',
             'action_result.data.*.device',
             'action_result.data.*.network',
             'action_result.data.*.organization']
               
    data = phantom.collect(results, paths)
    phantom.debug(data)
    return


def on_start(container):

    parameters = []
    parameters.append({
        "search_string": "d8:30:62:8f:33:b7",
        "timespan": "600",
    })

    phantom.act("locate device", parameters=parameters, assets=["meraki dashboard"], callback=locate_device_cb)

    return

def on_finish(container, summary):

    # This function is called after all actions are completed.
    # Summary and/or action results can be collected here.
    summary_json = phantom.get_summary()
    summary_results = summary_json['result']
    for result in summary_results:
        action_run_id = result['id']
        action_results = phantom.get_action_results(action_run_id=action_run_id)
    return
