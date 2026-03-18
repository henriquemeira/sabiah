"""Integração com Freshdesk."""

import logging
from typing import Optional

import requests

from src.config import get_settings
from src.services.helpdesk.base import (
    CanalHelpdesk,
    StatusTicket,
    PrioridadeTicket,
    TicketInfo,
    CriarTicketRequest,
)

logger = logging.getLogger(__name__)


class FreshdeskCanal(CanalHelpdesk):
    """
    Implementação de canal Freshdesk.
    
    Requer:
    - FRESHDESK_API_KEY: Chave da API do Freshdesk
    - FRESHDESK_SUBDOMAIN: Subdomínio da empresa no Freshdesk
    """
    
    # Mapeamento de status do Freshdesk
    FRESHDESK_STATUS = {
        StatusTicket.ABERTO: 2,  # Open
        StatusTicket.PENDENTE: 3,  # Pending
        StatusTicket.RESOLVIDO: 4,  # Resolved
        StatusTicket.FECHADO: 5,  # Closed
    }
    
    # Mapeamento reverso
    STATUS_FRESHDESK = {v: k for k, v in FRESHDESK_STATUS.items()}
    
    # Mapeamento de prioridade do Freshdesk
    FRESHDESK_PRIORIDADE = {
        PrioridadeTicket.BAIXA: 1,
        PrioridadeTicket.MEDIA: 2,
        PrioridadeTicket.ALTA: 3,
        PrioridadeTicket.CRITICA: 4,
    }
    
    # Mapeamento reverso
    PRIORIDADE_FRESHDESK = {v: k for k, v in FRESHDESK_PRIORIDADE.items()}
    
    def __init__(self):
        """Inicializa o canal Freshdesk."""
        self.settings = get_settings()
        self.api_key = self.settings.freshdesk_api_key
        self.subdomain = self.settings.freshdesk_subdomain
        
        if not self.api_key or not self.subdomain:
            logger.warning("⚠️ Freshdesk não configurado (API key ou subdomain não encontrados)")
    
    @property
    def base_url(self) -> str:
        """Retorna a URL base da API do Freshdesk."""
        return f"https://{self.subdomain}.freshdesk.com/api/v2"
    
    def _get_headers(self) -> dict:
        """Retorna os headers para requisições."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self._encode_auth()}",
        }
    
    def _encode_auth(self) -> str:
        """Codifica credenciais em Base64."""
        import base64
        credentials = f"{self.api_key}:X"
        return base64.b64encode(credentials.encode()).decode()
    
    def _construir_payload(self, request: CriarTicketRequest) -> dict:
        """Constrói o payload para criar ticket."""
        payload = {
            "subject": request.assunto,
            "description": request.descricao,
            "priority": self.FRESHDESK_PRIORIDADE.get(
                request.prioridade, PrioridadeTicket.MEDIA
            ),
            "status": self.FRESHDESK_STATUS[StatusTicket.ABERTO],
        }
        
        # Adicionar e-mail se fornecido
        if request.email_cliente:
            payload["email"] = request.email_cliente
        
        # Adicionar nome se fornecido
        if request.nome_cliente:
            payload["name"] = request.nome_cliente
        
        # Adicionar telefone se fornecido
        if request.telefone_cliente:
            payload["phone"] = request.telefone_cliente
        
        # Adicionar tags se fornecidas
        if request.tags:
            payload["tags"] = request.tags
        
        return payload
    
    def _converter_ticket(self, data: dict) -> TicketInfo:
        """Converte resposta da API em TicketInfo."""
        status = self.STATUS_FRESHDESK.get(data.get("status"), StatusTicket.ABERTO)
        prioridade = self.PRIORIDADE_FRESHDESK.get(
            data.get("priority"), PrioridadeTicket.MEDIA
        )
        
        return TicketInfo(
            id_externo=str(data.get("id")),
            status=status,
            prioridade=prioridade,
            assunto=data.get("subject", ""),
            descricao=data.get("description", ""),
            url=f"https://{self.subdomain}.freshdesk.com/a/tickets/{data.get('id')}",
            data_criacao=data.get("created_at"),
            data_atualizacao=data.get("updated_at"),
        )
    
    def criar_ticket(self, request: CriarTicketRequest) -> TicketInfo:
        """
        Cria um novo ticket no Freshdesk.
        
        Args:
            request: Dados do ticket a ser criado
            
        Returns:
            TicketInfo com informações do ticket criado
        """
        logger.info(f"📝 Criando ticket no Freshdesk: {request.assunto}")
        
        url = f"{self.base_url}/tickets"
        payload = self._construir_payload(request)
        
        response = requests.post(
            url,
            json=payload,
            headers=self._get_headers(),
            timeout=30,
        )
        
        if response.status_code not in (200, 201):
            logger.error(f"❌ Erro ao criar ticket: {response.status_code} - {response.text}")
            raise Exception(f"Erro ao criar ticket: {response.status_code}")
        
        data = response.json()
        logger.info(f"✅ Ticket criado: #{data.get('id')}")
        
        return self._converter_ticket(data)
    
    def consultar_status(self, ticket_id: str) -> TicketInfo:
        """
        Consulta o status de um ticket no Freshdesk.
        
        Args:
            ticket_id: ID do ticket no Freshdesk
            
        Returns:
            TicketInfo com informações atualizadas do ticket
        """
        logger.info(f"🔍 Consultando ticket #{ticket_id}")
        
        url = f"{self.base_url}/tickets/{ticket_id}"
        
        response = requests.get(
            url,
            headers=self._get_headers(),
            timeout=30,
        )
        
        if response.status_code == 404:
            raise Exception(f"Ticket #{ticket_id} não encontrado")
        
        if response.status_code != 200:
            raise Exception(f"Erro ao consultar ticket: {response.status_code}")
        
        data = response.json()
        return self._converter_ticket(data)
    
    def listar_tickets(
        self,
        email_cliente: Optional[str] = None,
        status: Optional[StatusTicket] = None,
        limite: int = 10,
    ) -> list[TicketInfo]:
        """
        Lista tickets no Freshdesk.
        
        Args:
            email_cliente: E-mail do cliente para filtrar
            status: Status para filtrar
            limite: Número máximo de tickets
            
        Returns:
            Lista de TicketInfo
        """
        logger.info(f"🔍 Listando tickets (email: {email_cliente}, status: {status})")
        
        params = {"per_page": limite}
        
        if email_cliente:
            params["email"] = email_cliente
        
        if status:
            params["status"] = self.FRESHDESK_STATUS.get(status)
        
        url = f"{self.base_url}/tickets"
        
        response = requests.get(
            url,
            params=params,
            headers=self._get_headers(),
            timeout=30,
        )
        
        if response.status_code != 200:
            raise Exception(f"Erro ao listar tickets: {response.status_code}")
        
        tickets = response.json()
        return [self._converter_ticket(t) for t in tickets]
    
    def validar_configuracao(self) -> bool:
        """
        Valida se a configuração do Freshdesk está correta.
        
        Returns:
            True se a configuração for válida
        """
        if not self.api_key or not self.subdomain:
            return False
        
        # Testar conexão
        try:
            url = f"{self.base_url}/settings"
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=10,
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Erro ao validar configuração do Freshdesk: {e}")
            return False
