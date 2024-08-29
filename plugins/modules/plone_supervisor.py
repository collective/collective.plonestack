#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule
from pathlib import Path


DOCUMENTATION = r"""
module: plone_supervisor
short_description: Create the supervisor configuration for serving a Plone site
description: This just creates the supervisor configuration file for a Plone site
             and ensures that we have convenience links to the supervisorctl command.

options:
    target:
        description:
            - The target directory where the supervisor configuration will be installed
        required: true
        type: str
"""

EXAMPLES = r"""
- name: Install Plone supervisor configuration
  plone_supervisor:
    - target: /opt/plone
"""

_supervisor_conf_file = """
[supervisord]
logfile={target}/var/log/supervisord.log
pidfile={target}/var/supervisor/supervisord.pid
logfile_maxbytes=50MB
logfile_backups=10
loglevel=info
childlogdir={target}/var/log
directory={target}

[unix_http_server]
file = {target}/var/supervisord.sock
username =
password =
chmod = 0700

[supervisorctl]
serverurl = unix://{target}/var/supervisord.sock
username =
password =

[rpcinterface:supervisor]
supervisor.rpcinterface_factory=supervisor.rpcinterface:make_main_rpcinterface

[include]
files = {target}/etc/supervisord.d/*.conf
""".lstrip()


def run_module():
    done = []
    module_args = dict(
        target=dict(type="str", required=True),
    )

    result = dict(
        original_message="",
        message="",
        done=done,
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    target = Path(module.params["target"]).expanduser().resolve()
    if module.params["target"] != str(target):
        module.params["target"] = str(target)

    supervisord_folder = target / "etc/supervisord.d"
    if not supervisord_folder.exists():
        done.append(f"Created folder {supervisord_folder}")
        supervisord_folder.mkdir(mode=0o700, parents=True, exist_ok=True)

    supervisord_conf = target / "etc/supervisord.conf"
    expected_content = _supervisor_conf_file.format(target=target)
    if (
        not supervisord_conf.exists()
        or expected_content != supervisord_conf.read_text()
    ):
        done.append(f"Created {supervisord_conf}")
        supervisord_conf.write_text(_supervisor_conf_file.format(target=target))

    result["changed"] = bool(done)
    result["original_message"] = "Plone supervisor configuration created"
    result["message"] = "Plone supervisor configuration created"
    module.exit_json(
        changed=bool(done),
        meta=result,
    )


def main():
    run_module()


if __name__ == "__main__":
    main()
