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
#      revisions:
#      16 June 2016  | Changes to parameters, create rule name base on the source IP
#
def block_IP_cb(action, success, container, results, handle):

    if not success:
        return
    
    return


def on_start(container):
 
    ips = set(phantom.collect(container, 'artifact:*.cef.sourceAddress'))

    boiler_plate = { "action" : "reject",  "policy" : None,  "rule name" : None,  "partition" : "Common"}

    for ip in ips:
        
        parameters = boiler_plate
        parameters["policy"] = "Phantom_Inbound"        # Policy name must exist on the F5 BIG-IP
        parameters["source"] = ip                       # Source IP we are blocking
        parameters["rule name"] = "Phantom" + ip        # Make the rule name based on the source IP address
        phantom.debug("PARAMETERS \n%s" % parameters)
        phantom.act('block ip', parameters=[parameters], assets=["f5"], callback=block_IP_cb)

    return

def on_finish(container, summary):

    phantom.debug("Summary: " + summary)

    return
