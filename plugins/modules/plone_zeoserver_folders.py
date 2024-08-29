#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule
from pathlib import Path


DOCUMENTATION = r"""
module: plone_zeoserver_folders
short_description: Create the folders for a Plone ZEO server
description: This module is not meant to be used directly,
             but as a dependency of the plone_zeoserver action plugin.

options:
    target:
        description:
            - The target directory where the ZEO server will be installed
        required: true
        type: str
"""

EXAMPLES = r"""
- name: Install Plone ZEO server
  plone_zeoserver_folders:
    - target: /opt/plone
"""

_supervisord_conf_template = """
[program:zeo]
command = {target}/parts/zeo/bin/runzeo
process_name = zeo
directory = {target}/parts/zeo/
priority = 10
redirect_stderr = false
""".lstrip()


def run_command():
    changed = False
    module_args = dict(
        target=dict(required=True, type="str"),
    )
    module = AnsibleModule(argument_spec=module_args)

    target = Path(module.params["target"]).expanduser().resolve()

    zeo_dirs = [
        "bin",
        "etc/supervisord.d",
        "parts/zeo/bin",
        "parts/zeo/etc",
        "var/blobstorage",
        "var/cache",
        "var/filestorage",
        "var/log",
        "var/supervisor",
        "var/zeo",
    ]
    for zeo_dir in zeo_dirs:
        zeo_dir = target / zeo_dir
        if not zeo_dir.exists():
            changed = True
            zeo_dir.mkdir(mode=0o700, parents=True)

    # Add the supervisor configuration file
    supervisor_conf_file = target / "etc/supervisord.d/zeo.conf"
    expected_content = _supervisord_conf_template.format(target=target)
    if (
        not supervisor_conf_file.exists()
        or expected_content != supervisor_conf_file.read_text()
    ):
        changed = True
        supervisor_conf_file.touch(mode=0o600)
        supervisor_conf_file.write_text(expected_content)

    module.exit_json(
        changed=changed,
        meta={"msg": "Plone ZEO server folders created", "target": str(target)},
    )


def main():
    run_command()


if __name__ == "__main__":
    main()
