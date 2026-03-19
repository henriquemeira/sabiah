"""Sabiah - Bot de Suporte Inteligente via Telegram."""

import asyncio
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
)

from src.config import get_settings
from src.config.logging import setup_logging
from src.bot.handlers.mensagens import get_conversation_handler, get_callback_handler
from src.models.database import init_db
from src.memory.memoria_geral import get_memoria_geral


async def post_init(application: Application) -> None:
    """Called after initialization, before the application starts."""
    logger = logging.getLogger("sabiah")
    bot = application.bot
    me = await bot.get_me()
    logger.info(f"🤖 Bot iniciado: @{me.username} (ID: {me.id})")
    
    # Inicializar base de conhecimento
    logger.info("📚 Carregando base de conhecimento...")
    memoria_geral = get_memoria_geral()
    total_docs = memoria_geral.indexar()
    logger.info(f"✅ Base de conhecimento carregada: {total_docs} documentos")


def main() -> None:
    """Função principal para iniciar o bot."""
    logger = setup_logging()
    settings = get_settings()
    
    # Sempre inicializar banco de dados primeiro
    logger.info("💾 Inicializando banco de dados...")
    init_db()
    logger.info("✅ Banco de dados inicializado!")
    
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
    application.add_handler(get_conversation_handler())
    application.add_handler(get_callback_handler())
    application.add_handler(CommandHandler("help", help_command))

    # Iniciar polling
    logger.info("📡 Aguardando mensagens...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


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


if __name__ == "__main__":
    main()
