"""
Centralized configuration management using Pydantic Settings.

Supports configuration from:
1. Environment variables
2. .env files
3. YAML config files
4. Default values
"""
from pathlib import Path
from typing import Optional, Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseSettings):
    """LLM provider configuration."""

    # Provider selection
    provider: Literal["ollama", "anthropic"] = Field(
        default="ollama",
        description="LLM provider to use"
    )

    # Ollama configuration
    ollama_model: str = Field(
        default="frob/qwen3-coder-next",
        description="Ollama model name"
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434/v1",
        description="Ollama API base URL"
    )
    ollama_timeout: float = Field(
        default=300.0,
        description="Ollama request timeout in seconds"
    )

    # Anthropic configuration
    anthropic_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Anthropic model name"
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key (or set ANTHROPIC_API_KEY env var)"
    )

    # General LLM parameters
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    max_tokens: int = Field(
        default=4096,
        gt=0,
        description="Maximum tokens to generate"
    )
    context_length: int = Field(
        default=32768,
        gt=0,
        description="Model context window size"
    )

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )


class WorkspaceConfig(BaseSettings):
    """Workspace and file paths configuration."""

    project_root: Path = Field(
        default=Path("/home/korety/Project/DR_2_Podcast"),
        description="Root directory of the project to work on"
    )
    sandbox_dir: Optional[Path] = Field(
        default=None,
        description="Sandbox directory for temporary files"
    )
    logs_path: Path = Field(
        default=Path("/home/korety/coding-agent/logs"),
        description="Directory for log files"
    )

    @field_validator("project_root", "logs_path", mode="before")
    @classmethod
    def expand_path(cls, v):
        """Expand ~ and make path absolute."""
        if isinstance(v, str):
            return Path(v).expanduser().absolute()
        return v

    @field_validator("sandbox_dir", mode="before")
    @classmethod
    def expand_optional_path(cls, v):
        """Expand optional path."""
        if v is None:
            return None
        if isinstance(v, str):
            return Path(v).expanduser().absolute()
        return v

    model_config = SettingsConfigDict(
        env_prefix="WORKSPACE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )


class DatabaseConfig(BaseSettings):
    """Database configuration for task persistence."""

    db_path: Path = Field(
        default=Path("/home/korety/coding-agent/tasks.db"),
        description="SQLite database file path"
    )
    backup_on_start: bool = Field(
        default=True,
        description="Create backup of database on startup"
    )
    auto_checkpoint_interval: int = Field(
        default=100,
        gt=0,
        description="Number of operations before auto-checkpoint"
    )

    @field_validator("db_path", mode="before")
    @classmethod
    def expand_db_path(cls, v):
        """Expand ~ and make path absolute."""
        if isinstance(v, str):
            return Path(v).expanduser().absolute()
        return v

    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )


class OrchestrationConfig(BaseSettings):
    """Orchestration and agent coordination settings."""

    max_iterations: int = Field(
        default=10,
        gt=0,
        le=100,
        description="Maximum iterations for agent tasks"
    )
    enable_resume: bool = Field(
        default=True,
        description="Enable resuming interrupted tasks"
    )
    auto_save_interval: int = Field(
        default=5,
        gt=0,
        description="Save state every N operations"
    )

    # Hierarchical agent roles
    pm_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Project Manager model (high-level coordination)"
    )
    lead_model: str = Field(
        default="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        description="Project Lead model (planning and review)"
    )
    lead_base_url: str = Field(
        default="http://localhost:8000/v1",
        description="Base URL for Lead model (vLLM server)"
    )
    member_model: str = Field(
        default="frob/qwen3-coder-next",
        description="Project Member model (implementation)"
    )

    model_config = SettingsConfigDict(
        env_prefix="ORCH_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )


class SecurityConfig(BaseSettings):
    """Security and sandboxing settings."""

    enable_sandbox: bool = Field(
        default=False,
        description="Enable Docker sandbox for code execution"
    )
    docker_image: str = Field(
        default="python:3.11-slim",
        description="Docker image for sandboxed execution"
    )
    max_execution_time: int = Field(
        default=300,
        gt=0,
        description="Maximum execution time in seconds"
    )
    allowed_commands: list[str] = Field(
        default_factory=lambda: ["python3", "pytest", "pip", "git"],
        description="Allowed commands in sandbox"
    )

    model_config = SettingsConfigDict(
        env_prefix="SECURITY_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )


class AppConfig(BaseSettings):
    """Main application configuration that aggregates all sub-configs."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    workspace: WorkspaceConfig = Field(default_factory=WorkspaceConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    orchestration: OrchestrationConfig = Field(default_factory=OrchestrationConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    # Global settings
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "AppConfig":
        """
        Load configuration from YAML file and merge with environment variables.

        Args:
            yaml_path: Path to YAML configuration file

        Returns:
            AppConfig instance with merged configuration
        """
        import yaml

        if not yaml_path.exists():
            raise FileNotFoundError(f"Config file not found: {yaml_path}")

        with open(yaml_path, 'r') as f:
            yaml_data = yaml.safe_load(f)

        # Create config from YAML data
        # Environment variables will override YAML values
        return cls(
            llm=LLMConfig(**yaml_data.get("llm", {})),
            workspace=WorkspaceConfig(**yaml_data.get("workspace", {})),
            orchestration=OrchestrationConfig(**yaml_data.get("orchestration", {})),
        )

    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        self.workspace.logs_path.mkdir(parents=True, exist_ok=True)
        if self.workspace.sandbox_dir:
            self.workspace.sandbox_dir.mkdir(parents=True, exist_ok=True)
        # Create parent directory for database
        self.database.db_path.parent.mkdir(parents=True, exist_ok=True)


# Singleton instance for easy access
_config: Optional[AppConfig] = None


def get_config(config_path: Optional[Path] = None, force_reload: bool = False) -> AppConfig:
    """
    Get the application configuration singleton.

    Args:
        config_path: Optional path to YAML config file
        force_reload: Force reload configuration

    Returns:
        AppConfig instance
    """
    global _config

    if _config is None or force_reload:
        if config_path and config_path.exists():
            _config = AppConfig.from_yaml(config_path)
        else:
            _config = AppConfig()

        # Ensure directories exist
        _config.ensure_directories()

    return _config


def reset_config():
    """Reset the configuration singleton (useful for testing)."""
    global _config
    _config = None
