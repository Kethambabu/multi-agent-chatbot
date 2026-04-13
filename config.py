"""
Configuration management for the multi-modal agent.

This module loads and manages configuration from environment variables.
Uses python-dotenv to load .env file for local development.

IMPORTANT: Never hardcode API keys. Always use environment variables.
"""

import os
import logging
from typing import Optional
from pathlib import Path

from dotenv import load_dotenv


# Configure logging
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent
DOTENV_PATH = PROJECT_ROOT / ".env"
DOTENV_TEMPLATE_PATH = PROJECT_ROOT / ".env.template"
_env_loaded = False


def _load_environment_once() -> None:
    """Load .env exactly once from project root.

    IMPORTANT:
    - Loads only `.env`
    - Never loads `.env.template`
    - Uses the required API call shape: load_dotenv(dotenv_path=".env")
    """
    global _env_loaded
    if _env_loaded:
        return

    if not DOTENV_PATH.exists():
        logger.warning("No .env found at %s; using existing process environment", DOTENV_PATH)
        _env_loaded = True
        return

    original_cwd = Path.cwd()
    try:
        os.chdir(PROJECT_ROOT)
        load_dotenv(dotenv_path=".env", override=False)
        logger.info("Loaded environment from %s", DOTENV_PATH)
    finally:
        os.chdir(original_cwd)

    if DOTENV_TEMPLATE_PATH.exists():
        logger.debug("Detected .env.template at %s (ignored at runtime)", DOTENV_TEMPLATE_PATH)

    _env_loaded = True


_load_environment_once()


class Config:
    """Configuration class for managing application settings.
    
    All configuration is loaded from environment variables.
    Never hardcodes sensitive data like API keys.
    
    Required Environment Variables:
    - HF_API_KEY: Hugging Face API token (https://huggingface.co/settings/tokens)

    
    Optional Environment Variables:
    - HF_TIMEOUT: API timeout in seconds (default: 60)
    - HF_MAX_RETRIES: Max API retries (default: 3)
    - HF_MODEL_LOADING_TIMEOUT: Model loading timeout in seconds (default: 180)
    - API_HOST: Server host (default: 0.0.0.0)
    - API_PORT: Server port (default: 8000)
    - API_RELOAD: Auto-reload on code changes (default: false)
    - API_WORKERS: Number of worker processes (default: 4)
    - DEBUG: Debug mode (default: false)
    - MODEL_NAME: Model name (default: multi-modal-agent)
    - MAX_IMAGE_SIZE: Max image upload size in bytes (default: 52428800)
    - MAX_BATCH_SIZE: Max batch size (default: 100)
    """
    
    def __init__(self):
        """Initialize configuration from environment variables.
        
        Loads all settings from environment variables with sensible defaults.
        Validates that required API key is present.
        
        Raises:
            ValueError: If HF_API_KEY is not set
        """
        # Hugging Face API settings
        self.hf_api_key: Optional[str] = os.getenv("HF_API_KEY")
        
        self.project_root: Path = PROJECT_ROOT
        
        # Validate API keys exist
        if not self.hf_api_key:
            logger.error(
                "HF_API_KEY environment variable is not set. "
                "Please set it before running the application. "
                "Get your token from: https://huggingface.co/settings/tokens"
            )
            raise ValueError(
                "HF_API_KEY environment variable is required. "
                "Set it in your .env file or system environment. "
                "Get your token from: https://huggingface.co/settings/tokens"
            )
        
        logger.info(
            "Environment debug: HF_API_KEY_loaded=%s, cwd=%s, project_root=%s",
            bool(self.hf_api_key),
            Path.cwd(),
            self.project_root
        )
        
        # API timeout and retry settings
        self.timeout: int = int(os.getenv("HF_TIMEOUT", "60"))  # Increased from 30 to 60
        self.max_retries: int = int(os.getenv("HF_MAX_RETRIES", "3"))
        self.retry_backoff_factor: float = float(os.getenv("HF_RETRY_BACKOFF_FACTOR", "0.3"))
        self.model_loading_timeout: int = int(os.getenv("HF_MODEL_LOADING_TIMEOUT", "180"))  # Increased from 120 to 180
        
        # Application settings
        self.model_name: str = os.getenv("MODEL_NAME", "multi-modal-agent")
        self.debug: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
        
        # FastAPI server settings
        self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
        self.api_port: int = int(os.getenv("API_PORT", "8000"))
        self.api_reload: bool = os.getenv("API_RELOAD", "false").lower() in ("true", "1", "yes")
        self.api_workers: int = int(os.getenv("API_WORKERS", "4"))
        
        # Upload and processing limits
        self.max_image_size: int = int(os.getenv("MAX_IMAGE_SIZE", "52428800"))  # 50MB
        self.max_batch_size: int = int(os.getenv("MAX_BATCH_SIZE", "100"))
        
        logger.info(
            "Configuration loaded successfully. "
            "API: %s:%d, Model: %s, Debug: %s",
            self.api_host,
            self.api_port,
            self.model_name,
            self.debug
        )
    
    def validate(self) -> bool:
        """Validate configuration settings.
        
        This method is called automatically in __init__ to ensure
        all required values are present and valid.
        
        Returns:
            True if validation passes
            
        Raises:
            ValueError: If any validation checks fail
        """
        # API key is already validated in __init__
        
        # Validate numeric ranges
        if self.timeout <= 0:
            raise ValueError(f"HF_TIMEOUT must be positive, got {self.timeout}")
        
        if self.max_retries < 0:
            raise ValueError(f"HF_MAX_RETRIES must be non-negative, got {self.max_retries}")
        
        if self.api_port <= 0 or self.api_port > 65535:
            raise ValueError(f"API_PORT must be between 1-65535, got {self.api_port}")
        
        if self.api_workers <= 0:
            raise ValueError(f"API_WORKERS must be positive, got {self.api_workers}")
        
        if self.max_image_size <= 0:
            raise ValueError(f"MAX_IMAGE_SIZE must be positive, got {self.max_image_size}")
        
        if self.max_batch_size <= 0:
            raise ValueError(f"MAX_BATCH_SIZE must be positive, got {self.max_batch_size}")
        
        logger.info("Configuration validation passed")
        return True
    
    def to_dict(self) -> dict:
        """Convert config to dictionary, excluding sensitive data.
        
        Returns:
            Dictionary with configuration (API key excluded for security)
        """
        return {
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "model_loading_timeout": self.model_loading_timeout,
            "model_name": self.model_name,
            "debug": self.debug,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "api_reload": self.api_reload,
            "api_workers": self.api_workers,
            "max_image_size": self.max_image_size,
            "max_batch_size": self.max_batch_size
        }


# Global config instance (lazy loaded)
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance.
    
    This is a singleton pattern that ensures only one Config instance
    is created and reused throughout the application.
    
    Returns:
        Config: The global configuration instance
        
    Raises:
        ValueError: If HF_API_KEY is not set
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = Config()
        _config_instance.validate()
        logger.info("Global configuration instance initialized and validated")
    
    return _config_instance


def print_config_info() -> None:
    """Print configuration information (without sensitive data).
    
    Useful for debugging and confirming settings are loaded correctly.
    """
    config = get_config()
    config_dict = config.to_dict()
    
    logger.info("=== Application Configuration ===")
    for key, value in config_dict.items():
        logger.info(f"{key}: {value}")
    logger.info("===================================")

