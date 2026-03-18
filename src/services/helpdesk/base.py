"""Interface abstrata para canais de Helpdesk."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class StatusTicket(str, Enum):
    """Status de um ticket."""
    ABERTO = "aberto"
    PENDENTE = "pendente"
    RESOLVIDO = "resolvido"
    FECHADO = "fechado"


class PrioridadeTicket(str, Enum):
    """Prioridade de um ticket."""
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


@dataclass
class TicketInfo:
    """Informações de um ticket retornado pelo helpdesk."""
    id_externo: str
    status: StatusTicket
    prioridade: PrioridadeTicket
    assunto: str
    descricao: str
    url: Optional[str] = None
    data_criacao: Optional[str] = None
    data_atualizacao: Optional[str] = None


@dataclass
class CriarTicketRequest:
    """Request para criar um novo ticket."""
    assunto: str
    descricao: str
    prioridade: PrioridadeTicket = PrioridadeTicket.MEDIA
    email_cliente: Optional[str] = None
    nome_cliente: Optional[str] = None
    telefone_cliente: Optional[str] = None
    tags: Optional[list[str]] = None


class CanalHelpdesk(ABC):
    """Interface abstrata para canais de helpdesk."""
    
    @abstractmethod
    def criar_ticket(self, request: CriarTicketRequest) -> TicketInfo:
        """
        Cria um novo ticket no helpdesk.
        
        Args:
            request: Dados do ticket a ser criado
            
        Returns:
            TicketInfo com informações do ticket criado
            
        Raises:
            Exception: Se houver erro ao criar o ticket
        """
        pass
    
    @abstractmethod
    def consultar_status(self, ticket_id: str) -> TicketInfo:
        """
        Consulta o status de um ticket.
        
        Args:
            ticket_id: ID do ticket no sistema externo
            
        Returns:
            TicketInfo com informações atualizadas do ticket
            
        Raises:
            Exception: Se o ticket não for encontrado ou houver erro
        """
        pass
    
    @abstractmethod
    def listar_tickets(
        self,
        email_cliente: Optional[str] = None,
        status: Optional[StatusTicket] = None,
        limite: int = 10,
    ) -> list[TicketInfo]:
        """
        Lista tickets de um cliente.
        
        Args:
            email_cliente: E-mail do cliente para filtrar
            status: Status para filtrar
            limite: Número máximo de tickets a retornar
            
        Returns:
            Lista de TicketInfo
        """
        pass
    
    @abstractmethod
    def validar_configuracao(self) -> bool:
        """
        Valida se a configuração do canal está correta.
        
        Returns:
            True se a configuração for válida
        """
        pass
