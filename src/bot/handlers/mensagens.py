"""Handler principal de mensagens do bot."""

import logging
import re
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
from src.services.deteccao_escalonamento import DetectorEscalonamento, TipoEscalonamento
from src.ai.factory import get_provedor
from src.memory.servico_contexto import ServicoContexto
from src.bot.handlers.escalonamento import (
    criar_menu_escalonamento,
    mostrar_opcoes_escalonamento,
    tratar_callback_escalonamento,
)

logger = logging.getLogger(__name__)


# Estados da conversa
AGUARDANDO_IDENTIFICACAO = 1


async def verificar_cliente_vinculado(telegram_id: int) -> tuple[Optional["Cliente"], list]:
    """
    Verifica se o Telegram ID está vinculado a um cliente.
    
    Args:
        telegram_id: ID do Telegram do usuário
        
    Returns:
        Tuple (cliente, lista de vínculos) - cliente pode ser None se não vinculado
    """
    db = next(get_db())
    identificador = IdentificacaoService(db)
    
    try:
        # Buscar vínculos do Telegram ID
        vinculos = identificador.buscar_vinculos_por_telegram_id(telegram_id)
        
        if vinculos:
            # Retornar primeiro vínculo (ou todos se precisar escolher)
            return vinculos[0].cliente, vinculos
        
        # Fallback: verificar campo direto (legado)
        cliente = identificador.buscar_por_telegram_id(telegram_id)
        return cliente, []
        
    finally:
        db.close()


async def tratar_mensagem_automatica(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handler para processar qualquer mensagem automaticamente.
    Verifica se o Telegram ID já está vinculado a um cliente.
    """
    telegram_id = update.effective_user.id
    mensagem = update.message.text
    
    # Ignorar comandos
    if mensagem.startswith('/'):
        return  # Deixa o ConversationHandler 处理 comandos
    
    logger.info(f"📥 Mensagem automática de {telegram_id}: {mensagem[:50]}...")
    
    # Verificar se já está em uma conversa ativa
    cliente_existente = context.user_data.get("cliente")
    if cliente_existente:
        # Já tem cliente no contexto, processar normalmente
        return await tratar_mensagem(update, context)
    
    # Verificar se Telegram ID está vinculado
    cliente, vinculos = await verificar_cliente_vinculado(telegram_id)
    
    if cliente:
        logger.info(f"✅ Cliente encontrado: {cliente.nome} (ID: {cliente.id})")
        
        # Restaurar contexto do cliente
        context.user_data["cliente"] = cliente
        context.user_data["historico_conversa"] = ""
        context.user_data["tentativas"] = 0
        
        # Saudação personalizada
        await update.message.reply_text(
            f"🐦 Olá, {cliente.nome}! Que bom ter você de volta!\n\n"
            "Em que posso ajudar hoje?"
        )
        
        # Processar a mensagem normalmente
        return await tratar_mensagem(update, context)
    
    else:
        # Cliente não vinculado - iniciar fluxo de identificação
        logger.info(f"❌ Telegram {telegram_id} não vinculado a nenhum cliente")
        
        await update.message.reply_text(
            "🐦 Olá! Sou o Sabiah, seu assistente de suporte.\n\n"
            "Para começar, preciso identificar sua conta. "
            "Por favor, informe seu CNPJ, código de cliente ou e-mail."
        )
        
        return AGUARDANDO_IDENTIFICACAO


# Estados da conversa (continuação)
AGUARDANDO_CADASTRO_NOME = 2  # Novo estado: coletar nome
AGUARDANDO_CADASTRO_EMAIL = 3  # Novo estado: coletar e-mail
AGUARDANDO_CADASTRO_TELEFONE = 4  # Novo estado: coletar telefone
AGUARDANDO_CONFIRMAR_CADASTRO = 5  # Novo estado: confirmar dados
AGUARDANDO_NOME_ATENDENTE = 6  # Estado para vincular telegram com nome de atendente
AGUARDANDO_MENSAGEM = 10


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
            # Agora permite múltiplos vínculos por cliente
            vinculos = identificador.listar_telegram_vinculados(cliente.id)
            telegram_vinculado = any(v.telegram_id == telegram_id for v in vinculos)
            
            if not telegram_vinculado:
                # Perguntar nome da pessoa que está solicitando suporte (opcional)
                await update.message.reply_text(
                    "📎 Deseja vincular seu Telegram a este cliente? "
                    "(Isso permite atendimento para múltiplas empresas)\n\n"
                    "Digite seu nome para identificação no atendimento "
                    "(ou /pular para continuar sem nome):"
                )
                context.user_data["pendente_vinculo_telegram"] = {
                    "cliente": cliente,
                    "telegram_id": telegram_id
                }
                db.close()
                return AGUARDANDO_NOME_ATENDENTE
            
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
            # Cliente não encontrado - iniciar fluxo de auto-cadastro
            context.user_data["cadastro_identificador"] = texto
            context.user_data["cadastro_tipo"] = identificador.obter_tipo_identificador(texto)
            
            await update.message.reply_text(
                "🔔 Não encontrei sua conta no sistema.\n\n"
                "Mas posso fazer seu cadastro agora! "
                "Para isso, preciso de algumas informações.\n\n"
                "Por favor, informe seu *nome completo*:",
                parse_mode="Markdown"
            )
            db.close()
            return AGUARDANDO_CADASTRO_NOME
            
    except Exception as e:
        logger.error(f"Erro na identificação: {e}")
        await update.message.reply_text(
            "⚠️ Ocorreu um erro ao processar sua solicitação. "
            "Por favor, tente novamente."
        )
        db.close()
        return AGUARDANDO_IDENTIFICACAO


async def tratar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa mensagens do cliente identificado usando IA."""
    mensagem = update.message.text
    cliente: Cliente = context.user_data.get("cliente")
    telegram_id = update.effective_user.id
    
    if not cliente:
        await update.message.reply_text(
            "⚠️ Sessão expirada. Por favor, envie /start para iniciar novamente."
        )
        return AGUARDANDO_IDENTIFICACAO
    
    # Verificar se é uma mensagem de cancelamento
    if mensagem.lower() in ["cancelar", "/cancelar"]:
        await update.message.reply_text(
            "✅ Atendimento encerrado. Envie /start para iniciar novamente."
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    # Mostrar indicador de "digitando" para o usuário
    await update.message.chat.send_action("typing")
    
    try:
        # Obter provedor de IA
        provedor = get_provedor()
        
        # Obter sessão do banco
        db = next(get_db())
        
        # Criar serviço de contexto
        servico_contexto = ServicoContexto(db)
        
        # Processar mensagem com IA (passando telegram_id do atendente para isolamento)
        resposta, contexto, resposta_ia = servico_contexto.processar_mensagem(
            cliente=cliente,
            mensagem=mensagem,
            provedor_ia=provedor,
            atendente_telegram_id=telegram_id,
        )
        
        # Enviar resposta (sem Markdown - Telegram interpreta * como Markdown por padrão)
        await update.message.reply_text(resposta, parse_mode=None)
        
        # Atualizar histórico no contexto
        context.user_data["historico_conversa"] = contexto.historico
        
        # Incrementar número de tentativas
        tentativas = context.user_data.get("tentativas", 0) + 1
        context.user_data["tentativas"] = tentativas
        
        # Verificar necessidade de escalonamento
        detector = DetectorEscalonamento()
        resultado_deteccao = detector.analisar(
            resposta_ia=resposta_ia,
            mensagem_cliente=mensagem,
            numero_tentativas=tentativas,
        )
        
        if resultado_deteccao.necesita_escalonar:
            logger.info(f"🔔 Escalonamento necessário: {resultado_deteccao.motivo}")
            await mostrar_opcoes_escalonamento(
                update, context, mensagem=resultado_deteccao.mensagem
            )
        
        db.close()
        return AGUARDANDO_MENSAGEM
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem com IA: {e}")
        await update.message.reply_text(
            "⚠️ Desculpe, estou tendo dificuldades para processar sua solicitação. "
            "Por favor, tente novamente em alguns momentos."
        )
        return AGUARDANDO_MENSAGEM


async def tratar_cadastro_nome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Coleta o nome do cliente durante o auto-cadastro."""
    nome = update.message.text.strip()
    
    if len(nome) < 3:
        await update.message.reply_text(
            "⚠️ Nome inválido. Por favor, informe seu nome completo:"
        )
        return AGUARDANDO_CADASTRO_NOME
    
    context.user_data["cadastro_nome"] = nome
    
    await update.message.reply_text(
        f"✅ Ótimo, {nome}!\n\n"
        "Agora, informe seu *e-mail* para contato:",
        parse_mode="Markdown"
    )
    return AGUARDANDO_CADASTRO_EMAIL


async def tratar_cadastro_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Coleta o e-mail do cliente durante o auto-cadastro."""
    email = update.message.text.strip().lower()
    
    # Validar formato de e-mail
    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    if not EMAIL_REGEX.match(email):
        await update.message.reply_text(
            "⚠️ E-mail inválido. Por favor, informe um e-mail válido:"
        )
        return AGUARDANDO_CADASTRO_EMAIL
    
    context.user_data["cadastro_email"] = email
    
    await update.message.reply_text(
        "✅ E-mail cadastrado!\n\n"
        "Por último, informe seu *telefone* com DDD "
        "(ex: 11999999999):",
        parse_mode="Markdown"
    )
    return AGUARDANDO_CADASTRO_TELEFONE


async def tratar_cadastro_telefone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Coleta o telefone do cliente durante o auto-cadastro."""
    telefone = update.message.text.strip()
    
    # Remover caracteres não numéricos exceto +
    telefone_limpo = re.sub(r"[^\d+]", "", telefone)
    
    # Validar telefone brasileiro (com ou sem +55)
    if telefone_limpo.startswith("+55"):
        telefone_limpo = telefone_limpo[3:]
    
    if len(telefone_limpo) < 10 or len(telefone_limpo) > 11:
        await update.message.reply_text(
            "⚠️ Telefone inválido. Por favor, informe seu telefone com DDD "
            "(ex: 11999999999):"
        )
        return AGUARDANDO_CADASTRO_TELEFONE
    
    context.user_data["cadastro_telefone"] = telefone
    
    # Mostrar resumo para confirmação
    identificador = context.user_data.get("cadastro_identificador", "")
    nome = context.user_data.get("cadastro_nome", "")
    email = context.user_data.get("cadastro_email", "")
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirmar", callback_data="cadastro_confirmar"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cadastro_cancelar"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📋 *Confirme seus dados:*\n\n"
        f"*Identificador:* {identificador}\n"
        f"*Nome:* {nome}\n"
        f"*E-mail:* {email}\n"
        f"*Telefone:* {telefone}\n\n"
        f"Os dados estão corretos?",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
    return AGUARDANDO_CONFIRMAR_CADASTRO


async def confirmar_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirma e cria o cadastro do cliente."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cadastro_cancelar":
        await query.edit_message_text(
            "❌ Cadastro cancelado. Envie /start para tentar novamente."
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    # Criar o cliente no banco de dados
    db = next(get_db())
    identificador = IdentificacaoService(db)
    telegram_id = update.effective_user.id
    
    try:
        # Determinar qual campo usar com base no tipo de identificador
        identificador_original = context.user_data.get("cadastro_identificador", "")
        tipo = context.user_data.get("cadastro_tipo", "cnpj")
        
        kwargs = {
            "nome": context.user_data.get("cadastro_nome"),
            "email": context.user_data.get("cadastro_email"),
            "telefone": context.user_data.get("cadastro_telefone"),
        }
        
        # Adicionar o identificador correto
        if tipo == "cnpj":
            kwargs["cnpj"] = identificador_original
        elif tipo == "email":
            kwargs["email"] = identificador_original
        elif tipo == "codigo":
            kwargs["codigo_cliente"] = identificador_original
        
        # Criar cliente
        cliente = identificador.criar_cliente(**kwargs)
        
        # Vincular Telegram ID
        identificador.vincular_telegram(cliente, telegram_id)
        
        # Limpar dados de cadastro e salvar cliente
        context.user_data["cliente"] = cliente
        context.user_data["historico_conversa"] = ""
        context.user_data["tentativas"] = 0
        context.user_data.pop("cadastro_identificador", None)
        context.user_data.pop("cadastro_tipo", None)
        context.user_data.pop("cadastro_nome", None)
        context.user_data.pop("cadastro_email", None)
        context.user_data.pop("cadastro_telefone", None)
        
        await query.edit_message_text(
            f"🎉 *Cadastro realizado com sucesso!*\n\n"
            f"Bem-vindo, {cliente.nome}!\n\n"
            f"Seu CNPJ/Código foi vinculado ao seu Telegram.\n"
            f"A partir de agora, é só enviar suas dúvidas!",
            parse_mode="Markdown"
        )
        
        db.close()
        return AGUARDANDO_MENSAGEM
        
    except Exception as e:
        logger.error(f"Erro ao criar cliente: {e}")
        await query.edit_message_text(
            "⚠️ Ocorreu um erro ao processar seu cadastro. "
            "Por favor, tente novamente com /start"
        )
        db.close()
        return ConversationHandler.END


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela a conversa."""
    await update.message.reply_text(
        "✅ Conversa cancelada. Envie /start para iniciar novamente."
    )
    context.user_data.clear()
    return ConversationHandler.END


async def tratar_nome_atendente(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Trata o nome da pessoa que está solicitando suporte para vincular ao Telegram."""
    texto = update.message.text.strip()
    telegram_id = update.effective_user.id
    
    # Obter dados pendentes
    pendente = context.user_data.get("pendente_vinculo_telegram")
    if not pendente:
        await update.message.reply_text(
            "❌ Sessão expirada. Envie /start para continuar."
        )
        return ConversationHandler.END
    
    cliente = pendente["cliente"]
    
    # Verificar se é comando /pular
    nome_solicitante = None
    if texto.lower() != "/pular":
        nome_solicitante = texto
    
    db = next(get_db())
    identificador = IdentificacaoService(db)
    
    try:
        # Vincular Telegram ID com nome do solicitante
        identificador.vincular_telegram(cliente, telegram_id, nome_solicitante)
        
        # Salvar cliente no contexto
        context.user_data["cliente"] = cliente
        context.user_data["historico_conversa"] = ""
        context.user_data["tentativas"] = 0
        context.user_data.pop("pendente_vinculo_telegram", None)
        
        msg = f"✅ Olá, {cliente.nome}! Seu Telegram foi vinculado."
        if nome_solicitante:
            msg += f"\n📋 Identificação: {nome_solicitante}"
        msg += "\n\nComo posso ajudar hoje?"
        
        await update.message.reply_text(msg)
        
        db.close()
        return AGUARDANDO_MENSAGEM
        
    except Exception as e:
        logger.error(f"Erro ao vincular telegram: {e}")
        await update.message.reply_text(
            "⚠️ Erro ao vincular Telegram. Tente novamente com /start"
        )
        db.close()
        return ConversationHandler.END


async def pular_nome_atendente(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pula a etapa de nome do atendente."""
    telegram_id = update.effective_user.id
    
    # Obter dados pendentes
    pendente = context.user_data.get("pendente_vinculo_telegram")
    if not pendente:
        await update.message.reply_text(
            "❌ Sessão expirada. Envie /start para continuar."
        )
        return ConversationHandler.END
    
    cliente = pendente["cliente"]
    
    db = next(get_db())
    identificador = IdentificacaoService(db)
    
    try:
        # Vincular Telegram ID sem nome do atendente
        identificador.vincular_telegram(cliente, telegram_id, None)
        
        # Salvar cliente no contexto
        context.user_data["cliente"] = cliente
        context.user_data["historico_conversa"] = ""
        context.user_data["tentativas"] = 0
        context.user_data.pop("pendente_vinculo_telegram", None)
        
        await update.message.reply_text(
            f"✅ Olá, {cliente.nome}! Seu Telegram foi vinculado.\n\n"
            "Como posso ajudar hoje?"
        )
        
        db.close()
        return AGUARDANDO_MENSAGEM
        
    except Exception as e:
        logger.error(f"Erro ao vincular telegram: {e}")
        await update.message.reply_text(
            "⚠️ Erro ao vincular Telegram. Tente novamente com /start"
        )
        db.close()
        return ConversationHandler.END


def get_conversation_handler() -> ConversationHandler:
    """Retorna o ConversationHandler principal."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start_command),
            # Handler para processar qualquer mensagem automaticamente
            MessageHandler(filters.TEXT & ~filters.COMMAND, tratar_mensagem_automatica),
        ],
        states={
            AGUARDANDO_IDENTIFICACAO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tratar_identificacao)
            ],
            AGUARDANDO_CADASTRO_NOME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tratar_cadastro_nome)
            ],
            AGUARDANDO_CADASTRO_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tratar_cadastro_email)
            ],
            AGUARDANDO_CADASTRO_TELEFONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tratar_cadastro_telefone)
            ],
            AGUARDANDO_CONFIRMAR_CADASTRO: [
                CallbackQueryHandler(confirmar_cadastro, pattern="^cadastro_")
            ],
            AGUARDANDO_NOME_ATENDENTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tratar_nome_atendente)
            ],
            AGUARDANDO_MENSAGEM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tratar_mensagem)
            ],
        },
        fallbacks=[
            CommandHandler("cancelar", cancelar),
            CommandHandler("start", start_command),
            CommandHandler("pular", pular_nome_atendente),
        ],
    )


def get_callback_handler():
    """Retorna o handler de callbacks inline."""
    # Handler para callbacks de escalonamento
    return CallbackQueryHandler(tratar_callback_escalonamento, pattern="^escalonar_")
