"""
Configuration and settings management for DSA AutoGen.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field


class Settings(BaseModel):
    # LLM Settings
    model_name: str = Field(default_factory=lambda: os.getenv("MODEL_NAME", "gpt-4o-mini"))
    api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    base_url: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", None))
    temperature: float = Field(default_factory=lambda: float(os.getenv("TEMPERATURE", "0.1")))

    # Execution & Self-Healing
    max_retries: int = Field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    execution_timeout_sec: float = Field(default_factory=lambda: float(os.getenv("EXECUTION_TIMEOUT_SEC", "8.0")))

    # C++ Compiler Settings
    cpp_compiler: str = Field(default_factory=lambda: os.getenv("CPP_COMPILER", "g++"))
    cpp_standard: str = Field(default_factory=lambda: os.getenv("CPP_STANDARD", "c++17"))
    cpp_opt_level: str = Field(default_factory=lambda: os.getenv("CPP_OPT_LEVEL", "-O2"))
    cpp_flags: List[str] = Field(default_factory=lambda: ["-Wall", "-Wextra"])

    # Directory Paths
    workspace_dir: Path = Field(
        default_factory=lambda: Path(os.getenv("DSA_WORKSPACE_DIR", "./.dsa_workspace")).resolve()
    )


_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
        _settings_instance.workspace_dir.mkdir(parents=True, exist_ok=True)
    return _settings_instance

