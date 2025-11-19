"""
Settings and configuration for URDB Tariff Viewer.

This module contains application settings, paths, and configuration management.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import os


class Settings:
    """Application settings and configuration."""
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent.parent
    SRC_DIR = BASE_DIR / "src"
    DATA_DIR = BASE_DIR / "data"
    TARIFFS_DIR = DATA_DIR / "tariffs"
    LOAD_PROFILES_DIR = DATA_DIR / "load_profiles"
    USER_DATA_DIR = DATA_DIR / "user_data"
    ARCHIVE_DIR = BASE_DIR / "archive"
    DOCS_DIR = BASE_DIR / "docs"
    TESTS_DIR = BASE_DIR / "tests"
    SCRIPTS_DIR = BASE_DIR / "scripts"
    
    # UI Settings
    DEFAULT_CHART_HEIGHT = 700
    DEFAULT_TEXT_SIZE = 12
    DEFAULT_FLAT_DEMAND_HEIGHT = 450
    
    # File Settings
    MAX_FILE_SIZE_MB = 50
    SUPPORTED_FILE_TYPES = ['.json', '.csv']
    
    # Application Settings
    APP_TITLE = "URDB Tariff Viewer"
    APP_VERSION = "2.0.0"
    
    @classmethod
    def get_streamlit_config(cls) -> Dict[str, Any]:
        """
        Get Streamlit-specific configuration.
        
        Returns:
            Dict[str, Any]: Streamlit page configuration
        """
        return {
            "page_title": cls.APP_TITLE,
            "layout": "wide",
            "initial_sidebar_state": "expanded",
            "page_icon": "⚡"
        }
    
    @classmethod
    def get_data_directories(cls) -> List[Path]:
        """
        Get list of data directories to search for files.
        
        Returns:
            List[Path]: List of data directory paths
        """
        return [
            cls.TARIFFS_DIR,
            cls.USER_DATA_DIR,
            cls.LOAD_PROFILES_DIR
        ]
    
    @classmethod
    def ensure_directories_exist(cls) -> None:
        """Ensure all required directories exist."""
        directories = [
            cls.DATA_DIR,
            cls.TARIFFS_DIR,
            cls.LOAD_PROFILES_DIR,
            cls.USER_DATA_DIR,
            cls.DOCS_DIR,
            cls.TESTS_DIR,
            cls.SCRIPTS_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_environment(cls) -> str:
        """
        Get the current environment.
        
        Returns:
            str: Environment name (development, production, etc.)
        """
        return os.getenv('ENVIRONMENT', 'development')
    
    @classmethod
    def is_development(cls) -> bool:
        """
        Check if running in development mode.
        
        Returns:
            bool: True if in development mode
        """
        return cls.get_environment().lower() in ['development', 'dev']
    
    @classmethod
    def get_debug_mode(cls) -> bool:
        """
        Check if debug mode is enabled.
        
        Returns:
            bool: True if debug mode is enabled
        """
        return os.getenv('DEBUG', 'false').lower() in ['true', '1', 'yes']
    
    @classmethod
    def get_openai_api_key(cls) -> Optional[str]:
        """
        Get OpenAI API key from Streamlit secrets or environment.
        
        Returns:
            Optional[str]: API key if configured, None otherwise
        """
        try:
            import streamlit as st
            # Try Streamlit secrets first (for production)
            if hasattr(st, 'secrets') and 'openai' in st.secrets:
                return st.secrets["openai"].get("api_key")
        except Exception:
            pass
        
        # Fallback to environment variable (for development)
        return os.getenv('OPENAI_API_KEY')
    
    @classmethod
    def get_openai_config(cls) -> Dict[str, Any]:
        """
        Get OpenAI configuration from Streamlit secrets or defaults.
        
        Returns:
            Dict[str, Any]: OpenAI configuration with api_key, model, max_tokens
        """
        config = {
            "api_key": None,
            "model": "gpt-4o",  # gpt-4o required for accurate schedule generation
            "max_tokens": 2000,
            "temperature": 0.1
        }
        
        try:
            import streamlit as st
            # Try to get from Streamlit secrets
            if hasattr(st, 'secrets') and 'openai' in st.secrets:
                config["api_key"] = st.secrets["openai"].get("api_key")
                config["model"] = st.secrets["openai"].get("model", "gpt-4o")  # Default to gpt-4o
                config["max_tokens"] = st.secrets["openai"].get("max_tokens", 2000)
                config["temperature"] = st.secrets["openai"].get("temperature", 0.1)
        except Exception:
            pass
        
        # Fallback to environment variable for API key
        if not config["api_key"]:
            config["api_key"] = os.getenv('OPENAI_API_KEY')
        
        return config
    
    @classmethod
    def has_openai_configured(cls) -> bool:
        """
        Check if OpenAI is properly configured.
        
        Returns:
            bool: True if API key is available
        """
        return cls.get_openai_api_key() is not None
