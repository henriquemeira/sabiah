"""Sabiah - Bot de Suporte Inteligente via Telegram."""

import asyncio
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from src.config import get_settings
from src.config.logging import setup_logging

# Setup logging
logger = setup_logging()
settings = get_settings()


async def start_command(update: Update, context) -> None:
    """Handler para o comando /start."""
    await update.message.reply_text(
        "🐦 Olá! Sou o Sabiah, seu assistente de suporte.\n\n"
        "Para começar, preciso identificar sua conta. "
        "Por favor, informe seu CNPJ, código de cliente ou e-mail."
    )


async def help_command(update: Update, context) -> None:
    """Handler para o comando /help."""
    await update.message.reply_text(
        "📋 *Ajuda do Sabiah*\n\n"
        "• /start - Iniciar atendimento\n"
        "• /help - Ver esta mensagem\n"
        "• /status - Ver status dos seus tickets\n\n"
        "Em caso de dúvidas, digite sua pergunta e farei o possível para ajudar.",
        parse_mode="Markdown"
    )


async def echo_message(update: Update, context) -> None:
    """Handler para mensagens de texto (echo temporário)."""
    user_message = update.message.text
    await update.message.reply_text(f"Você disse: {user_message}")


async def post_init(application: Application) -> None:
    """Called after initialization, before the application starts."""
    bot = application.bot
    me = await bot.get_me()
    logger.info(f"🤖 Bot iniciado: @{me.username} (ID: {me.id})")


def main() -> None:
    """Função principal para iniciar o bot."""
    if not settings.telegram_bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN não configurado!")
        logger.error("Crie um bot via @BotFather e configure o token no arquivo .env")
        return

    logger.info("🚀 Iniciando Sabiah...")

    # Criar aplicação
    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .build()
    )

    # Registrar handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))

    # Iniciar polling
    logger.info("📡 Aguardando mensagens...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
