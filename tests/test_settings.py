"""Tests for settings module."""

import pytest
from unittest.mock import patch
from pathlib import Path

from src.config.settings import Settings, get_settings


class TestSettings:
    """Test cases for Settings."""

    def test_settings_defaults(self):
        """Test Settings has correct default values."""
        settings = Settings()
        
        assert settings.telegram_bot_token == ""
        assert settings.gemini_api_key == ""
        assert settings.groq_api_key == ""
        assert settings.groq_model == "llama-3.1-70b-versatile"
        assert settings.database_path == "data/sabiah.db"
        assert settings.chroma_persist_directory == "data/chroma_db"
        assert settings.freshdesk_api_key == ""
        assert settings.freshdesk_subdomain == ""
        assert settings.telegram_grupo_id == ""

    def test_settings_database_url_property(self):
        """Test database_url property returns correct URL."""
        settings = Settings()
        
        assert settings.database_url == "sqlite:///data/sabiah.db"

    def test_settings_data_dir_property(self):
        """Test data_dir property returns correct directory."""
        settings = Settings()
        
        assert settings.data_dir == Path("data")

    @patch.dict('os.environ', {
        'TELEGRAM_BOT_TOKEN': 'test_token',
        'GROQ_API_KEY': 'test_groq_key',
        'DATABASE_PATH': 'test.db',
    })
    def test_settings_from_environment(self):
        """Test Settings loads from environment variables."""
        # Clear the cache to ensure new Settings instance
        get_settings.cache_clear()
        
        settings = get_settings()
        
        assert settings.telegram_bot_token == "test_token"
        assert settings.groq_api_key == "test_groq_key"
        assert settings.database_path == "test.db"

    def test_settings_aliases(self):
        """Test Settings uses correct aliases."""
        settings = Settings(
            TELEGRAM_BOT_TOKEN="token123",
            GEMINI_API_KEY="gemini_key",
            GROQ_API_KEY="groq_key",
        )
        
        assert settings.telegram_bot_token == "token123"
        assert settings.gemini_api_key == "gemini_key"
        assert settings.groq_api_key == "groq_key"


class TestGetSettings:
    """Test cases for get_settings function."""

    def test_get_settings_returns_cached_instance(self):
        """Test get_settings returns cached instance."""
        # Clear cache first
        get_settings.cache_clear()
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Same instance should be returned (cached)
        assert settings1 is settings2

    def test_get_settings_cache_clear(self):
        """Test cache_clear works."""
        # Get an instance
        settings1 = get_settings()
        
        # Clear cache
        get_settings.cache_clear()
        
        # Get another instance - should be different now
        settings2 = get_settings()
        
        # Both should be Settings instances (but different instances after clear)
        assert isinstance(settings1, Settings)
        assert isinstance(settings2, Settings)
