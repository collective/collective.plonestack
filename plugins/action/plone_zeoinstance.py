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
        if "instances" not in module_args:
            module_args["instances"] = [{"name": "instance"}]
        instances = module_args["instances"]
        fast_listen = module_args.pop("fast_listen", True)
        base_port = module_args.pop("base_port", 8080)
        threads = module_args.pop("threads", 2)
        changed = False

        # call the plone_zeoserver_folders module
        plone_zeoinstance_folders_results = self._execute_module(
            module_name="collective.plonestack.plone_zeoinstance_folders",
            module_args=module_args,
            task_vars=task_vars,
        )
        if plone_zeoinstance_folders_results.get("failed"):
            result.update(plone_zeoinstance_folders_results)
            return result

        if plone_zeoinstance_folders_results.get("changed"):
            changed = True

        target = Path(module_args["target"])

        # Call the template action to render the wsgi.ini file
        wsgi_template = module_args.get("wsgi_template", "")
        if not wsgi_template:
            wsgi_template = _templates_folder / "wsgi.ini.j2"

        for idx, instance in enumerate(instances):
            wsgi_template_dest = (
                target / "parts" / instance["name"] / "etc" / "wsgi.ini"
            )
            template_task = self._task.copy()
            template_task.args = {
                "src": str(wsgi_template),
                "dest": str(wsgi_template_dest),
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
                    "target": module_args["target"],
                    "fast_listen": fast_listen,
                    "threads": threads,
                    "http_port": instance.get("http_port") or base_port + idx,
                }
            )
            template_action_results = template_action.run(
                task_vars=template_action_vars
            )
            if template_action_results.get("failed"):
                result.update(template_action_results)
                return result
            if template_action_results.get("changed"):
                changed = True

        if changed:
            result["changed"] = True
        return result
