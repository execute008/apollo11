"""Application settings and configuration."""

import os
from pathlib import Path
from typing import Optional
import yaml
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment and config file."""

    # Apollo.io Configuration
    apollo_api_key: str = Field(..., env="APOLLO_API_KEY")
    apollo_base_url: str = Field(
        default="https://api.apollo.io/v1",
        env="APOLLO_BASE_URL"
    )

    # ElevenLabs Configuration
    elevenlabs_api_key: str = Field(..., env="ELEVENLABS_API_KEY")
    elevenlabs_agent_id: Optional[str] = Field(None, env="ELEVENLABS_AGENT_ID")
    elevenlabs_base_url: str = Field(
        default="https://api.elevenlabs.io/v1",
        env="ELEVENLABS_BASE_URL"
    )

    # Twilio Configuration (optional)
    twilio_account_sid: Optional[str] = Field(None, env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: Optional[str] = Field(None, env="TWILIO_AUTH_TOKEN")
    twilio_phone_number: Optional[str] = Field(None, env="TWILIO_PHONE_NUMBER")

    # Orchestrator Configuration
    max_concurrent_calls: int = Field(default=5, env="MAX_CONCURRENT_CALLS")
    call_retry_attempts: int = Field(default=3, env="CALL_RETRY_ATTEMPTS")
    call_timeout_seconds: int = Field(default=300, env="CALL_TIMEOUT_SECONDS")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Database
    database_url: str = Field(
        default="sqlite:///calls.db",
        env="DATABASE_URL"
    )

    # Config file path
    config_file: Path = Field(
        default=PROJECT_ROOT / "config.yaml",
        env="CONFIG_FILE"
    )

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False


def load_yaml_config(config_path: Path) -> dict:
    """Load YAML configuration file."""
    if not config_path.exists():
        return {}

    with open(config_path, "r") as f:
        return yaml.safe_load(f) or {}


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get singleton settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def get_config() -> dict:
    """Get full configuration including YAML config."""
    settings = get_settings()
    yaml_config = load_yaml_config(settings.config_file)
    return yaml_config
