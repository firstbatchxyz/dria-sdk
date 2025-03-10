"""
Workflow Factory Module

This module implements the Factory Pattern for workflow creation in the Dria SDK.
The Factory Pattern provides a way to create different workflow objects without
exposing the instantiation logic to the client and referring to the newly created
object using a common interface.

Key benefits of the Factory Pattern in this implementation:
1. Encapsulation: Hides the complex instantiation logic from clients
2. Standardization: All workflows follow the same interface (WorkflowTemplate)
3. Extensibility: New workflow types can be added without changing client code
4. Reusability: Common workflow patterns can be reused across different applications

The factory exports various pre-built workflow templates that can be instantiated
with specific parameters to create customized workflows for different AI tasks.
"""

__core_exports = [
    "Clair",
    "GenerateCode",
    "IterateCode",
    "EvolveComplexity",
    "ScoreComplexity",
    "EvolveInstruct",
    "EvolveQuality",
    "GenerateGraph",
    "TextMatching",
    "TextClassification",
    "SemanticTriplet",
    "MagPie",
    "SearchWeb",
    "Simple",
    "EvaluatePrediction",
    "ValidatePrediction",
    "SelfInstruct",
    "PersonaBackstory",
    "PersonaBio",
    "GenerateSubtopics",
    "CSVExtenderPipeline",
    "ListExtenderPipeline",
    "QAPipeline",
    "MultiHopQuestion",
    "InstructionBacktranslation",
    "Reasoning",
]

from .workflows.simple.task import Simple
from .workflows.clair.task import Clair
from .workflows.code_gen.task import GenerateCode, IterateCode
from .workflows.graph_builder.task import GenerateGraph
from .workflows.magpie_instruct.task import MagPie
from .workflows.self_instruct.task import SelfInstruct
from .workflows.instruction_backtranslation.task import InstructionBacktranslation
from .workflows.reasoning.task import Reasoning
from .workflows.evol_instruct import EvolveInstruct
from .workflows.model_as_a_judge import EvaluatePrediction, ValidatePrediction
from .workflows.evol_quality import EvolveQuality
from .subtopic.task import GenerateSubtopics
from .persona import PersonaBio


__all__ = __core_exports
