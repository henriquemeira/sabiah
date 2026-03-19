"""Serviço de Escalonamento - Orquestra todo o fluxo de escalonamento."""

import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from src.models import Cliente, Ticket, Conversa
from src.services.deteccao_escalonamento import (
    DetectorEscalonamento,
    MotivoEscalonamento,
    TipoEscalonamento,
    ResultadoDetecção,
)
from src.services.helpdesk import (
    HelpdeskFactory,
    CriarTicketRequest,
    PrioridadeTicket,
    StatusTicket,
)
from src.services.notificacao_equipe import ServicoNotificacaoEquipe
from src.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ResultadoEscalonamento:
    """Resultado de uma operação de escalonamento."""
    sucesso: bool
    tipo: TipoEscalonamento
    mensagem: str
    ticket_id: Optional[str] = None
    ticket_url: Optional[str] = None


class ServicoEscalonamento:
    """
    Serviço que orchestrates o fluxo completo de escalonamento.
    
    Responsabilidades:
    1. Detectar necessidade de escalonamento
    2. Criar tickets no helpdesk
    3. Notificar a equipe interna
    4. Coletar informações necessárias (telefone, etc.)
    5. Registrar escalonamento no banco de dados
    """
    
    def __init__(self, db: Session):
        """
        Inicializa o serviço de escalonamento.
        
        Args:
            db: Sessão do banco de dados
        """
        self.db = db
        self.settings = get_settings()
        self.detector = DetectorEscalonamento()
        self.helpdesk = HelpdeskFactory.get_canal()
    
    def analisar_necessidade(
        self,
        cliente: Cliente,
        mensagem: str,
        resposta_ia=None,
        numero_tentativas: int = 0,
    ) -> ResultadoDetecção:
        """
        Analisa se o atendimento precisa ser escalonado.
        
        Args:
            cliente: Cliente
            mensagem: Última mensagem do cliente
            resposta_ia: Resposta da IA (opcional)
            numero_tentativas: Número de tentativas já realizadas
            
        Returns:
            ResultadoDetecção
        """
        return self.detector.analisar(
            resposta_ia=resposta_ia,
            mensagem_cliente=mensagem,
            numero_tentativas=numero_tentativas,
        )
    
    def executar_escalonamento(
        self,
        cliente: Cliente,
        tipo: TipoEscalonamento,
        historico_conversa: str,
        motivo: Optional[MotivoEscalonamento] = None,
        telefone: Optional[str] = None,
        atendente_telegram_id: Optional[int] = None,
    ) -> ResultadoEscalonamento:
        """
        Executa o escalonamiento según o tipo especificado.
        
        Args:
            cliente: Cliente
            tipo: Tipo de escalonamento
            historico_conversa: Histórico da conversa
            motivo: Motivo do escalonamento
            telefone: Telefone para callback (se aplicável)
            atendente_telegram_id: Telegram ID do atendente (para isolamento de tickets)
            
        Returns:
            ResultadoEscalonamento
        """
        logger.info(f"🔄 Executando escalonamento: {tipo} para cliente {cliente.id}")
        
        if tipo == TipoEscalonamento.ABRIR_TICKET:
            return self._abrir_ticket(
                cliente, historico_conversa, motivo, telefone, atendente_telegram_id
            )
        
        elif tipo == TipoEscalonamento.ATENDIMENTO_HUMANO:
            return self._solicitar_atendimento_humano(
                cliente, historico_conversa, motivo, atendente_telegram_id
            )
        
        elif tipo == TipoEscalonamento.CALLBACK:
            return self._solicitar_callback(
                cliente, historico_conversa, telefone, atendente_telegram_id
            )
        
        elif tipo == TipoEscalonamento.REFORMULAR:
            return ResultadoEscalonamento(
                sucesso=True,
                tipo=TipoEscalonamento.REFORMULAR,
                mensagem="Vamos tentar novamente! Por favor, reformule sua pergunta.",
            )
        
        else:
            return ResultadoEscalonamento(
                sucesso=False,
                tipo=tipo,
                mensagem="Tipo de escalonamento não reconhecido.",
            )
    
    def _abrir_ticket(
        self,
        cliente: Cliente,
        historico_conversa: str,
        motivo: Optional[MotivoEscalonamento],
        telefone: Optional[str] = None,
        atendente_telegram_id: Optional[int] = None,
    ) -> ResultadoEscalonamento:
        """Abre um ticket no helpdesk."""
        
        # Verificar se helpdesk está configurado
        if not self.helpdesk:
            logger.warning("⚠️ Helpdesk não configurado, salvando ticket localmente")
            return self._criar_ticket_local(
                cliente=cliente,
                historico_conversa=historico_conversa,
                motivo=motivo,
                telefone=telefone,
                atendente_telegram_id=atendente_telegram_id,
            )
        
        # Determinar prioridade
        prioridade = PrioridadeTicket.MEDIA
        if motivo == MotivoEscalonamento.ERRO_TECNICO:
            prioridade = PrioridadeTicket.ALTA
        elif motivo == MotivoEscalonamento.BAIXA_CONFIANCA:
            prioridade = PrioridadeTicket.BAIXA
        
        # Criar request
        request = CriarTicketRequest(
            assunto=f"Suporte via Telegram - {cliente.nome}",
            descricao=self._formatar_descricao_ticket(
                cliente=cliente,
                historico=historico_conversa,
                motivo=motivo,
            ),
            prioridade=prioridade,
            email_cliente=cliente.email,
            nome_cliente=cliente.nome,
            telefone_cliente=telefone or cliente.telefone,
            tags=["telegram", "escalonado"],
        )
        
        try:
            ticket_info = self.helpdesk.criar_ticket(request)
            
            # Salvar no banco local
            self._salvar_ticket_local(
                cliente=cliente,
                ticket_externo_id=ticket_info.id_externo,
                canal="freshdesk",
                assunto=request.assunto,
                descricao=request.descricao,
                prioridade=prioridade.value,
                atendente_telegram_id=atendente_telegram_id,
            )
            
            # Notificar equipe
            self._notificar_equipe(
                cliente=cliente,
                tipo=TipoEscalonamento.ABRIR_TICKET,
                ticket_id=ticket_info.id_externo,
                ticket_url=ticket_info.url,
            )
            
            return ResultadoEscalonamento(
                sucesso=True,
                tipo=TipoEscalonamento.ABRIR_TICKET,
                mensagem=f"✅ Ticket #{ticket_info.id_externo} criado com sucesso!\n\n"
                       f"Você pode acompanhar o andamento em: {ticket_info.url}",
                ticket_id=ticket_info.id_externo,
                ticket_url=ticket_info.url,
            )
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar ticket: {e}")
            return self._criar_ticket_local(
                cliente=cliente,
                historico_conversa=historico_conversa,
                motivo=motivo,
                telefone=telefone,
                atendente_telegram_id=atendente_telegram_id,
                erro=str(e),
            )
    
    def _criar_ticket_local(
        self,
        cliente: Cliente,
        historico_conversa: str,
        motivo: Optional[MotivoEscalonamento],
        telefone: Optional[str] = None,
        atendente_telegram_id: Optional[int] = None,
        erro: Optional[str] = None,
    ) -> ResultadoEscalonamento:
        """Cria um ticket local quando o helpdesk não está disponível."""
        
        # Determinar prioridade
        prioridade = "media"
        if motivo == MotivoEscalonamento.ERRO_TECNICO:
            prioridade = "alta"
        
        ticket = Ticket(
            cliente_id=cliente.id,
            telegram_id=cliente.telegram_id,
            atendente_telegram_id=atendente_telegram_id,
            ticket_externo_id=None,
            canal="telegram",
            assunto=f"Suporte via Telegram - {cliente.nome}",
            descricao=self._formatar_descricao_ticket(
                cliente=cliente,
                historico=historico_conversa,
                motivo=motivo,
            ),
            status="aberto",
            prioridade=prioridade,
        )
        
        self.db.add(ticket)
        self.db.commit()
        
        # Notificar equipe
        self._notificar_equipe(
            cliente=cliente,
            tipo=TipoEscalonamento.ABRIR_TICKET,
            ticket_id=str(ticket.id),
            erro=erro,
        )
        
        mensagem = "✅ Ticket criado no sistema interno.\n\n"
        if erro:
            mensagem += f"⚠️ O sistema de tickets externo está temporariamente indisponível. "
            mensagem += f"Nosso equipo foi notificado e entrará em contato em breve.\n\n"
            mensagem += f"ID do ticket: #{ticket.id}"
        else:
            mensagem += f"ID do ticket: #{ticket.id}"
        
        return ResultadoEscalonamento(
            sucesso=True,
            tipo=TipoEscalonamento.ABRIR_TICKET,
            mensagem=mensagem,
            ticket_id=str(ticket.id),
        )
    
    def _salvar_ticket_local(
        self,
        cliente: Cliente,
        ticket_externo_id: str,
        canal: str,
        assunto: str,
        descricao: str,
        prioridade: str,
        atendente_telegram_id: Optional[int] = None,
    ) -> None:
        """Salva referência do ticket no banco local."""
        ticket = Ticket(
            cliente_id=cliente.id,
            telegram_id=cliente.telegram_id,
            atendente_telegram_id=atendente_telegram_id,
            ticket_externo_id=ticket_externo_id,
            canal=canal,
            assunto=assunto,
            descricao=descricao,
            status="aberto",
            prioridade=prioridade,
        )
        
        self.db.add(ticket)
        self.db.commit()
    
    def _solicitar_atendimento_humano(
        self,
        cliente: Cliente,
        historico_conversa: str,
        motivo: Optional[MotivoEscalonamento],
    ) -> ResultadoEscalonamento:
        """Solicita transferência para atendimento humano."""
        
        # Criar ticket de优先级 alta
        ticket = Ticket(
            cliente_id=cliente.id,
            telegram_id=cliente.telegram_id,
            ticket_externo_id=None,
            canal="telegram",
            assunto=f"ATENDIMENTO HUMANO - {cliente.nome}",
            descricao=self._formatar_descricao_ticket(
                cliente=cliente,
                historico=historico_conversa,
                motivo=motivo,
            ),
            status="aberto",
            prioridade="alta",
        )
        
        self.db.add(ticket)
        self.db.commit()
        
        # Notificar equipe
        self._notificar_equipe(
            cliente=cliente,
            tipo=TipoEscalonamento.ATENDIMENTO_HUMANO,
            ticket_id=str(ticket.id),
        )
        
        return ResultadoEscalonamento(
            sucesso=True,
            tipo=TipoEscalonamento.ATENDIMENTO_HUMANO,
            mensagem="✅ Sua solicitação foi transferida para nossa equipe.\n\n"
                   "Um atendente entrará em contato em breve. "
                   f"ID da solicitação: #{ticket.id}",
            ticket_id=str(ticket.id),
        )
    
    def _solicitar_callback(
        self,
        cliente: Cliente,
        historico_conversa: str,
        telefone: Optional[str] = None,
        atendente_telegram_id: Optional[int] = None,
    ) -> ResultadoEscalonamento:
        """Solicita callback telefônico."""
        
        # Se não tem telefone, pedir ao cliente
        telefone_cliente = telefone or cliente.telefone
        if not telefone_cliente:
            return ResultadoEscalonamento(
                sucesso=False,
                tipo=TipoEscalonamento.CALLBACK,
                mensagem="Para solicitar um callback, por favor, informe seu número de telefone.",
            )
        
        # Criar ticket
        ticket = Ticket(
            cliente_id=cliente.id,
            telegram_id=cliente.telegram_id,
            atendente_telegram_id=atendente_telegram_id,
            ticket_externo_id=None,
            canal="telegram",
            assunto=f"CALLBACK - {cliente.nome} - {telefone_cliente}",
            descricao=self._formatar_descricao_ticket(
                cliente=cliente,
                historico=historico_conversa,
                motivo=MotivoEscalonamento.SOLICITACAO_EXPLICITA,
            ),
            status="aberto",
            prioridade="alta",
        )
        
        self.db.add(ticket)
        
        # Atualizar telefone do cliente
        if not cliente.telefone:
            cliente.telefone = telefone_cliente
        
        self.db.commit()
        
        # Notificar equipe
        self._notificar_equipe(
            cliente=cliente,
            tipo=TipoEscalonamento.CALLBACK,
            ticket_id=str(ticket.id),
            telefone=telefone_cliente,
        )
        
        return ResultadoEscalonamento(
            sucesso=True,
            tipo=TipoEscalonamento.CALLBACK,
            mensagem=f"✅ Callback solicitado para {telefone_cliente}.\n\n"
                   "Nossa equipe entrará em contato em breve.",
            ticket_id=str(ticket.id),
        )
    
    def _formatar_descricao_ticket(
        self,
        cliente: Cliente,
        historico_conversa: str,
        motivo: Optional[MotivoEscalonamento],
    ) -> str:
        """Formata a descrição do ticket."""
        descricao = f"""# Solicitações de Suporte

## Cliente
- **Nome:** {cliente.nome}
- **CNPJ:** {cliente.cnpj or 'N/A'}
- **E-mail:** {cliente.email or 'N/A'}
- **Telefone:** {cliente.telefone or 'N/A'}
- **Versão Software:** {cliente.versao_software or 'N/A'}
- **Plano:** {cliente.plano or 'N/A'}

## Motivo
{motivo.value if motivo else 'Não especificado'}

## Histórico da Conversa
{historico_conversa}

---
*Ticket criado automaticamente pelo Sabiah (Bot de Suporte)*
"""
        return descricao
    
    def _notificar_equipe(
        self,
        cliente: Cliente,
        tipo: TipoEscalonamento,
        ticket_id: Optional[str] = None,
        ticket_url: Optional[str] = None,
        telefone: Optional[str] = None,
        erro: Optional[str] = None,
    ) -> None:
        """
        Notifica a equipe interna sobre o escalonamento.
        
        Args:
            cliente: Cliente
            tipo: Tipo de escalonamento
            ticket_id: ID do ticket
            ticket_url: URL do ticket
            telefone: Telefone para callback
            erro: Erro se houver
        """
        try:
            notificador = ServicoNotificacaoEquipe()
            # Executar de forma síncrona (não precisa await aqui pois é chamado de contexto não-async)
            logger.info(
                f"📢 Notificação de equipe: {tipo.value} | "
                f"Cliente: {cliente.nome} | "
                f"Ticket: {ticket_id or 'N/A'}"
            )
        except Exception as e:
            logger.error(f"❌ Erro ao notificar equipe: {e}")
        
        if erro:
            logger.error(f"⚠️ Erro ao criar ticket externo: {erro}")
    
    def listar_tickets_cliente(
        self, 
        cliente: Cliente, 
        atendente_telegram_id: Optional[int] = None
    ) -> list[Ticket]:
        """Lista tickets de um cliente, opcionalmente filtrado por atendente."""
        query = self.db.query(Ticket).filter(Ticket.cliente_id == cliente.id)
        
        # Se fornecido, filtrar apenas tickets deste atendente
        if atendente_telegram_id:
            query = query.filter(Ticket.atendente_telegram_id == atendente_telegram_id)
        
        return (
            query
            .order_by(Ticket.created_at.desc())
            .limit(10)
            .all()
        )
    
    def consultar_ticket_externo(self, ticket_id: str) -> Optional[dict]:
        """Consulta ticket no helpdesk externo."""
        if not self.helpdesk:
            return None
        
        try:
            ticket = self.helpdesk.consultar_status(ticket_id)
            return {
                "id": ticket.id_externo,
                "status": ticket.status.value,
                "prioridade": ticket.prioridade.value,
                "url": ticket.url,
            }
        except Exception as e:
            logger.error(f"Erro ao consultar ticket: {e}")
            return None
