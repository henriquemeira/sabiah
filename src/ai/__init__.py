"""Módulo de Inteligência Artificial do Sabiah."""

from src.ai.base import ProvedorIA, RespostaIA, TipoProvedor
from src.ai.factory import criar_provedor, get_provedor
from src.ai.gemini import GeminiProvedor

__all__ = [
    "ProvedorIA",
    "RespostaIA",
    "TipoProvedor",
    "GeminiProvedor",
    "criar_provedor",
    "get_provedor",
]
