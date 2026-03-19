"""Serviço de Pesquisa de Satisfação."""

import logging
from enum import Enum
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
)

from src.models import Cliente, Conversa
from src.models.database import get_db

logger = logging.getLogger(__name__)


class NivelSatisfacao(str, Enum):
    """Níveis de satisfação do cliente."""
    MUITO_SATISFEITO = 5
    SATISFEITO = 4
    NEUTRO = 3
    INSATISFEITO = 2
    MUITO_INSATISFEITO = 1


# Mapeamento de emojis para níveis
EMOJIS_SATISFACAO = {
    "5": "😁",
    "4": "🙂",
    "3": "😐",
    "2": "😕",
    "1": "😞",
}

# Texto para cada nível
TEXTOS_SATISFACAO = {
    "5": "Muito Satisfeito",
    "4": "Satisfeito",
    "3": "Neutro",
    "2": "Insatisfeito",
    "1": "Muito Insatisfeito",
}


def criar_teclado_satisfacao() -> InlineKeyboardMarkup:
    """
    Cria o teclado de pesquisa de satisfação.
    
    Returns:
        InlineKeyboardMarkup com botões de satisfação
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "😁 Muito Satisfeito",
                callback_data="satisfacao_5"
            ),
            InlineKeyboardButton(
                "🙂 Satisfeito",
                callback_data="satisfacao_4"
            ),
        ],
        [
            InlineKeyboardButton(
                "😐 Neutro",
                callback_data="satisfacao_3"
            ),
        ],
        [
            InlineKeyboardButton(
                "😕 Insatisfeito",
                callback_data="satisfacao_2"
            ),
            InlineKeyboardButton(
                "😞 Muito Insatisfeito",
                callback_data="satisfacao_1"
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(keyboard)


async def enviar_pesquisa_satisfacao(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    conversa_id: Optional[int] = None,
) -> None:
    """
    Envia a pesquisa de satisfação para o cliente.
    
    Args:
        update: Update do Telegram
        context: Contexto do bot
        conversa_id: ID da conversa (opcional)
    """
    mensagem = (
        "📊 *Pesquisa de Satisfação*\n\n"
        "Por favor, avalie seu atendimento de hoje:\n\n"
        "Como você avalia a qualidade do suporte recebido?"
    )
    
    keyboard = criar_teclado_satisfacao()
    
    # Armazenar o ID da conversa no contexto se fornecido
    if conversa_id:
        context.user_data["conversa_avaliacao"] = conversa_id
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=mensagem,
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            text=mensagem,
            reply_markup=keyboard,
            parse_mode="Markdown",
        )


async def tratar_resposta_satisfacao(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Trata a resposta da pesquisa de satisfação.
    
    Args:
        update: Update do Telegram
        context: Contexto do bot
    """
    query = update.callback_query
    await query.answer()
    
    # Extrair nível de satisfação do callback_data
    callback_data = query.data
    if not callback_data.startswith("satisfacao_"):
        return
    
    try:
        nivel = int(callback_data.split("_")[1])
    except (ValueError, IndexError):
        await query.edit_message_text(
            "⚠️ Erro ao processar sua avaliação. Por favor, tente novamente."
        )
        return
    
    # Obter cliente do contexto
    cliente = context.user_data.get("cliente")
    if not cliente:
        await query.edit_message_text(
            "⚠️ Sessão expirada. Por favor, envie /start para iniciar novamente."
        )
        return
    
    # Obter ID da conversa para atualizar
    conversa_id = context.user_data.get("conversa_avaliacao")
    
    db = next(get_db())
    try:
        # Atualizar a conversa com a satisfação
        if conversa_id:
            conversa = db.query(Conversa).filter(Conversa.id == conversa_id).first()
            if conversa:
                conversa.satisfacao = nivel
                db.commit()
        
        # Gerar mensagem de agradecimento
        emoji = EMOJIS_SATISFACAO.get(str(nivel), "❓")
        
        if nivel >= 4:
            mensagem = (
                f"{emoji} *Obrigado pela sua avaliação!*\n\n"
                "Ficamos felizes em saber que você ficou satisfeito(a) com o atendimento. "
                "Estamos sempre trabalhando para melhorar!\n\n"
                "Se precisar de mais alguma coisa, é só chamar. 😊"
            )
        elif nivel == 3:
            mensagem = (
                f"{emoji} *Obrigado pela sua avaliação!*\n\n"
                "Agradecemos seu feedback. "
                "Estamos sempre trabalhando para melhorar nosso atendimento.\n\n"
                "Se precisar de mais alguma coisa, é só chamar."
            )
        else:
            mensagem = (
                f"{emoji} *Obrigado pela sua avaliação!*\n\n"
                "Pedimos desculpas por não termos atendi-lo completamente. "
                "Vamos usar seu feedback para melhorar.\n\n"
                "Se preferir falar com um atendente, digite *atendente*."
            )
        
        await query.edit_message_text(
            text=mensagem,
            parse_mode="Markdown",
        )
        
        # TODO: Notificar equipe sobre avaliação negativa
        if nivel <= 2:
            logger.info(f"⚠️ Cliente {cliente.id} deu avaliação negativa: {nivel}")
        
    except Exception as e:
        logger.error(f"Erro ao salvar satisfação: {e}")
        await query.edit_message_text(
            "⚠️ Erro ao salvar sua avaliação. Por favor, tente novamente mais tarde."
        )
    finally:
        db.close()


def get_handler_satisfacao() -> CallbackQueryHandler:
    """
    Retorna o handler para pesquisa de satisfação.
    
    Returns:
        CallbackQueryHandler
    """
    return CallbackQueryHandler(
        tratar_resposta_satisfacao,
        pattern="^satisfacao_",
    )
