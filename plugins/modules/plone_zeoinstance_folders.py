#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule
from pathlib import Path


DOCUMENTATION = r"""
module: plone_zeoinstance_folders
short_description: Create the folders for a Plone ZEO instance
description: This module is not meant to be used directly, but as a dependency of the plone_zeoinstance action plugin.

options:
    target:
        description:
            - The target directory where the ZEO instance will be installed
        required: true
        type: str
    instances:
        description:
            - A list of dictionaries with the instance names and ports
        required: false
        default: []
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
"""  # noqa: E501

EXAMPLES = r"""
- name: Install Plone ZEO server
  plone_zeoinstance_folders:
    - target: /opt/plone
    - instances:
        - name: instance1
          port: 8101
        - name: instance2
          port: 8102
    - environment_vars: |
        zope_i18n_compile_mo_files true
        CHAMELEON_CACHE /opt/plone/var/cache
        DIAZO_ALWAYS_CACHE_RULES true
        PTS_LANGUAGES en
    - zcml:
        - foo.bar
"""

_site_zcml_template = r"""
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:meta="http://namespaces.zope.org/meta"
    xmlns:five="http://namespaces.zope.org/five">

  <include package="Products.Five" />
  <meta:redefinePermission from="zope2.Public" to="zope.Public" />

  <!-- Load the meta -->
  <include files="package-includes/*-meta.zcml" />
  <five:loadProducts file="meta.zcml"/>

  <!-- Load the configuration -->
  <include files="package-includes/*-configure.zcml" />
  <five:loadProducts />

  <!-- Load the configuration overrides-->
  <includeOverrides files="package-includes/*-overrides.zcml" />
  <five:loadProductsOverrides />

  <securityPolicy
      component="AccessControl.security.SecurityPolicy" />

</configure>
""".lstrip()

_zcml_include_template = '<include package="{package}" />\n'

_zcml_additional_template = r"""
<configure xmlns="http://namespaces.zope.org/zope">

{additional_zcml}

</configure>
""".lstrip()

_interpreter_template = r"""
#!{target}/.venv/bin/python

import sys


_interactive = True
if len(sys.argv) > 1:
    _options, _args = __import__("getopt").getopt(sys.argv[1:], 'iIc:m:')
    _interactive = False
    for (_opt, _val) in _options:
        if _opt == '-i':
            _interactive = True
        elif _opt == '-c':
            exec(_val)
        elif _opt == '-m':
            sys.argv[1:] = _args
            _args = []
            __import__("runpy").run_module(_val, {{}}, "__main__", alter_sys=True)

    if _args:
        sys.argv[:] = _args
        __file__ = _args[0]
        del _options, _args
        with open(__file__) as __file__f:
            exec(compile(__file__f.read(), __file__, "exec"))

if _interactive:
    del _interactive
    __import__("code").interact(banner="", local=globals())
""".lstrip()

_instance_template = r"""
#!{target}/.venv/bin/python

import plone.recipe.zope2instance.ctl
import sys

if __name__ == "__main__":
    sys.exit(
        plone.recipe.zope2instance.ctl.main(
            [
                "-C",
                "{target}/parts/{name}/etc/zope.conf",
                "-p",
                "{target}/bin/interpreter",
                "-w",
                "{target}/parts/{name}/etc/wsgi.ini",
            ]
            + sys.argv[1:]
        )
    )
""".lstrip()

_zope_conf_template = r"""
%define INSTANCEHOME {target}/parts/instance
instancehome $INSTANCEHOME
%define CLIENTHOME {target}/var/instance
clienthome $CLIENTHOME
debug-mode off
security-policy-implementation C
verbose-security off
default-zpublisher-encoding utf-8
<environment>
    {environment_vars}
</environment>
<zodb_db main>
    # Main database
    cache-size 100000
# Blob-enabled ZEOStorage database
    <zeoclient>
      read-only false
      read-only-fallback false
      blob-dir {target}/var/blobstorage
      shared-blob-dir on
      server {target}/var/zeo.socket
      storage 1
      name zeostorage
      cache-size 128MB
    </zeoclient>
    mount-point /
</zodb_db>
python-check-interval 10000
""".lstrip()

_supervisord_conf_template = """
[program:{name}]
command = {target}/bin/{name} console
process_name = {name}
directory = {target}
priority = 20
redirect_stderr = false
""".lstrip()


def run_command():
    changed = False
    module_args = {
        "target": {"required": True, "type": "str"},
        "instances": {"required": False, "type": "list", "default": []},
        "zcml": {"required": False, "type": "list", "default": []},
        "additional_zcml": {"required": False, "type": "str", "default": ""},
        "environment_vars": {"required": False, "type": "str", "default": ""},
        "wsgi_template": {"required": False, "type": "str", "default": ""},
    }
    module = AnsibleModule(argument_spec=module_args)

    target = Path(module.params["target"]).expanduser().resolve()

    # Prepare the bin folder where we will have the instance scripts
    bin_folder = target / "bin"
    if not bin_folder.exists():
        changed = True
        bin_folder.mkdir(mode=0o700, parents=True)

    etc_folder = target / "etc"
    if not etc_folder.exists():
        changed = True
        etc_folder.mkdir(mode=0o700, parents=True)

    instances = module.params.get("instances", [])
    zcml = module.params.get("zcml", [])
    additional_zcml = module.params.get("additional_zcml", "")
    environment_vars = module.params.get("environment_vars", "")

    instance_dirs = [
        "bin",
        "etc/packages-includes",
        "var",
    ]
    for instance in instances:
        base_folder = target / "parts" / instance["name"]
        for instance_dir in instance_dirs:
            instance_dir = base_folder / instance_dir
            if not instance_dir.exists():
                changed = True
                instance_dir.mkdir(parents=True)

        site_zcml_file = base_folder / "etc" / "site.zcml"
        expected_content = _site_zcml_template
        if (
            not site_zcml_file.exists()
            or expected_content != site_zcml_file.read_text()
        ):
            changed = True
            site_zcml_file.write_text(expected_content)

        zope_conf_file = base_folder / "etc" / "zope.conf"
        expected_content = _zope_conf_template.format(
            target=target, environment_vars=environment_vars
        )
        if (
            not zope_conf_file.exists()
            or expected_content != zope_conf_file.read_text()
        ):
            changed = True
            zope_conf_file.write_text(expected_content)

        instance_zcml_folder = base_folder / "etc/packages-includes"

        for idx, package in enumerate(zcml):
            zcml_file = instance_zcml_folder / f"1{idx:02d}-{package}.zcml"
            expected_content = _zcml_include_template.format(package=package)
            if not zcml_file.exists() or expected_content != zcml_file.read_text():
                changed = True
                zcml_file.write_text(expected_content)

        additional_zcml_file = instance_zcml_folder / "999-additional-overrides.zcml"
        expected_content = _zcml_additional_template.format(
            additional_zcml=additional_zcml
        )
        if (
            not additional_zcml_file.exists()
            or expected_content != additional_zcml_file.read_text()
        ):
            changed = True
            additional_zcml_file.write_text(expected_content)

        interpreter_file = base_folder / "bin" / "interpreter"
        expected_content = _interpreter_template.format(target=target)
        if (
            not interpreter_file.exists()
            or expected_content != interpreter_file.read_text()
        ):
            changed = True
            interpreter_file.write_text(expected_content)

        instance_file = target / "bin" / instance["name"]
        expected_content = _instance_template.format(
            target=target, name=instance["name"]
        )
        if not instance_file.exists() or expected_content != instance_file.read_text():
            changed = True
            instance_file.touch(mode=0o700)
            instance_file.write_text(expected_content)

        instance_var_folder = target / "var" / instance["name"]
        if not instance_var_folder.exists():
            changed = True
            instance_var_folder.mkdir(parents=True)

        supervisor_conf_file = etc_folder / f"supervisord.d/{instance['name']}.conf"
        if not instance.get("skip_supervisor", False):
            expected_content = _supervisord_conf_template.format(
                target=target, name=instance["name"]
            )
            if (
                not supervisor_conf_file.exists()
                or expected_content != supervisor_conf_file.read_text()
            ):
                changed = True
                supervisor_conf_file.write_text(expected_content)
        else:
            if supervisor_conf_file.exists():
                changed = True
                supervisor_conf_file.unlink()

    module.exit_json(
        changed=changed,
        meta={"msg": "Plone ZEO instance folders created", "target": str(target)},
    )


def main():
    run_command()


if __name__ == "__main__":
    main()
