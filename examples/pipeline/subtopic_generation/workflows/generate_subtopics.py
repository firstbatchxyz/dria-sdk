import logging
from dria.models import Task, Model, TaskInput
from typing import List, Optional, Any
from dria_workflows import WorkflowBuilder, Operator, Write, Edge, Read, GetAll, Workflow, ConditionBuilder, Expression
import json
import re
import random
from typing import Dict, List
from dria.pipelines import Step
from dria.pipelines import Step, StepTemplate


class GenerateSubtopics(StepTemplate):
    def create_workflow(
            self,
            topics: List[str]
    ) -> Workflow:
        """Generate subtopics for a given topic.

        Args:
            topics (list): The input data for the workflow.
        Returns:
            Workflow: The built workflow for subtopic generation.
        """
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        builder = WorkflowBuilder(topics=topics)

        # Step A: GenerateSubtopics
        builder.generative_step(
            id="generate_subtopics",
            path="workflows/prompts/generate_subtopics.md",
            operator=Operator.GENERATION,
            inputs=[
                GetAll.new(key="topics", required=True),
            ],
            outputs=[Write.new("subtopics")]
        )

        flow = [
            Edge(source="generate_subtopics", target="_end")
        ]
        builder.flow(flow)
        builder.set_return_value("subtopics")
        workflow = builder.build()

        return workflow
