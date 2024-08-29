#!/usr/bin/python
DOCUMENTATION = r"""
module: plone_zeoserver
short_description: Create the folders for a Plone ZEO server
description: This module is not meant to be used directly,
             but as a dependency of the plone_zeoserver action plugin.

options:
    target:
        description:
            - The target directory where the ZEO server will be installed
        required: true
        type: str
    zeo_server_address:
        description:
            - The address of the ZEO server or socket file
        required: false
        default: f"{target}/var/zeo.socket"
        type: str
    blob_dir:
        description:
            - The directory to store the blobs
        required: false
        default: f"{target}/var/blobstorage"
        type: str
    zeo_conf_template:
        description:
            - The template file to use for the zeo.conf file
        required: false
        type: str
    runzeo_template:
        description:
            - The template file to use for the runzeo file
        required: false
        type: str
"""

EXAMPLES = r"""
- name: Install Plone ZEO server
  plone_zeoserver:
    - target: /opt/plone/zeoserver
"""
