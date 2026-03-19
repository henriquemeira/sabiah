"""Tests for helpdesk factory module."""

import pytest
from unittest.mock import MagicMock, patch

from src.services.helpdesk.factory import HelpdeskFactory


class TestHelpdeskFactory:
    """Test cases for HelpdeskFactory."""

    def setup_method(self):
        """Reset the factory before each test."""
        HelpdeskFactory.reset()

    def test_get_canal_freshdesk_valido(self):
        """Test getting freshdesk canal when configured."""
        with patch('src.services.helpdesk.factory.FreshdeskCanal') as mock_freshdesk:
            # Setup mock
            mock_canal = MagicMock()
            mock_canal.validar_configuracao.return_value = True
            mock_freshdesk.return_value = mock_canal

            # Call the factory
            canal = HelpdeskFactory.get_canal("freshdesk")

            # Assertions
            assert canal is not None
            mock_freshdesk.assert_called_once()
            mock_canal.validar_configuracao.assert_called_once()

    def test_get_canal_freshdesk_invalido(self):
        """Test getting freshdesk canal when not configured."""
        with patch('src.services.helpdesk.factory.FreshdeskCanal') as mock_freshdesk:
            # Setup mock
            mock_canal = MagicMock()
            mock_canal.validar_configuracao.return_value = False
            mock_freshdesk.return_value = mock_canal

            # Call the factory
            canal = HelpdeskFactory.get_canal("freshdesk")

            # Assertions
            assert canal is None
            mock_freshdesk.assert_called_once()
            mock_canal.validar_configuracao.assert_called_once()

    def test_get_canal_desconhecido(self):
        """Test getting canal with unknown type."""
        canal = HelpdeskFactory.get_canal("unknown_type")

        # Should return None for unknown types
        assert canal is None

    def test_get_canal_cached(self):
        """Test that canal is cached after first creation."""
        with patch('src.services.helpdesk.factory.FreshdeskCanal') as mock_freshdesk:
            # Setup mock
            mock_canal = MagicMock()
            mock_canal.validar_configuracao.return_value = True
            mock_freshdesk.return_value = mock_canal

            # Call the factory twice
            canal1 = HelpdeskFactory.get_canal("freshdesk")
            canal2 = HelpdeskFactory.get_canal("freshdesk")

            # Assertions - same instance should be returned
            assert canal1 is canal2
            # Freshdesk should only be created once (cached)
            assert mock_freshdesk.call_count == 1

    def test_reset_clears_cache(self):
        """Test that reset clears the cached canal."""
        with patch('src.services.helpdesk.factory.FreshdeskCanal') as mock_freshdesk:
            # Setup mock
            mock_canal = MagicMock()
            mock_canal.validar_configuracao.return_value = True
            mock_freshdesk.return_value = mock_canal

            # First call - creates the canal
            canal1 = HelpdeskFactory.get_canal("freshdesk")

            # Reset the factory
            HelpdeskFactory.reset()

            # Second call - should create a new canal
            canal2 = HelpdeskFactory.get_canal("freshdesk")

            # Freshdesk should be called twice (once for each get_canal after reset)
            assert mock_freshdesk.call_count == 2

    def test_get_canal_tipo_default(self):
        """Test that default tipo is freshdesk."""
        with patch('src.services.helpdesk.factory.FreshdeskCanal') as mock_freshdesk:
            # Setup mock
            mock_canal = MagicMock()
            mock_canal.validar_configuracao.return_value = True
            mock_freshdesk.return_value = mock_canal

            # Call without specifying tipo
            canal = HelpdeskFactory.get_canal()

            # Should default to freshdesk
            mock_freshdesk.assert_called_once()
            assert canal is not None
