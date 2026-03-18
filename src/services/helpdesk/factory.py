"""Factory para criar instâncias de canais de helpdesk."""

import logging
from typing import Optional

from src.services.helpdesk.base import CanalHelpdesk
from src.services.helpdesk.freshdesk import FreshdeskCanal

logger = logging.getLogger(__name__)


class HelpdeskFactory:
    """Factory para criar instâncias de canais de helpdesk."""
    
    _canal: Optional[CanalHelpdesk] = None
    
    @classmethod
    def get_canal(cls, tipo: str = "freshdesk") -> Optional[CanalHelpdesk]:
        """
        Retorna uma instância do canal de helpdesk.
        
        Args:
            tipo: Tipo de canal ("freshdesk")
            
        Returns:
            Instância do canal ou None se não configurado
        """
        if cls._canal is not None:
            return cls._canal
        
        if tipo == "freshdesk":
            canal = FreshdeskCanal()
            if canal.validar_configuracao():
                cls._canal = canal
                return canal
            else:
                logger.warning("⚠️ Freshdesk não está configurado corretamente")
                return None
        
        logger.warning(f"⚠️ Tipo de helpdesk desconhecido: {tipo}")
        return None
    
    @classmethod
    def reset(cls) -> None:
        """Reseta a instância cacheada (útil para testes)."""
        cls._canal = None
