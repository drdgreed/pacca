"""
PACCA Agent Framework.

Multi-agent system for healthcare prior authorization processing.
"""

from pacca.agents.base import BaseAgent
from pacca.agents.classification_agent import (
    ClassificationOutput,
    ClinicalClassificationAgent,
)
from pacca.agents.decision_agent import DecisionOutput, DecisionSupportAgent
from pacca.agents.evidence_agent import EvidenceAggregationAgent, EvidenceOutput
from pacca.agents.orchestrator import OrchestrationAgent, WorkflowResult, WorkflowState
from pacca.agents.types import (
    AgentContext,
    AgentError,
    AgentResponse,
    AgentTimeoutError,
    AgentValidationError,
    LLMError,
    TokenUsage,
    ToolCall,
)

__all__ = [
    # Base
    "BaseAgent",
    # Types
    "AgentContext",
    "AgentResponse",
    "AgentError",
    "AgentTimeoutError",
    "AgentValidationError",
    "LLMError",
    "TokenUsage",
    "ToolCall",
    # Agents
    "EvidenceAggregationAgent",
    "EvidenceOutput",
    "ClinicalClassificationAgent",
    "ClassificationOutput",
    "DecisionSupportAgent",
    "DecisionOutput",
    # Orchestration
    "OrchestrationAgent",
    "WorkflowResult",
    "WorkflowState",
]
