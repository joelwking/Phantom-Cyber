# Splunk Phantom
The F5 and Meraki app contributions to the contest were recognized as a first place (tie) entry at the 17 June 2016 webinar.
The apps will be discussed at the 26th August 2016 Phantom tech session: Video Tutorial https://my.phantom.us/video/23/ [requires login].

http://www.slideshare.net/joelwking/10000-phantom-app-playbook-contest-f5-and-cisco-meraki

The Ansible Tower app was developed for the second app challenge.

# Blog
In an effort to demonstrate building and automating the next generation networks, I’ve submitted on behalf of World Wide Technology, these entries in the 2016 Phantom playbook and app contest. 

This contest is sponsored by Phantom (www.phantom.us) to promote the community development of playbooks and apps, the press release http://www.businesswire.com/news/home/20160120005085/en is available.

*Phantom is a Security Automation & Orchestration platform that integrates with existing security technologies in order to provide a layer of “connective tissue” between them.  Phantom doesn’t replace existing security products, but instead uses Playbooks and Apps to make them smarter, faster and stronger.*

## F5 App
At World Wide Technology, we are engaging with customers in their evaluation of Phantom and this video clip provides a demonstration of the playbooks and apps developed to ingest data through the REST API and then implement a firewall rule on a F5 BIG-IP appliance to block the source IP address identified in the artifact.

https://youtu.be/1lktjQzVcQQ

This app is also referenced on F5 DevCentral as part of the *June is Programmability Month!* initiative.

https://devcentral.f5.com/codeshare/f5-big-ip-phantom-cyber-app-915

### Installation
To install this app download the tarball ( f5_firewall.tgz ) and follow the app installation instructions in the Phantom documentation, see `https://<your_phantom_host>/docs/admin/apps`.

## Metadata Collection
This utility creates containers and artifacts via the Phantom REST API from metadata off Cisco IP Phones. It is used to programatically create incidents for testing the F5 and Meraki apps.

## REST_ingest
This is a python class and methods to abstract the functionality of creating containers and artifacts in Phantom.

## Meraki App
*Integrating Cloud Controlled WiFi, Routing and Security with Security Automation and Orchestration*

Cisco Meraki is a cloud managed architecture, which is used to deploy, configure, manage and monitor WiFI, routing and security appliances in small to medium branch office locations. Phantom Cyber is an extensible security automation and orchestration package which allow custom applications to be written within its framework. This video demonstrates how the Meraki device provisioning APIs can be used by a Phantom app to quickly locate devices in the Meraki network.

https://youtu.be/RaUU7evOJi0

This app has been updated to include a `bind network` action which can be used to associate (substitute) a named configuration template to a specified network.

* [How Agile Is Your Managed SD-WAN Solution?](https://www.wwt.com/article/how-agile-is-your-managed-sd-wan-solution)
* [Video Clip](https://vimeo.com/423587585)
* [DevPost submission](https://devpost.com/software/meraki-app-for-splunk-phantom)

### Installation
To install this app download the tarball ( meraki.tgz ) and follow the app installation instructions in the Phantom documentation, see `https://<your_phantom_host>/docs/admin/apps`.

## Ansible Tower app
Ansible Tower is a enterprice licensed GUI for managing Ansible workflows. This Phantom app implements an interface to run (launch) job templates defined in Ansible Tower from Phantom. Variables can be passed from a Phantom playbook to the job template. Ansible is a force multiplier for Phantom, as it provides a means to execute simple to complex playbooks written for Ansible from Phantom.

While this app provides a high degree of flexibility to security operations, only the success or failure of the job launched in Ansible Tower is returned to the Phantom playbook, which means output cannot be used in subsequent playbook steps. 

A sample configurations for implementing a Remote Triggered Black Hole, adding a static route to a Cisco router, is provided in this powerpoint slide deck, for both Phantom and Ansible. 

http://www.slideshare.net/joelwking/phantom-app-ansible-tower

The Ansible playbook ( RTBH.yml ) and the Phantom playbook ( Remote_Trigger_Black_Hole.py ) are provided in the repository.

A youtube video is available demonstrating how a Cisco ACI fabric configuration can be modified from Phantom. 
The Phantom playbook ( Dropzone_2.py ) and the Ansible playbook ( dbgacEpgToIp.yml ) and Jinja template ( dbgacEpgToIp.j2 ) to create the ACI XML file is also provided.

https://youtu.be/neaCPil8c0k

### Installation
To install this app download the tarball ( ansible_tower.tgz ) and follow the app installation instructions in the Phantom documentation, see `https://<your_phantom_host>/docs/admin/apps`.

## A10 Lightning Application Delivery System (LADS) App
A10 Lightning Application Delivery System (LADS) is a subscription based managed service (SaaS) that provides a unified set of features for applications deployed in a public and private cloud infrastructure. This app enables security operations the ability to block or unblock IP addresses and IP networks from accessing the application running behind the LADC Cluster. 

This app uses the northbound API to the A10 Lightning Controller to manage the configurations of the LADC Cluster. For more information or to request a trial, refer to https://www.a10networks.com/products/lightning-application-delivery-service and watch this video on the integration of Phantom and A10 LADS.

https://youtu.be/vakqZ0wGh6g

### Installation
To install this app download the tarball ( A10_LADS.tgz ) and follow the app installation instructions in the Phantom documentation, see `https://<your_phantom_host>/docs/admin/apps`.

# Contact Information
For more information on the security solutions at World Wide Technology, visit https://www.wwt.com/category/security-transformation.

## Author
Joel W. King - joel.king@wwt.com @joelwking
