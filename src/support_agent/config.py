"""Application settings loaded from environment variables (.env in development)."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    """Immutable, validated application settings."""

    # repr=False keeps the secret out of print() and log output.
    gemini_api_key: str = field(repr=False)
    gemini_model: str = DEFAULT_GEMINI_MODEL


def load_settings() -> Settings:
    """Load settings from the environment, failing fast if required values are missing."""
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ConfigError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and fill in your key."
        )

    # `or` also covers a variable that exists but is empty (e.g. "GEMINI_MODEL=").
    model = os.getenv("GEMINI_MODEL", "").strip() or DEFAULT_GEMINI_MODEL

    return Settings(gemini_api_key=api_key, gemini_model=model)
