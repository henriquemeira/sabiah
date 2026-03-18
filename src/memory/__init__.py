"""Módulo de Memória do Sabiah.

Este módulo implementa as três camadas de memória do sistema:
- Memória Geral: Base de conhecimento (documentação, FAQs, tutoriais)
- Memória do Cliente: Histórico de conversas e interações
- Memória do Domínio: Dados específicos do ambiente do cliente
"""

from src.memory.memoria_geral import MemoriaGeral, get_memoria_geral
from src.memory.memoria_cliente import MemoriaCliente
from src.memory.memoria_dominio import MemoriaDominio
from src.memory.servico_contexto import ServicoContexto, ContextoAtendimento

__all__ = [
    "MemoriaGeral",
    "get_memoria_geral",
    "MemoriaCliente",
    "MemoriaDominio",
    "ServicoContexto",
    "ContextoAtendimento",
]
