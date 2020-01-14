# README for PhantomIngest.py

This document illustrates use of the PhantomIngest class and methods.

Verify and tested using Phantom version 4.5.15922

## Usage examples
Import the module and instanciate it with the hostname and access token.
```
import PhantomIngest as ingest
p = ingest.PhantomIngest("phantom.example.net", "yourPhantomToken")
```
## Create container

Add or update the fields specified in https://phantom.example.net/docs/rest/create_container
```
kontainer = {"name": "Voltaire", "description": "French Enlightenment writer, historian, and philosopher."}
```
Create the container, returned is the container id, needed to add an artifact to the container
```
try:
    container_id = p.add_container(**kontainer)
except AssertionError as e:
    print "Any HTTP return code other than OK %s" % e
except Exception as e:
    print "Typically the phantom host did not respond, a connection error %s" % e
```

## Add artifact to the container
Add or update fields specified in https://phantom.example.net/docs/rest/artifacts
```
art_i_fact = {"name": "François-Marie Arouet", "source_data_identifier": "IR_3458575"}
```
Specify the CEF data you want in the artifact, or an empty dictionary.
```
cef = {'sourceAddress': '192.0.2.1', 'sourcePort': '6553', 'sourceUserId': 'voltaire@example.net'}
cef = {}
```
Add meta data, or an empty dictionary if none.
```
meta_data = {"Influenced by": "John Locke, William Shakespeare, Isaac Newton", "Born": "November 21, 1694",
             "quote": "Judge of a man by his questions rather than by his answers."}
meta_data = {}
```
Add the artifact.
```
artifact_id = p.add_artifact(container_id, cef, meta_data, **art_i_fact)
print p.status_code
```
Each container can have no artifacts, or one or more artifacts.

## Copyright and contact info
Copyright (c) 2020 World Wide Technology, LLC
All rights reserved.

author: joel.king@wwt.com  GitHub/GitLab: @joelwking

