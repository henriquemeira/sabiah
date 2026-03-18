"""Canais de Helpdesk."""

from src.services.helpdesk.base import (
    CanalHelpdesk,
    StatusTicket,
    PrioridadeTicket,
    TicketInfo,
    CriarTicketRequest,
)
from src.services.helpdesk.freshdesk import FreshdeskCanal
from src.services.helpdesk.factory import HelpdeskFactory

__all__ = [
    "CanalHelpdesk",
    "StatusTicket",
    "PrioridadeTicket",
    "TicketInfo",
    "CriarTicketRequest",
    "FreshdeskCanal",
    "HelpdeskFactory",
]
