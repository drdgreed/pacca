"""
Base agent implementation for the PACCA system.

Provides the abstract base class that all agents inherit from,
defining the common interface, LLM integration, and lifecycle hooks.
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generic, TypeVar

import anthropic
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from uuid7 import uuid7

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
from pacca.config import get_logger, get_settings
from pacca.models.enums import AgentAutonomyLevel, AgentType

# Type variable for agent-specific output
T = TypeVar("T", bound=BaseModel)

logger = get_logger(__name__)


class BaseAgent(ABC, Generic[T]):
    """
    Abstract base class for all PACCA agents.

    Provides common functionality including:
    - LLM client management
    - Structured output parsing
    - Error handling and retry logic
    - Logging and observability
    - Timeout management

    Subclasses must implement:
    - agent_type: The type of agent
    - output_model: Pydantic model for structured output
    - execute(): The main agent logic
    """

    def __init__(
        self,
        model: str | None = None,
        max_tokens: int | None = None,
        timeout: int | None = None,
        autonomy_level: AgentAutonomyLevel = AgentAutonomyLevel.SUPERVISED,
    ) -> None:
        """
        Initialize the agent.

        Args:
            model: Claude model to use. Defaults to settings.
            max_tokens: Max tokens for response. Defaults to settings.
            timeout: Timeout in seconds. Defaults to settings.
            autonomy_level: Agent's autonomy level.
        """
        settings = get_settings()

        self.agent_id = f"{self.agent_type.value}-{uuid7()}"
        self.model = model or settings.default_model
        self.max_tokens = max_tokens or settings.max_tokens
        self.timeout = timeout or settings.agent_timeout
        self.autonomy_level = autonomy_level

        # Initialize Anthropic client
        self._client = anthropic.Anthropic(
            api_key=settings.anthropic_api_key.get_secret_value()
        )

        # Tracking
        self._tool_calls: list[ToolCall] = []
        self._token_usage = TokenUsage()

        logger.info(
            "agent_initialized",
            agent_id=self.agent_id,
            agent_type=self.agent_type.value,
            model=self.model,
            autonomy_level=self.autonomy_level.value,
        )

    @property
    @abstractmethod
    def agent_type(self) -> AgentType:
        """Return the type of this agent."""
        ...

    @property
    @abstractmethod
    def output_model(self) -> type[T]:
        """Return the Pydantic model for this agent's output."""
        ...

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        ...

    @abstractmethod
    async def execute(
        self,
        request: Any,
        context: AgentContext,
    ) -> T:
        """
        Execute the agent's main logic.

        Args:
            request: The authorization request to process
            context: Execution context with prior agent outputs

        Returns:
            Agent-specific output model instance

        Raises:
            AgentError: If execution fails
        """
        ...

    async def run(
        self,
        request: Any,
        context: AgentContext,
    ) -> AgentResponse[T]:
        """
        Run the agent with full lifecycle management.

        This is the main entry point that wraps execute() with:
        - Validation
        - Timeout handling
        - Error handling
        - Response construction
        - Logging

        Args:
            request: The authorization request to process
            context: Execution context

        Returns:
            AgentResponse containing output and metadata
        """
        started_at = datetime.utcnow()
        self._tool_calls = []
        self._token_usage = TokenUsage()

        logger.info(
            "agent_run_started",
            agent_id=self.agent_id,
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )

        try:
            # Validate inputs
            validation_errors = await self.validate(request, context)
            if validation_errors:
                raise AgentValidationError(
                    agent_type=self.agent_type,
                    validation_errors=validation_errors,
                    request_id=context.request_id,
                )

            # Execute with timeout
            output = await asyncio.wait_for(
                self.execute(request, context),
                timeout=self.timeout,
            )

            # Calculate confidence
            confidence = await self.calculate_confidence(output, context)

            # Determine escalation
            should_escalate, escalation_reasons = await self.should_escalate(
                output, confidence, context
            )

            # Determine next agent
            next_agent = await self.get_next_agent(output, context)

            response = AgentResponse[T](
                agent_type=self.agent_type,
                agent_id=self.agent_id,
                request_id=context.request_id,
                success=True,
                output=output,
                confidence_score=confidence,
                should_escalate=should_escalate,
                escalation_reasons=escalation_reasons,
                next_agent=next_agent,
                tool_calls=self._tool_calls,
                token_usage=self._token_usage,
                started_at=started_at,
            )

            logger.info(
                "agent_run_completed",
                agent_id=self.agent_id,
                request_id=context.request_id,
                success=True,
                confidence=confidence,
                should_escalate=should_escalate,
                duration_ms=response.duration_ms,
                token_usage=self._token_usage.total_tokens,
            )

            return response

        except asyncio.TimeoutError:
            error = AgentTimeoutError(
                agent_type=self.agent_type,
                timeout_seconds=self.timeout,
                request_id=context.request_id,
            )
            logger.error("agent_timeout", **error.to_dict())
            return self._error_response(error, started_at, context.request_id)

        except AgentError as e:
            logger.error("agent_error", **e.to_dict())
            return self._error_response(e, started_at, context.request_id)

        except Exception as e:
            error = AgentError(
                message=str(e),
                agent_type=self.agent_type,
                request_id=context.request_id,
                recoverable=False,
                details={"exception_type": type(e).__name__},
            )
            logger.exception("agent_unexpected_error", **error.to_dict())
            return self._error_response(error, started_at, context.request_id)

    def _error_response(
        self,
        error: AgentError,
        started_at: datetime,
        request_id: str,
    ) -> AgentResponse[T]:
        """Construct an error response."""
        return AgentResponse[T](
            agent_type=self.agent_type,
            agent_id=self.agent_id,
            request_id=request_id,
            success=False,
            error_message=error.message,
            error_type=type(error).__name__,
            output=None,
            confidence_score=0.0,
            should_escalate=True,
            escalation_reasons=[f"Agent error: {error.message}"],
            tool_calls=self._tool_calls,
            token_usage=self._token_usage,
            started_at=started_at,
        )

    async def validate(
        self,
        request: Any,
        context: AgentContext,
    ) -> list[str]:
        """
        Validate inputs before execution.

        Override in subclasses for agent-specific validation.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        if request is None:
            errors.append("Request cannot be None")
        if not context.request_id:
            errors.append("Context must have request_id")
        return errors

    async def calculate_confidence(
        self,
        output: T,
        context: AgentContext,
    ) -> float:
        """
        Calculate confidence score for the output.

        Override in subclasses for agent-specific confidence calculation.
        Default implementation returns a moderate confidence.

        Returns:
            Confidence score between 0.0 and 1.0
        """
        return 0.75

    async def should_escalate(
        self,
        output: T,
        confidence: float,
        context: AgentContext,
    ) -> tuple[bool, list[str]]:
        """
        Determine if this request should be escalated to human review.

        Override in subclasses for agent-specific escalation logic.

        Returns:
            Tuple of (should_escalate, list of reasons)
        """
        settings = get_settings()
        reasons = []

        # Force escalation if requested
        if context.force_escalation:
            reasons.append("Escalation forced by context")
            return True, reasons

        # Escalate if below confidence threshold
        if confidence < settings.escalation_confidence_threshold:
            reasons.append(
                f"Confidence {confidence:.2f} below threshold "
                f"{settings.escalation_confidence_threshold}"
            )
            return True, reasons

        # Escalate if autonomy level requires it
        if self.autonomy_level == AgentAutonomyLevel.SHADOW:
            reasons.append("Agent in shadow mode")
            return True, reasons

        return False, reasons

    async def get_next_agent(
        self,
        output: T,
        context: AgentContext,
    ) -> AgentType | None:
        """
        Determine the next agent in the processing chain.

        Override in subclasses for agent-specific routing.

        Returns:
            Next agent type, or None if chain is complete
        """
        return None

    @retry(
        retry=retry_if_exception_type(anthropic.RateLimitError),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(3),
    )
    async def _call_llm(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        temperature: float = 0.0,
    ) -> anthropic.types.Message:
        """
        Call the Claude API with retry logic.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: System prompt override (uses self.system_prompt if None)
            temperature: Temperature for generation

        Returns:
            Claude Message response

        Raises:
            LLMError: If API call fails after retries
        """
        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system or self.system_prompt,
                messages=messages,  # type: ignore
                temperature=temperature,
            )

            # Track token usage
            self._token_usage = TokenUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            )

            return response

        except anthropic.APIStatusError as e:
            raise LLMError(
                agent_type=self.agent_type,
                llm_error=str(e),
                status_code=e.status_code,
            ) from e

    def _record_tool_call(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_output: Any = None,
        success: bool = True,
        error_message: str | None = None,
        duration_ms: int | None = None,
    ) -> ToolCall:
        """Record a tool call for observability."""
        tool_call = ToolCall(
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            success=success,
            error_message=error_message,
            duration_ms=duration_ms,
        )
        self._tool_calls.append(tool_call)
        return tool_call

    def _extract_text_content(self, response: anthropic.types.Message) -> str:
        """Extract text content from Claude response."""
        for block in response.content:
            if block.type == "text":
                return block.text
        return ""

    async def _parse_structured_output(
        self,
        response: anthropic.types.Message,
    ) -> T:
        """
        Parse structured output from Claude response.

        Expects Claude to return JSON matching the output_model schema.

        Returns:
            Parsed instance of output_model

        Raises:
            AgentValidationError: If parsing fails
        """
        import json

        text = self._extract_text_content(response)

        # Try to extract JSON from markdown code blocks if present
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            text = text[start:end].strip()

        try:
            data = json.loads(text)
            return self.output_model.model_validate(data)
        except (json.JSONDecodeError, Exception) as e:
            raise AgentValidationError(
                agent_type=self.agent_type,
                validation_errors=[f"Failed to parse structured output: {e}"],
            ) from e
