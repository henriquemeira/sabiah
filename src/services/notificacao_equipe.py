"""Serviço de notificação para a equipe de suporte."""

import logging
from typing import Optional

from telegram import Bot
from telegram.error import TelegramError

from src.config import get_settings
from src.models import Cliente
from src.services.deteccao_escalonamento import TipoEscalonamento

logger = logging.getLogger(__name__)


class ServicoNotificacaoEquipe:
    """
    Serviço para notificar a equipe de suporte sobre escalonamentos.
    
    Usa o Telegram para enviar mensagens a um grupo configurado.
    """
    
    def __init__(self):
        """Inicializa o serviço de notificação."""
        self.settings = get_settings()
        self.bot_token = self.settings.telegram_bot_token
        self.chat_id_equipe = self.settings.telegram_grupo_id  # ID do grupo
    
    @property
    def bot(self) -> Optional[Bot]:
        """Retorna instância do bot."""
        if not self.bot_token:
            return None
        return Bot(token=self.bot_token)
    
    def _formatar_mensagem(
        self,
        cliente: Cliente,
        tipo: TipoEscalonamento,
        ticket_id: Optional[str] = None,
        ticket_url: Optional[str] = None,
        telefone: Optional[str] = None,
        erro: Optional[str] = None,
    ) -> str:
        """Formata a mensagem de notificação."""
        
        # Emoji baseado no tipo
        emojis = {
            TipoEscalonamento.ABRIR_TICKET: "🎫",
            TipoEscalonamento.ATENDIMENTO_HUMANO: "👤",
            TipoEscalonamento.CALLBACK: "📞",
            TipoEscalonamento.REFORMULAR: "🔄",
        }
        emoji = emojis.get(tipo, "❓")
        
        # Título
        titulos = {
            TipoEscalonamento.ABRIR_TICKET: "Novo Ticket Criado",
            TipoEscalonamento.ATENDIMENTO_HUMANO: "Solicitação de Atendimento Humano",
            TipoEscalonamento.CALLBACK: "Solicitação de Callback",
            TipoEscalonamento.REFORMULAR: "Cliente Reformulou Pergunta",
        }
        titulo = titulos.get(tipo, "Notificação")
        
        # Construir mensagem
        mensagem = f"""🚨 *{titulo}*

*Cliente:*
- Nome: {cliente.nome}
- CNPJ: {cliente.cnpj or 'N/A'}
- E-mail: {cliente.email or 'N/A'}
- Telegram: {cliente.telegram_id or 'N/A'}
- Versão: {cliente.versao_software or 'N/A'}
- Plano: {cliente.plano or 'N/A'}
"""
        
        if telefone:
            mensagem += f"- Telefone: {telefone}\n"
        
        if ticket_id:
            mensagem += f"\n*Ticket:* #{ticket_id}"
            if ticket_url:
                mensagem += f" | [Ver ticket]({ticket_url})"
        
        if erro:
            mensagem += f"\n\n⚠️ *Erro:* {erro}"
        
        mensagem += f"\n\n{emoji} _Notificação automática do Sabiah_"
        
        return mensagem
    
    async def notificar_escalonamento(
        self,
        cliente: Cliente,
        tipo: TipoEscalonamento,
        ticket_id: Optional[str] = None,
        ticket_url: Optional[str] = None,
        telefone: Optional[str] = None,
        erro: Optional[str] = None,
    ) -> bool:
        """
        Envia notificação para a equipe.
        
        Args:
            cliente: Cliente que originou a solicitação
            tipo: Tipo de escalonamento
            ticket_id: ID do ticket criado
            ticket_url: URL do ticket
            telefone: Telefone para callback
            erro: Erro se houver
            
        Returns:
            True se enviou com sucesso
        """
        if not self.chat_id_equipe:
            logger.warning("⚠️ ID do grupo de equipe não configurado")
            return False
        
        if not self.bot:
            logger.warning("⚠️ Bot não configurado para notificações")
            return False
        
        try:
            mensagem = self._formatar_mensagem(
                cliente=cliente,
                tipo=tipo,
                ticket_id=ticket_id,
                ticket_url=ticket_url,
                telefone=telefone,
                erro=erro,
            )
            
            await self.bot.send_message(
                chat_id=self.chat_id_equipe,
                text=mensagem,
                parse_mode="Markdown",
            )
            
            logger.info(f"✅ Notificação enviada para a equipe: {tipo.value}")
            return True
            
        except TelegramError as e:
            logger.error(f"❌ Erro ao enviar notificação: {e}")
            return False
    
    async def notificar_novo_cliente(self, cliente: Cliente) -> bool:
        """
        Notifica quando um novo cliente inicia conversa.
        
        Args:
            cliente: Cliente que iniciou
            
        Returns:
            True se enviou com sucesso
        """
        if not self.chat_id_equipe or not self.bot:
            return False
        
        mensagem = f"""🆕 *Novo Cliente*

- Nome: {cliente.nome}
- CNPJ: {cliente.cnpj or 'N/A'}
- E-mail: {cliente.email or 'N/A'}
- Telegram: {cliente.telegram_id or 'N/A'}
"""
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id_equipe,
                text=mensagem,
                parse_mode="Markdown",
            )
            return True
        except TelegramError as e:
            logger.error(f"❌ Erro ao notificar novo cliente: {e}")
            return False
