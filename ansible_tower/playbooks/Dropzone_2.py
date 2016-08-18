import phantom.rules as phantom
import json
#
#      Copyright (c) 2016 World Wide Technology, Inc.
#      All rights reserved.
#
#      author: Joel W. King,  World Wide Technology
#
def on_start(container):
    
    # call 'run_job_1' block
    run_job_1(container)

    return

def run_job_1(container, filtered_artifacts=None, filtered_results=None):
    phantom.debug('container passed is: '+json.dumps(container))
    # collect data for 'run_job_1' call
    container_data = phantom.collect2(container=container, datapath=['artifact:*.cef.sourceAddress', 'artifact:*.id'])

    parameters = []
    
    # build parameters list for 'run_job_1' call
    for container_item in container_data:
        parameters.append({
            'dead interval': "10",
            'extra vars':  "name=dropzone_%s,dstIp=%s,fvTenant=mediaWIKI,ap=test_mediaWIKI,epg=Outside,srcPort=https,prot=tcp" % (container_item[0], container_item[0]),
            'job template id': "32",
            # context (artifact id) is added for action results to be associated with the artifact
            'context':{'artifact_id': container_item[1]},
        })

    if parameters:
        phantom.act("run job", parameters=parameters, assets=['ansible_tower'], name="run_job_1")    
    
    return

def on_finish(container, summary):

    # This function is called after all actions are completed.
    # Summary and/or action results can be collected here.

    # summary_json = phantom.get_summary()
    # summary_results = summary_json['result']
    # for result in summary_results:
            # action_run_id = result['id']
            # action_results = phantom.get_action_results(action_run_id=action_run_id)

    return