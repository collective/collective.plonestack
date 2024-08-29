from ansible.plugins.action import ActionBase
from pathlib import Path


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        """
        Run the action
        """
        result = super().run(tmp, task_vars)
        del tmp  # deprecated parameter, it should not be used

        module_args = self._task.args.copy()
        src = Path(module_args["target"]).expanduser().resolve() / "src"

        # Checkout the packages we need
        source_checkouts = module_args.get("source_checkouts", [])
        for source_checkout in source_checkouts:
            checkout_result = self._execute_module(
                module_name="ansible.builtin.git",
                module_args={
                    "repo": source_checkout["repo"],
                    "dest": str(src / source_checkout["name"]),
                    "version": source_checkout.get("version", "HEAD"),
                },
                task_vars=task_vars,
            )
            result.update(checkout_result)
            if checkout_result.get("failed"):
                return result

        # Run the plone_venv module
        module_results = self._execute_module(
            module_name="collective.plonestack.plone_venv",
            module_args=module_args,
            task_vars=task_vars,
        )
        result.update(module_results)
        return result
