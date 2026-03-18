"""Factory para criação de provedores de IA."""

from typing import Optional

from src.ai.base import ProvedorIA, TipoProvedor
from src.ai.gemini import GeminiProvedor
from src.config import get_settings

settings = get_settings()


def criar_provedor(tipo: Optional[TipoProvedor] = None) -> ProvedorIA:
    """
    Cria uma instância de provedor de IA.
    
    Args:
        tipo: Tipo de provedor (se None, usa o padrão: GEMINI)
        
    Returns:
        Instância do provedor de IA
        
    Raises:
        ValueError: Se o tipo de provedor for desconhecido
    """
    if tipo is None:
        tipo = TipoProvedor.GEMINI
    
    if tipo == TipoProvedor.GEMINI:
        return GeminiProvedor()
    
    raise ValueError(f"Provedor desconhecido: {tipo}")


# Instância global do provedor
_provedor: Optional[ProvedorIA] = None


def get_provedor() -> ProvedorIA:
    """Retorna a instância global do provedor de IA."""
    global _provedor
    if _provedor is None:
        _provedor = criar_provedor()
    return _provedor
