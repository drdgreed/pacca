import os
from abc import ABC, abstractmethod
from typing import Type, TypeVar, Any, Dict
from pydantic import BaseModel
from anthropic import AsyncAnthropic

T = TypeVar("T", bound=BaseModel)

class AgentConfig(BaseModel):
    # CHANGED: Using your verified working model ID
    model: str = "claude-sonnet-4-5-20250929"
    temperature: float = 0.0
    max_tokens: int = 4096

class BaseAgent(ABC):
    def __init__(self, config: AgentConfig = AgentConfig()):
        self.config = config
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
    @property
    @abstractmethod
    def name(self) -> str: pass

    @property
    @abstractmethod
    def system_prompt(self) -> str: pass

    async def execute(self, user_input: str, response_model: Type[T]) -> T:
        messages = [{"role": "user", "content": user_input}]
        
        # Tool definition to enforce JSON structure
        tool_def = {
            "name": "submit_result",
            "description": f"Submit result for {self.name}",
            "input_schema": response_model.model_json_schema()
        }

        try:
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=self.system_prompt,
                messages=messages,
                tools=[tool_def],
                tool_choice={"type": "tool", "name": "submit_result"}
            )

            for content in response.content:
                if content.type == "tool_use":
                    return response_model.model_validate(content.input)
            
            # Fallback (shouldn't happen with correct tool use)
            raise ValueError("Agent failed to use structured tool")
            
        except Exception as e:
            print(f"Agent {self.name} Error: {e}")
            raise e
