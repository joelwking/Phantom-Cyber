import phantom.rules as phantom
import json
#
#      F5 firewall 
#
#      Copyright (c) 2016 World Wide Technology, Inc. 
#      All rights reserved. 
#
#      author: Joel W. King,  World Wide Technology
#
#
def block_IP_cb(action, success, container, results, handle):

    if not success:
        return
    
    return


def on_start(container):
 
    ips = set(phantom.collect(container, 'artifact:*.cef.sourceAddress'))

    boiler_plate = { "action" : "reject",  "policy" : "Phantom_Inbound",  "rule name" : "Phantom_DYNAMIC_BLOCK",  "partition" : "Common"}

    for ip in ips:
        
        parameters = boiler_plate
        parameters["source"] = ip
        phantom.debug("PARAMETERS \n%s" % parameters)
        phantom.act('block ip', parameters=[parameters], assets=["f5"], callback=block_IP_cb)

    return

def on_finish(container, summary):

    phantom.debug("Summary: " + summary)

    return

