#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from pathlib import Path

import shutil


DOCUMENTATION = r"""
module: plone_venv
short_description: Install a Plone python virtual environment

# version_added: "0.0.0"
description: Install python virtual environment given some options are given

options:
    target:
        description:
            - The target directory where the virtual environment will be installed
        required: true
        type: str
    python_version:
        description:
            - The python version to use for the virtual environment
        required: true
        type: str
    plone_version:
        description:
            - The Plone version to install
        required: true
        type: str
    constraints:
        description:
            - The constraints file to use
        required: false
        default: []
        type: list
    extra_constraints:
        description:
            - Additional constraints to add to the constraints file
        required: false
        type: dict
        default: {}
    extra_requirements:
        description:
            - Extra packages to install in the virtual environment
        required: false
        type: list
    source_checkouts:
        description:
            - Source checkouts to install in the virtual environment,
            - e.g.: ['git+https://github.com/plone/plone.app.contenttypes.git@master']
        required: false
        type: list
    use_uv:
        description:
            - Use uv to install the packages
        required: false
        default: True
        type: bool
"""

EXAMPLES = r"""
- name: Install Plone
  plone_venv:
    target: /opt/plone
    python_version: 3.8
    plone_version: 6.0.13
    extra_requirements:
      - plone.app.debugtoolbar
    source_checkouts:
      - git+https://github.com/plone/plone.app.contenttypes.git@master
    constraints:
      - https://dist.plone.org/release/6.0.13/constraints.txt
      - https://example.com/6.0.13/constraints.txt
    use_uv: true
"""

_default_requirements = [
    "Plone",
    "ZEO",
    "supervisor",
    "plone.recipe.zope2instance",
]


def constraints_to_dict(constraints):
    """We have a file with constraints. Take it and create a dict like:
    {package_name: version}
    """
    constraints_dict = {}
    for line in constraints.splitlines():
        if line.strip() and not line.startswith("#"):
            name, version = line.partition("==")[::2]
            if name and not name.startswith("-e "):
                # skip editable packages
                constraints_dict[name.strip()] = version.strip()
    return constraints_dict


def run_command():
    done = []

    module_args = {
        "target": {"type": "str", "required": True},
        "python_version": {"type": "str", "required": True},
        "constraints": {"type": "list", "required": False, "default": []},
        "extra_constraints": {"type": "dict", "required": False, "default": {}},
        "plone_version": {"type": "str", "required": True},
        "extra_requirements": {"type": "list", "required": False, "default": []},
        "source_checkouts": {"type": "list", "required": False, "default": []},
        "use_uv": {"type": "bool", "required": False, "default": True},
    }

    # Create the AnsibleModule object
    module = AnsibleModule(argument_spec=module_args)

    # Get the arguments
    target = Path(module.params["target"]).expanduser().resolve()

    python_version = module.params["python_version"]
    plone_version = module.params["plone_version"]
    extra_requirements = module.params["extra_requirements"]
    source_checkouts = module.params["source_checkouts"]
    use_uv = module.params["use_uv"]
    constraints = module.params["constraints"] or [
        f"https://dist.plone.org/release/{plone_version}/constraints.txt"
    ]
    extra_constraints = module.params["extra_constraints"]

    # Ensure target folder exists
    if not target.exists():
        target.mkdir(mode=0o700, parents=True)
        done.append(f"Created target folder {target}")

    # Create the requirements file
    requirements_lines = _default_requirements + extra_requirements

    # Add to the requirements the editable source checkouts
    for source_checkout in source_checkouts:
        name = source_checkout["name"]
        if name in requirements_lines:
            requirements_lines.remove(name)
        requirements_lines.append(f"-e {target / 'src' / name}")

    # Add a newline at the end
    requirements_lines.append("")

    requirements_txt = target / "requirements.txt"
    existing_requirements = (
        requirements_txt.read_text().splitlines() if requirements_txt.exists() else []
    )

    if existing_requirements != requirements_lines:
        requirements_txt.write_text("\n".join(requirements_lines))
        done.append(f"Created {requirements_txt}")

    packages_not_constrained = [
        source_checkout["name"] for source_checkout in source_checkouts
    ]

    constraints_values = {}
    for constraint in constraints:
        constraints_values.update(
            constraints_to_dict(fetch_url(module, constraint)[0].read().decode())
        )
    constraints_values.update(extra_constraints)
    for package in packages_not_constrained:
        constraints_values.pop(package, None)

    # Create the constraints.txt file
    constraints_txt = target / "constraints.txt"
    existing_constraints_text = (
        constraints_txt.read_text() if constraints_txt.exists() else ""
    )
    existing_constraints_values = constraints_to_dict(existing_constraints_text)

    if existing_constraints_values != constraints_values:
        constraints_txt.write_text(
            "\n".join(
                [
                    f"{name}=={version}"
                    for name, version in sorted(constraints_values.items())
                ]
            )
            + "\n"
        )
        done.append(f"Created {constraints_txt}")

    # Check that we have a virtual environment
    venv_folder = target / ".venv"
    if not venv_folder.exists():
        # Find the python executable that provides python_version
        python_executable = Path(shutil.which(f"python{python_version}"))
        if not python_executable:
            module.fail_json(
                msg=f"Python version {python_version} not found in the system"
            )
            return
        command = [python_executable, "-m", "venv", str(venv_folder)]
        module.run_command(command)
        done.append(f"Created virtual environment in {venv_folder}")
        if use_uv:
            command = [
                str(venv_folder / "bin" / "python"),
                "-m",
                "pip",
                "install",
                "uv",
            ]
            module.run_command(command)
            done.append("Installed uv")

    # Run a command to install the requirements respecting the constraints
    if done:
        command = [str(target / ".venv/bin/python"), "-m"]
        if use_uv:
            command.append("uv")
        command.extend(
            [
                "pip",
                "install",
                "-c",
                str(constraints_txt),
                "-r",
                str(requirements_txt),
            ]
        )
        exit_code, stdout, stderr = module.run_command(command)
        if exit_code != 0:
            module.fail_json(msg=stderr)

        done.append("Installed requirements")

    # Check if pip freeze is consistent with the constraints.txt file
    command = [str(venv_folder / "bin" / "pip"), "freeze"]
    _, pip_freeze_stdout, _ = module.run_command(command)

    missing_constraints = {
        key: value
        for key, value in constraints_to_dict(pip_freeze_stdout).items()
        if key not in constraints_values
    }
    if missing_constraints:
        module.warn(f"Missing constraints: {missing_constraints}")

    # ensure we have the a bin folder with useful symlinks
    bin_folder = target / "bin"
    if not bin_folder.exists():
        bin_folder.mkdir(mode=0o700, exist_ok=True)
        done.append(f"Created {bin_folder}")

    # Symlink supervisorctl and supervisord
    supervisorctl = bin_folder / "supervisorctl"
    if not supervisorctl.resolve() == target / ".venv/bin/supervisorctl":
        if supervisorctl.exists():
            supervisorctl.unlink()
        supervisorctl.symlink_to(target / ".venv/bin/supervisorctl")
        done.append(f"Created symlink {supervisorctl}")

    supervisord = bin_folder / "supervisord"
    if not supervisord.resolve() == target / ".venv/bin/supervisord":
        if supervisord.exists():
            supervisord.unlink()
        supervisord.symlink_to(target / ".venv/bin/supervisord")
        done.append(f"Created symlink {supervisord}")

    module.exit_json(
        changed=bool(done),
        meta={"msg": "Plone virtual environment created", "done": done},
    )


def main():
    run_command()


if __name__ == "__main__":
    main()
