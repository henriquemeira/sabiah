"""Handler principal de mensagens do bot."""

import logging
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

from src.models.database import get_db
from src.models import Cliente
from src.services import IdentificacaoService, ClienteNaoEncontrado
from src.services.escalonamento import ServicoEscalonamento
from src.services.deteccao_escalonamento import TipoEscalonamento
from src.bot.handlers.escalonamento import (
    criar_menu_escalonamento,
    mostrar_opcoes_escalonamento,
    tratar_callback_escalonamento,
)

logger = logging.getLogger(__name__)


# Estados da conversa
AGUARDANDO_IDENTIFICACAO = 1
AGUARDANDO_MENSAGEM = 2


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler para o comando /start."""
    await update.message.reply_text(
        "🐦 Olá! Sou o Sabiah, seu assistente de suporte.\n\n"
        "Para começar, preciso identificar sua conta. "
        "Por favor, informe seu CNPJ, código de cliente ou e-mail."
    )
    return AGUARDANDO_IDENTIFICACAO


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para o comando /help."""
    await update.message.reply_text(
        "📋 *Ajuda do Sabiah*\n\n"
        "• /start - Iniciar atendimento\n"
        "• /help - Ver esta mensagem\n"
        "• /status - Ver status dos seus tickets\n\n"
        "Em caso de dúvidas, digite sua pergunta e farei o possível para ajudar.",
        parse_mode="Markdown"
    )


async def tratar_identificacao(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa a identificação do cliente."""
    texto = update.message.text.strip()
    telegram_id = update.effective_user.id
    
    db = next(get_db())
    identificador = IdentificacaoService(db)
    
    try:
        # Tentar identificar o cliente
        cliente = identificador.identificar(texto)
        
        if cliente:
            # Cliente encontrado - vincular Telegram se necessário
            if not cliente.telegram_id:
                identificador.vincular_telegram(cliente, telegram_id)
            
            # Salvar cliente no contexto
            context.user_data["cliente"] = cliente
            context.user_data["historico_conversa"] = ""
            context.user_data["tentativas"] = 0
            
            await update.message.reply_text(
                f"✅ Olá, {cliente.nome}! Como posso ajudar hoje?"
            )
            
            db.close()
            return AGUARDANDO_MENSAGEM
        else:
            # Cliente não encontrado
            await update.message.reply_text(
                "❓ Não encontrei sua conta no sistema.\n\n"
                "Por favor, verifique o CNPJ/código/e-mail informado "
                "ou entre em contato com nosso suporte."
            )
            db.close()
            return AGUARDANDO_IDENTIFICACAO
            
    except Exception as e:
        logger.error(f"Erro na identificação: {e}")
        await update.message.reply_text(
            "⚠️ Ocorreu um erro ao processar sua solicitação. "
            "Por favor, tente novamente."
        )
        db.close()
        return AGUARDANDO_IDENTIFICACAO


async def tratar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa mensagens do cliente identificado."""
    mensagem = update.message.text
    cliente: Cliente = context.user_data.get("cliente")
    
    if not cliente:
        await update.message.reply_text(
            "⚠️ Sessão expirada. Por favor, envie /start para iniciar novamente."
        )
        return AGUARDANDO_IDENTIFICACAO
    
    # Atualizar histórico
    historico = context.user_data.get("historico_conversa", "")
    historico += f"Cliente: {mensagem}\n"
    
    # TODO: Aqui entraria a lógica de IA
    # Por enquanto, apenas echo com menu de escalonamento simulado
    await update.message.reply_text(
        f"📝 Você disse: {mensagem}\n\n"
        "Em uma implementação completa, isso seria processado pela IA."
    )
    
    # Simular detecção de necessidade de escalonamento
    # (Aqui você integraria com o DetectorEscalonamento)
    
    # Atualizar histórico
    context.user_data["historico_conversa"] = historico
    
    return AGUARDANDO_MENSAGEM


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela a conversa."""
    await update.message.reply_text(
        "✅ Conversa cancelada. Envie /start para iniciar novamente."
    )
    context.user_data.clear()
    return ConversationHandler.END


def get_conversation_handler() -> ConversationHandler:
    """Retorna o ConversationHandler principal."""
    return ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            AGUARDANDO_IDENTIFICACAO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tratar_identificacao)
            ],
            AGUARDANDO_MENSAGEM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tratar_mensagem)
            ],
        },
        fallbacks=[
            CommandHandler("cancelar", cancelar),
            CommandHandler("start", start_command),
        ],
    )


def get_callback_handler():
    """Retorna o handler de callbacks inline."""
    return CallbackQueryHandler(tratar_callback_escalonamento, pattern="^escalonar_")
