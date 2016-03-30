#!/usr/bin/env python
"""

Usage:

python meta_data_collection.py <phone_ip_address> <token> 

   Copyright (c) 2016 World Wide Technology, Inc.
   All rights reserved.

   author: joel.king@wwt.com

   Revision history:
     26 March 2016  |  1.0 - initial release

"""

import sys, os
import time
import getpass
import requests
import json
import xml.etree.ElementTree as ET



def main(phone_ip):
    """Get the metadata from the streaming statistics on the IP phone, 
       then create a container and artifact in Phantom
    """
    requests.packages.urllib3.disable_warnings()
    
    # Get the metadata off the IP Phone
    meta_data = format_meta_data(get_streaming_stats(phone_ip))

    if debug: print "main: %s meta_data %s" % (type(meta_data), meta_data)

    if type(meta_data) != dict:
    	print "Failed to retrieve meta data"
    	return

    if meta_data['StreamStatus'] != "Active":
    	print "Hey, you are not on a call, call someone who cares, like 202-762-1401"
    	return

    # Add a container to Phantom Cyber and add an artifact to the container
    container_id = add_container(meta_data['Name'], int(time.time()))
    if debug: print "main: container_id %s" % container_id

    if container_id:
        artifact_id = add_artifact(meta_data, container_id)
        print "Created container: %s and artifact: %s" % (container_id, artifact_id)
    else:
    	print "Failed to create container"

	return



def get_streaming_stats(phone_ip):
    " "
    URL = "https://%s/StreamingStatisticsX?1" % phone_ip
    try:
        r = requests.get(URL, verify=False)
    except requests.ConnectionError as e:
        return 999

    if debug: print "get_streaming_stats: status code %s" % r.status_code
    return r.content



def format_meta_data(xml_string):
    " "
    if type(xml_string) !=  str:
        # we failed to get xml data back from the phone
        return  xml_string

    meta_dict = {}

    root = ET.fromstring(xml_string)
    if debug: print "root is now %s" % root

    for element in get_meta_data_keys():
        meta_dict[element] = root.find(element).text

    if debug: print "format_meta_data: meta_dict %s" % meta_dict
    return meta_dict



def usage():
    "Print out the module documentation"

    print __doc__
    sys.exit()



def get_headers():
	"REST header"
	try:
	    return {"ph-auth-token": sys.argv[2]}
	except IndexError:
		usage()



def get_container_common():
    return {"description" : "VoIP metadata collection"}



# ================================== Start Phantom Code Example =====

def add_container(name, sid):
    "Containers are objects which document incidents"

    url = 'https://{}/rest/container'.format(PHANTOM_SERVER)

    post_data = get_container_common().copy()
    post_data['name'] = 'VoIP_{} ({})'.format(name, sid)
    post_data['source_data_identifier'] = sid
    json_blob = json.dumps(post_data)

    # set verify to False when running with a self signed certificate
    r = requests.post(url, data=json_blob, headers=get_headers(), verify=False)
    if (r is None or r.status_code != 200):
      if r is None:
        print('error adding container')
      else:
        print('error {} {}'.format(r.status_code,json.loads(r.text)['message']))
      return False

    return r.json().get('id')



def add_artifact(meta_data, container_id):
    "Artifacts provde supporting information for their container object"

    url = 'https://{}/rest/artifact'.format(PHANTOM_SERVER)

    post_data = {}
    post_data['name'] = 'artifact for {}'.format(meta_data['Name'])
    post_data['label'] = ARTIFACT_LABEL
    post_data['container_id'] = container_id
    post_data['source_data_identifier'] = getpass.getuser()

    # The cef key is intended for structured data that can be used when
    # dealing with product agnostic apps or playbooks. Place any standard
    # CEF fields here.

    sip, sport = meta_data['RemoteAddr'].split('/')
    dip, dport = meta_data['LocalAddr'].split('/')

    cef = {
            'sourceAddress': sip,
            'sourcePort': sport,
            'destinationAddress': dip,
            'destinationPort': dport,
            'startTime': meta_data['StartTime'],
            'deviceHostName': meta_data['Name']
          }

    post_data['cef'] = cef
    post_data['data'] = meta_data.copy()         # The "data" key can contain arbitrary json data.

    json_blob = json.dumps(post_data)

    r = requests.post(url, data=json_blob, headers=get_headers(), verify=False)

    if (r is None or r.status_code != 200):
        if (r is None):
            print('error adding artifact')
        else:
            error = json.loads(r.text)
            print('error {} {}'.format(r.status_code, error['message']))
            return False

    resp_data = r.json()
    return resp_data.get('id')

# ================================== End Phantom Code Example =====



def get_meta_data_keys():

	""" Include the keys you wish to format for phantom cyber from the IP phone streaming statistics
	see the URL in get_streaming_stats and paste in a browser to see the XML returned for the phone """

	return   ("IsVideo",
              "StartTime",
              "RcvrCodec",
              "Name",
              "Latency",
              "MaxJitter",
              "AvgJitter",
              "RcvrLostPackets",
              "SenderEncrypted",
              "RemoteAddr",
              "LocalAddr",
              "StreamStatus")



if __name__ == '__main__':

    debug = False
    PHANTOM_SERVER = "10.255.78.71"
    ARTIFACT_LABEL = "event"                            #  This is user configurable, will show up in menu

    try:
        main(sys.argv[1])
    except IndexError:
        usage()