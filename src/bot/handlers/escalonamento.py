"""Handlers de escalonamento para o bot do Telegram."""

import logging
from enum import Enum

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from src.services.deteccao_escalonamento import TipoEscalonamento
from src.services.escalonamento import ServicoEscalonamento, ResultadoEscalonamento

logger = logging.getLogger(__name__)


# Estados para conversa de callback
COLETAR_TELEFONE = 1


class EstadosEscalonamento(Enum):
    """Estados para o conversation handler de escalonamento."""
    AGUARDANDO_TELEFONE = 1


def criar_menu_escalonamento() -> InlineKeyboardMarkup:
    """
    Cria o menu de opções de escalonamento.
    
    Returns:
        InlineKeyboardMarkup com as opções
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "🎫 Abrir Ticket",
                callback_data="escalonar_ticket"
            )
        ],
        [
            InlineKeyboardButton(
                "👤 Falar com Atendente",
                callback_data="escalonar_humano"
            )
        ],
        [
            InlineKeyboardButton(
                "📞 Solicitar Callback",
                callback_data="escalonar_callback"
            )
        ],
        [
            InlineKeyboardButton(
                "🔄 Reformular Pergunta",
                callback_data="escalonar_reformular"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Cancelar",
                callback_data="escalonar_cancelar"
            )
        ],
    ]
    
    return InlineKeyboardMarkup(keyboard)


async def mostrar_opcoes_escalonamento(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    mensagem: str = None,
) -> None:
    """
    Mostra as opções de escalonamento para o usuário.
    
    Args:
        update: Update do Telegram
        context: Contexto do bot
        mensagem: Mensagem adicional (opcional)
    """
    if mensagem is None:
        mensagem = (
            "Parece que não consegui resolver sua questão. "
            "Como você gostaria de prosseguir?"
        )
    
    keyboard = criar_menu_escalonamento()
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=mensagem,
            reply_markup=keyboard,
        )
    else:
        await update.message.reply_text(
            text=mensagem,
            reply_markup=keyboard,
        )


async def tratar_callback_escalonamento(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Trata os callbacks dos botões de escalonamento.
    
    Args:
        update: Update do Telegram
        context: Contexto do bot
    """
    query = update.callback_query
    await query.answer()
    
    # Obter dados do cliente do context
    cliente = context.user_data.get("cliente")
    if not cliente:
        await query.edit_message_text(
            "⚠️ Sessão expirada. Por favor, envie /start para iniciar novamente."
        )
        return
    
    # Obter o tipo de escalonamento
    callback_data = query.data
    logger.info(f"📥 Callback de escalonamento: {callback_data}")
    
    # Obter Telegram ID do atendente
    telegram_id = update.effective_user.id
    
    # Obter histórico da conversa
    historico = context.user_data.get("historico_conversa", "")
    
    # Criar serviço de escalonamento
    from src.models.database import get_db
    db = next(get_db())
    servico = ServicoEscalonamento(db)
    
    try:
        if callback_data == "escalonar_ticket":
            resultado = await _executar_escalonamento(
                servico, cliente, TipoEscalonamento.ABRIR_TICKET, historico, telegram_id
            )
            await query.edit_message_text(resultado.mensagem)
        
        elif callback_data == "escalonar_humano":
            resultado = await _executar_escalonamento(
                servico, cliente, TipoEscalonamento.ATENDIMENTO_HUMANO, historico, telegram_id
            )
            await query.edit_message_text(resultado.mensagem)
        
        elif callback_data == "escalonar_callback":
            # Perguntar pelo telefone
            await query.edit_message_text(
                "📞 Para solicitar um callback, por favor, informe seu número de telefone."
            )
            context.user_data["estado"] = EstadosEscalonamento.AGUARDANDO_TELEFONE
            return COLETAR_TELEFONE
        
        elif callback_data == "escalonar_reformular":
            await query.edit_message_text(
                "🔄 Vamos tentar novamente!\n\n"
                "Por favor, reformule sua pergunta ou forneça mais detalhes sobre o que você precisa."
            )
        
        elif callback_data == "escalonar_cancelar":
            await query.edit_message_text(
                "✅ Ok! Se precisar de mais alguma coisa, é só perguntar."
            )
        
        else:
            await query.edit_message_text(
                "⚠️ Opção não reconhecida. Por favor, tente novamente."
            )
    
    except Exception as e:
        logger.error(f"❌ Erro no escalonamento: {e}")
        await query.edit_message_text(
            "⚠️ Ocorreu um erro ao processar sua solicitação. "
            "Por favor, tente novamente mais tarde."
        )


async def _executar_escalonamento(
    servico: ServicoEscalonamento,
    cliente,
    tipo: TipoEscalonamento,
    historico: str,
    atendente_telegram_id: int = None,
) -> ResultadoEscalonamento:
    """
    Executa o escalonamento.
    
    Args:
        servico: Serviço de escalonamento
        cliente: Cliente
        tipo: Tipo de escalonamento
        historico: Histórico da conversa
        atendente_telegram_id: Telegram ID do atendente
        
    Returns:
        ResultadoEscalonamento
    """
    return servico.executar_escalonamento(
        cliente=cliente,
        tipo=tipo,
        historico_conversa=historico,
        atendente_telegram_id=atendente_telegram_id,
    )


async def tratar_telefone_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """
    Trata o recebimento do telefone para callback.
    
    Args:
        update: Update do Telegram
        context: Contexto do bot
        
    Returns:
        Estado da conversa
    """
    telefone = update.message.text
    
    # Obter dados do cliente
    cliente = context.user_data.get("cliente")
    if not cliente:
        await update.message.reply_text(
            "⚠️ Sessão expirada. Por favor, envie /start para iniciar novamente."
        )
        return ConversationHandler.END
    
    # Obter histórico
    historico = context.user_data.get("historico_conversa", "")
    
    # Criar serviço de escalonamento
    from src.models.database import get_db
    db = next(get_db())
    servico = ServicoEscalonamento(db)
    
    try:
        resultado = servico.executar_escalonamento(
            cliente=cliente,
            tipo=TipoEscalonamento.CALLBACK,
            historico_conversa=historico,
            telefone=telefone,
        )
        
        await update.message.reply_text(resultado.mensagem)
        
    except Exception as e:
        logger.error(f"❌ Erro ao solicitar callback: {e}")
        await update.message.reply_text(
            "⚠️ Ocorreu um erro ao processar sua solicitação. "
            "Por favor, tente novamente mais tarde."
        )
    
    # Limpar estado
    context.user_data.pop("estado", None)
    return ConversationHandler.END


async def cancelar_conversa_escalonamento(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """
    Cancela a conversa de escalonamento.
    
    Args:
        update: Update do Telegram
        context: Contexto do bot
        
    Returns:
        Fim da conversa
    """
    await update.message.reply_text(
        "✅ Operação cancelada. Se precisar de mais alguma coisa, é só perguntar."
    )
    context.user_data.pop("estado", None)
    return ConversationHandler.END


def get_handlers_escalonamento() -> list:
    """
    Retorna os handlers de escalonamento.
    
    Returns:
        Lista de handlers
    """
    # Handler de callback (botões inline)
    callback_handler = CallbackQueryHandler(
        tratar_callback_escalonamento,
        pattern="^escalonar_",
    )
    
    # Conversation handler para coletar telefone
    conversation_handler = ConversationHandler(
        entry_points=[],  # Adicionado dinamicamente
        states={
            COLETAR_TELEFONE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    tratar_telefone_callback,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancelar", cancelar_conversa_escalonamento),
        ],
    )
    
    return [callback_handler, conversation_handler]
