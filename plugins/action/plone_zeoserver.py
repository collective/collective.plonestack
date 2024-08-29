#!/usr/bin/python

from ansible.plugins.action import ActionBase
from pathlib import Path


_templates_folder = Path(__file__).parent / "templates" / Path(__file__).stem


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        """
        Run the action
        """
        result = super().run(tmp, task_vars)
        del tmp  # deprecated parameter, it should not be used

        module_args = self._task.args.copy()
        target = Path(module_args["target"]).expanduser().resolve()
        zeo_server_address = (
            module_args.get("zeo_server_address") or f"{target}/var/zeo.socket"
        )
        blob_dir = module_args.get("blob_dir") or f"{target}/var/blobstorage"

        # call the plone_zeoserver_folders module
        plone_zeoserver_folders_results = self._execute_module(
            module_name="collective.plonestack.plone_zeoserver_folders",
            module_args={"target": str(target)},
            task_vars=task_vars,
        )

        result.update(plone_zeoserver_folders_results)
        if plone_zeoserver_folders_results.get("failed"):
            return result

        # Call the template action to render the zeo.conf file
        zeo_conf_template = module_args.get("zeo_conf_template")
        if not zeo_conf_template:
            zeo_conf_template = _templates_folder / "zeo.conf.j2"

        zeo_conf_dest = Path(module_args["target"]) / "parts/zeo/etc/zeo.conf"

        template_task = self._task.copy()
        template_task.args = {
            "src": str(zeo_conf_template),
            "dest": str(zeo_conf_dest),
            "mode": "0600",
        }

        template_action = self._shared_loader_obj.action_loader.get(
            "ansible.builtin.template",
            task=template_task,
            connection=self._connection,
            play_context=self._play_context,
            loader=self._loader,
            templar=self._templar,
            shared_loader_obj=self._shared_loader_obj,
        )
        template_action_vars = task_vars.copy()
        template_action_vars.update(
            {
                "target": str(target),
                "zeo_server_address": zeo_server_address,
                "blob_dir": blob_dir,
            }
        )
        template_action_results = template_action.run(task_vars=template_action_vars)
        result.update(template_action_results)
        if template_action_results.get("failed"):
            return result

        # Call the template action to render the runzeo file
        runzeo_template = module_args.get("runzeo_template")
        if not runzeo_template:
            runzeo_template = _templates_folder / "runzeo.j2"

        runzeo_dest = Path(module_args["target"]) / "parts/zeo/bin/runzeo"

        template_task = self._task.copy()
        template_task.args = {
            "src": str(runzeo_template),
            "dest": str(runzeo_dest),
            "mode": "0700",
        }

        template_action = self._shared_loader_obj.action_loader.get(
            "ansible.builtin.template",
            task=template_task,
            connection=self._connection,
            play_context=self._play_context,
            loader=self._loader,
            templar=self._templar,
            shared_loader_obj=self._shared_loader_obj,
        )
        template_action_vars = task_vars.copy()
        template_action_vars.update({"target": module_args["target"]})
        template_action_results = template_action.run(task_vars=template_action_vars)
        result.update(template_action_results)
        if template_action_results.get("failed"):
            return result

        return result
