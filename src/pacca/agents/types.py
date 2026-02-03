"""
Agent type definitions and response models.

Defines the core types used across all agents in the PACCA system,
including response structures, tool calls, and context management.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from uuid7 import uuid7

from pacca.models.enums import AgentAutonomyLevel, AgentType

# Generic type for agent-specific output
T = TypeVar("T", bound=BaseModel)


class ToolCall(BaseModel):
    """
    Represents a tool call made by an agent.

    Tools are external capabilities agents can invoke,
    such as database queries, API calls, or guideline searches.
    """

    model_config = ConfigDict(frozen=True)

    tool_id: str = Field(default_factory=lambda: str(uuid7())[:8])
    tool_name: str = Field(..., description="Name of the tool called")
    tool_input: dict[str, Any] = Field(..., description="Input parameters")
    tool_output: Any | None = Field(None, description="Output from tool")
    success: bool = Field(True, description="Whether tool call succeeded")
    error_message: str | None = Field(None, description="Error if failed")
    duration_ms: int | None = Field(None, description="Execution duration")
    called_at: datetime = Field(default_factory=datetime.utcnow)


class TokenUsage(BaseModel):
    """Token usage statistics for an LLM call."""

    model_config = ConfigDict(frozen=True)

    input_tokens: int = Field(0, ge=0, description="Input/prompt tokens")
    output_tokens: int = Field(0, ge=0, description="Output/completion tokens")
    total_tokens: int = Field(0, ge=0, description="Total tokens used")

    @property
    def estimated_cost(self) -> float:
        """Estimate cost based on Claude pricing (approximate)."""
        # Claude 3.5 Sonnet pricing: $3/M input, $15/M output
        input_cost = (self.input_tokens / 1_000_000) * 3.0
        output_cost = (self.output_tokens / 1_000_000) * 15.0
        return input_cost + output_cost


class AgentContext(BaseModel):
    """
    Context passed to agents for request processing.

    Contains all information an agent needs to perform its task,
    including request data, prior agent outputs, and configuration.
    """

    model_config = ConfigDict(frozen=False)

    # Request identification
    request_id: str = Field(..., description="Authorization request ID")
    correlation_id: str = Field(
        default_factory=lambda: str(uuid7()), description="Correlation ID for tracing"
    )

    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)

    # Agent chain state
    previous_agents: list[AgentType] = Field(
        default_factory=list, description="Agents that have processed this request"
    )
    agent_outputs: dict[str, Any] = Field(
        default_factory=dict, description="Outputs from previous agents"
    )

    # Configuration overrides
    autonomy_level: AgentAutonomyLevel = Field(
        AgentAutonomyLevel.SUPERVISED,
        description="Autonomy level for this request",
    )
    force_escalation: bool = Field(
        False, description="Force escalation regardless of confidence"
    )
    skip_agents: list[AgentType] = Field(
        default_factory=list, description="Agents to skip"
    )

    # Metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional context metadata"
    )

    def add_agent_output(self, agent_type: AgentType, output: Any) -> None:
        """Record output from an agent."""
        self.previous_agents.append(agent_type)
        self.agent_outputs[agent_type.value] = output

    def get_agent_output(self, agent_type: AgentType) -> Any | None:
        """Get output from a specific agent."""
        return self.agent_outputs.get(agent_type.value)

    def has_run(self, agent_type: AgentType) -> bool:
        """Check if an agent has already processed this request."""
        return agent_type in self.previous_agents


class AgentResponse(BaseModel, Generic[T]):
    """
    Standard response structure from all agents.

    Wraps the agent-specific output with metadata about
    the execution, including timing, confidence, and any errors.
    """

    model_config = ConfigDict(frozen=True)

    # Identification
    agent_type: AgentType = Field(..., description="Type of agent that produced this")
    agent_id: str = Field(..., description="Unique agent instance ID")
    request_id: str = Field(..., description="Request being processed")

    # Status
    success: bool = Field(True, description="Whether agent completed successfully")
    error_message: str | None = Field(None, description="Error message if failed")
    error_type: str | None = Field(None, description="Error type/class name")

    # Output
    output: T | None = Field(None, description="Agent-specific output")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in output (0-1)"
    )

    # Recommendations
    should_escalate: bool = Field(
        False, description="Whether this should escalate to human"
    )
    escalation_reasons: list[str] = Field(
        default_factory=list, description="Reasons for escalation recommendation"
    )
    next_agent: AgentType | None = Field(
        None, description="Recommended next agent in chain"
    )

    # Execution details
    tool_calls: list[ToolCall] = Field(
        default_factory=list, description="Tools called during execution"
    )
    token_usage: TokenUsage = Field(
        default_factory=TokenUsage, description="LLM token usage"
    )

    # Timing
    started_at: datetime = Field(..., description="When agent started")
    completed_at: datetime = Field(
        default_factory=datetime.utcnow, description="When agent completed"
    )

    @property
    def duration_ms(self) -> int:
        """Calculate execution duration in milliseconds."""
        delta = self.completed_at - self.started_at
        return int(delta.total_seconds() * 1000)

    @property
    def duration_seconds(self) -> float:
        """Calculate execution duration in seconds."""
        return self.duration_ms / 1000


class AgentError(Exception):
    """
    Base exception for agent errors.

    Provides structured error information for logging and handling.
    """

    def __init__(
        self,
        message: str,
        agent_type: AgentType,
        request_id: str | None = None,
        recoverable: bool = True,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.agent_type = agent_type
        self.request_id = request_id
        self.recoverable = recoverable
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for logging."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "agent_type": self.agent_type.value,
            "request_id": self.request_id,
            "recoverable": self.recoverable,
            "details": self.details,
        }


class AgentTimeoutError(AgentError):
    """Agent execution timed out."""

    def __init__(
        self,
        agent_type: AgentType,
        timeout_seconds: int,
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message=f"Agent {agent_type.value} timed out after {timeout_seconds}s",
            agent_type=agent_type,
            request_id=request_id,
            recoverable=True,
            details={"timeout_seconds": timeout_seconds},
        )


class AgentValidationError(AgentError):
    """Agent input validation failed."""

    def __init__(
        self,
        agent_type: AgentType,
        validation_errors: list[str],
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message=f"Validation failed for {agent_type.value}: {', '.join(validation_errors)}",
            agent_type=agent_type,
            request_id=request_id,
            recoverable=False,
            details={"validation_errors": validation_errors},
        )


class LLMError(AgentError):
    """Error from LLM API call."""

    def __init__(
        self,
        agent_type: AgentType,
        llm_error: str,
        request_id: str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(
            message=f"LLM error in {agent_type.value}: {llm_error}",
            agent_type=agent_type,
            request_id=request_id,
            recoverable=status_code in (429, 500, 502, 503, 504) if status_code else True,
            details={"llm_error": llm_error, "status_code": status_code},
        )
