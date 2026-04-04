"""
Application settings and configuration management.

Uses Pydantic Settings for type-safe environment variable handling
with validation and sensible defaults.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via environment variables.
    Sensitive values use SecretStr to prevent accidental logging.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================================================
    # Application
    # ==========================================================================
    app_name: str = Field(default="pacca", description="Application name")
    app_env: Literal["development", "staging", "production", "test"] = Field(
        default="development", description="Environment"
    )
    debug: bool = Field(default=True, description="Debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )

    # ==========================================================================
    # API Keys
    # ==========================================================================
    anthropic_api_key: SecretStr = Field(
        default=SecretStr("sk-ant-placeholder"),
        description="Anthropic API key for Claude",
    )

    # Optional: Pinecone for production vector store
    pinecone_api_key: SecretStr | None = Field(
        default=None, description="Pinecone API key"
    )
    pinecone_environment: str | None = Field(
        default=None, description="Pinecone environment"
    )
    pinecone_index_name: str = Field(
        default="pacca-guidelines", description="Pinecone index name"
    )

    # ==========================================================================
    # Database
    # ==========================================================================
    database_url: str = Field(
        default="sqlite+aiosqlite:///./pacca.db",
        description="Database connection URL",
    )

    # Connection pool settings
    db_pool_size: int = Field(default=5, ge=1, le=20, description="Connection pool size")
    db_max_overflow: int = Field(default=10, ge=0, le=50, description="Max overflow connections")
    db_pool_timeout: int = Field(default=30, ge=5, le=120, description="Pool timeout seconds")

    # ==========================================================================
    # Redis
    # ==========================================================================
    redis_url: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )
    redis_enabled: bool = Field(default=False, description="Enable Redis caching")

    # ==========================================================================
    # Security
    # ==========================================================================
    secret_key: SecretStr = Field(
        default=SecretStr("dev-secret-key-change-in-production-min-32-characters"),
        description="Secret key for JWT and session encryption",
    )
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ==========================================================================
    # LLM / Agent Configuration
    # ==========================================================================
    default_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Default Claude model for agents",
    )
    max_tokens: int = Field(
        default=4096, ge=256, le=8192, description="Max tokens for responses"
    )
    agent_timeout: int = Field(
        default=60, ge=10, le=300, description="Agent timeout in seconds"
    )

    # Confidence thresholds
    auto_approve_confidence_threshold: float = Field(
        default=0.85,
        ge=0.5,
        le=1.0,
        description="Confidence threshold for autonomous approval",
    )
    escalation_confidence_threshold: float = Field(
        default=0.75,
        ge=0.3,
        le=1.0,
        description="Confidence threshold below which to escalate",
    )

    # ==========================================================================
    # Clinical Settings
    # ==========================================================================
    complexity_auto_approve_max: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Maximum complexity level for auto-approval",
    )
    complexity_specialist_review_min: int = Field(
        default=4,
        ge=1,
        le=5,
        description="Minimum complexity level requiring specialist",
    )
    high_cost_threshold: int = Field(
        default=100000,
        ge=0,
        description="Cost threshold for medical director review",
    )

    # ==========================================================================
    # Observability
    # ==========================================================================
    enable_tracing: bool = Field(default=True, description="Enable agent tracing")
    metrics_enabled: bool = Field(default=True, description="Enable metrics endpoint")

    # OpenTelemetry configuration
    # When otel_endpoint is set, traces are exported to that collector
    # (Langfuse, Jaeger, Tempo, etc.). When None, traces are logged locally only.
    otel_endpoint: str | None = Field(
        default=None,
        description="OpenTelemetry collector endpoint (e.g. http://localhost:4318)",
    )
    otel_service_name: str = Field(
        default="pacca",
        description="Service name reported in OTel traces",
    )
    otel_enabled: bool = Field(
        default=True,
        description="Enable OpenTelemetry span instrumentation",
    )

    # Retry configuration for LLM API calls
    # These values control tenacity's exponential backoff behaviour.
    llm_retry_max_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of LLM call attempts before giving up",
    )
    llm_retry_wait_min_seconds: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Minimum wait seconds between retries (exponential base)",
    )
    llm_retry_wait_max_seconds: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        description="Maximum wait seconds between retries (exponential cap)",
    )

    # ==========================================================================
    # Rate Limiting
    # ==========================================================================
    rate_limit_rpm: int = Field(
        default=60, ge=1, le=1000, description="Requests per minute limit"
    )

    # ==========================================================================
    # Feature Flags
    # ==========================================================================
    enable_autonomous_decisions: bool = Field(
        default=True, description="Allow autonomous agent decisions"
    )
    enable_rag: bool = Field(
        default=True, description="Enable RAG-based guideline retrieval"
    )
    demo_mode: bool = Field(
        default=True, description="Use mock EHR data for demo"
    )

    # ==========================================================================
    # Computed Properties
    # ==========================================================================
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"

    @property
    def use_pinecone(self) -> bool:
        """Check if Pinecone should be used instead of local ChromaDB."""
        return self.pinecone_api_key is not None and self.pinecone_environment is not None


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    Clear cache with get_settings.cache_clear() if needed.
    """
    return Settings()


# Convenience function for common settings access
def get_anthropic_api_key() -> str:
    """Get the Anthropic API key as a string."""
    return get_settings().anthropic_api_key.get_secret_value()
