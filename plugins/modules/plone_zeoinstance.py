#!/usr/bin/python

DOCUMENTATION = r"""
module: plone_zeoinstance
short_description: Create the ZEO instances
description: This module uses the plone_zeoinstance_folders module to create
             the folders for the ZEO instances.

options:
    target:
        description:
            - The target directory where the ZEO instance will be installed
        required: true
        type: str
    instances:
        description:
            - A list of dictionaries with the instance that need to have a
              name and can optionally have an some additional parameters like: http_port
        required: false
        default:
            - name: instance
        type: list
    zcml:
        description:
            - A list packages to include in the instance.zcml file
        required: false
        default: []
        type: list
    additional_zcml:
        description:
            - A zcml snippet that will be included last
        required: false
        default: ''
        type: str
    environment_vars:
        description:
            - The environment variables to set for the instance
        required: false
        default: ''
        type: str
    wsgi_template:
        description:
            - A template for the wsgi file
        required: false
        default: ''
        type: str
    fast_listen:
        description:
            - Whether to use the fast-listen option in the instance
        required: false
        default: false
        type: bool
    base_port:
        description:
            - The base port number to use for the instances
        required: false
        default: 8080
        type: int
    threads:
        description:
            - The number of threads to use in the instances
        required: false
        default: 2
        type: int
"""

EXAMPLES = r"""
- name: Install Plone ZEO server
  plone_zeoinstance:
    target: /opt/plone
    instances:
      - name: instance1
      - name: instance2
    environment_vars: |
      zope_i18n_compile_mo_files true
      CHAMELEON_CACHE /opt/plone/var/cache
      DIAZO_ALWAYS_CACHE_RULES true
      PTS_LANGUAGES en
    zcml:
      - foo.bar
"""
