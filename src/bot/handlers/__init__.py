"""Handlers do bot do Telegram."""

from src.bot.handlers.mensagens import (
    criar_menu_escalonamento,
    mostrar_opcoes_escalonamento,
    tratar_callback_escalonamento,
)

__all__ = [
    "criar_menu_escalonamento",
    "mostrar_opcoes_escalonamento",
    "tratar_callback_escalonamento",
    "get_handlers_escalonamento",
]
