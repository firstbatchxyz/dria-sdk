from dria_workflows import Workflow

from dria.workflow import WorkflowTemplate


class Simple(WorkflowTemplate):

    def define_workflow(self):
        """
        Creates a workflow for simple text generation.

        Returns:
            Workflow: The constructed workflow
        """
        self.add_step(prompt="{{prompt}}", outputs=["response"])
        self.set_output("response")
