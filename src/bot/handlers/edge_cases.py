"""Handlers para tratar edge cases e mensagens especiais."""

import logging
import re
from typing import Optional

from telegram import Update
from telegram.ext import (
    MessageHandler,
    filters,
    ContextTypes,
)

logger = logging.getLogger(__name__)


class EdgeCaseHandler:
    """
    Handler para tratar edge cases e mensagens especiais.
    """
    
    # Padrões de mensagens de spam
    SPAM_PATTERNS = [
        r"(?i)(click aqui|ganhe|gratis|promoção|marketing|viagra|casino)",
        r"(?i)(seguidor|likes|followers|instagram|tiktok)",
        r"(?i)(invite|forward|copy|share this)",
    ]
    
    # Mensagens de saudação
    SAUDACOES = [
        "olá", "ola", "oi", "bom dia", "boa tarde", "boa noite",
        "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
    ]
    
    # Mensagens de despedida
    DESPEDIDAS = [
        "obrigado", "obrigada", "tchau", "bye", "até logo", "até mais",
        "vlw", "valeu", "thanks", "thank you", "goodbye",
    ]
    
    # Mensagens de confirmação
    CONFIRMACAO = [
        "sim", "yes", "ok", "okay", "claro", "com certeza", "entendi",
        "entendeu", "recebi", "perfeito", "perfeita", "blz", "beleza",
    ]
    
    # Mensagens de negativa
    NEGACAO = [
        "não", "nao", "no", "nunca", "nem", "jamais", "nope",
    ]
    
    # Palavras de emergência
    EMERGENCIA = [
        "urgente", "emergencia", "emergency", "crítico", "crítica",
        "não consigo", "sistema fora", "parou", "caiu", "erro crítico",
    ]
    
    @staticmethod
    def detectar_tipo_mensagem(mensagem: str) -> str:
        """
        Detecta o tipo de mensagem.
        
        Args:
            mensagem: Texto da mensagem
            
        Returns:
            Tipo de mensagem detectado
        """
        texto = mensagem.lower().strip()
        
        # Verificar se é spam
        if EdgeCaseHandler._eh_spam(texto):
            return "spam"
        
        # Verificar se é saudação
        if EdgeCaseHandler._eh_saudacao(texto):
            return "saudacao"
        
        # Verificar se é despedida
        if EdgeCaseHandler._eh_despedida(texto):
            return "despedida"
        
        # Verificar se é confirmação
        if EdgeCaseHandler._eh_confirmacao(texto):
            return "confirmacao"
        
        # Verificar se é negativa
        if EdgeCaseHandler._eh_negacao(texto):
            return "negacao"
        
        # Verificar se é emergência
        if EdgeCaseHandler._eh_emergencia(texto):
            return "emergencia"
        
        # Verificar se é muito curta
        if len(texto) < 3:
            return "muito_curta"
        
        return "normal"
    
    @staticmethod
    def _eh_spam(texto: str) -> bool:
        """Verifica se a mensagem é spam."""
        for padrao in EdgeCaseHandler.SPAM_PATTERNS:
            if re.search(padrao, texto):
                return True
        return False
    
    @staticmethod
    def _eh_saudacao(texto: str) -> bool:
        """Verifica se é uma saudação."""
        return texto in EdgeCaseHandler.SAUDACOES
    
    @staticmethod
    def _eh_despedida(texto: str) -> bool:
        """Verifica se é uma despedida."""
        return texto in EdgeCaseHandler.DESPEDIDAS
    
    @staticmethod
    def _eh_confirmacao(texto: str) -> bool:
        """Verifica se é uma confirmação."""
        return texto in EdgeCaseHandler.CONFIRMACAO
    
    @staticmethod
    def _eh_negacao(texto: str) -> bool:
        """Verifica se é uma negativa."""
        return texto in EdgeCaseHandler.NEGACAO
    
    @staticmethod
    def _eh_emergencia(texto: str) -> bool:
        """Verifica se é uma emergência."""
        for palavra in EdgeCaseHandler.EMERGENCIA:
            if palavra in texto:
                return True
        return False
    
    @staticmethod
    def gerar_resposta(tipo: str, contexto: Optional[dict] = None) -> Optional[str]:
        """
        Gera uma resposta apropriada para o tipo de mensagem.
        
        Args:
            tipo: Tipo de mensagem
            contexto: Contexto adicional (opcional)
            
        Returns:
            Resposta gerada ou None
        """
        respostas = {
            "saudacao": (
                "👋Olá! Sou o Sabiah, seu assistente de suporte.\n\n"
                "Para começar, preciso identificar sua conta. "
                "Por favor, informe seu CNPJ, código de cliente ou e-mail."
            ),
            "despedida": (
                "👋Obrigado por entrar em contato! "
                "Se precisar de mais alguma coisa, é só chamar.\n\n"
                "Tenha um ótimo dia! 😊"
            ),
            "confirmacao": (
                "✅Entendido! Como posso ajudar você hoje?"
            ),
            "negacao": (
                "Entendi. Se precisar de algo, é só perguntar!"
            ),
            "emergencia": (
                "⚠️ Entendo que você está com uma questão urgente. "
                "Vou abrir as opções de escalonamento para que você possa "
                "falar com um atendente o mais rápido possível."
            ),
            "muito_curta": (
                "🤔 Pode me dar mais detalhes? "
                "Assim posso te ajudar melhor."
            ),
            "spam": (
                "⚠️ Mensagem não autorizada. "
                "Por favor, evite enviar spam."
            ),
        }
        
        return respostas.get(tipo)


async def tratar_edge_case(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    """
    Trata edge cases e retorna resposta se aplicável.
    
    Args:
        update: Update do Telegram
        context: Contexto do bot
        
    Returns:
        Resposta ou None se não for edge case
    """
    mensagem = update.message.text.strip()
    tipo = EdgeCaseHandler.detectar_tipo_mensagem(mensagem)
    
    # Se for um edge case conhecido, responder
    if tipo in ["saudacao", "despedida", "confirmacao", "negacao", 
                "emergencia", "muito_curta", "spam"]:
        resposta = EdgeCaseHandler.gerar_resposta(tipo)
        if resposta:
            await update.message.reply_text(resposta)
            logger.info(f"📝 Edge case tratado: {tipo}")
            return resposta
    
    return None


# Filtros para edge cases
class EdgeCaseFilters:
    """Filtros prontos para usar nos handlers."""
    
    @staticmethod
    def is_saudacao() -> filters.MessageFilter:
        """Filtro para mensagens de saudação."""
        padrao = "|".join(EdgeCaseHandler.SAUDACOES)
        return filters.Regex(f"(?i)^{padrao}$")
    
    @staticmethod
    def is_despedida() -> filters.MessageFilter:
        """Filtro para mensagens de despedida."""
        padrao = "|".join(EdgeCaseHandler.DESPEDIDAS)
        return filters.Regex(f"(?i)^{padrao}$")
    
    @staticmethod
    def is_spam() -> filters.MessageFilter:
        """Filtro para mensagens de spam."""
        padroes = "|".join(EdgeCaseHandler.SPAM_PATTERNS)
        return filters.Regex(padroes)
    
    @staticmethod
    def is_curta() -> filters.MessageFilter:
        """Filtro para mensagens muito curtas (< 3 caracteres)."""
        return filters.Regex(r"^.{0,2}$")
