"""Serviço de detecção de necessidade de escalonamento."""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.ai.base import RespostaIA

logger = logging.getLogger(__name__)


class MotivoEscalonamento(str, Enum):
    """Motivos pelos quais o atendimento deve ser escalonado."""
    BAIXA_CONFIANCA = "baixa_confianca"
    CLIENTE_INSATISFEITO = "cliente_insatisfeito"
    SOLICITACAO_EXPLICITA = "solicitacao_explicita"
    ERRO_TECNICO = "erro_tecnico"
    FORA_DO_ESCOPO = "fora_do_escopo"
    DADOS_INSUFICIENTES = "dados_insuficientes"


class TipoEscalonamento(str, Enum):
    """Tipos de escalonamento disponíveis."""
    ABRIR_TICKET = "abrir_ticket"
    ATENDIMENTO_HUMANO = "atendimento_humano"
    CALLBACK = "callback"
    REFORMULAR = "reformular"


@dataclass
class ResultadoDetecção:
    """Resultado da detecção de necessidade de escalonamento."""
    necesita_escalonar: bool
    motivo: Optional[MotivoEscalonamento] = None
    confianca: float = 0.0
    recomendacao: Optional[TipoEscalonamento] = None
    mensagem: str = ""


class DetectorEscalonamento:
    """
    Serviço para detectar quando o atendimento precisa ser escalonado.
    
    Analisa:
    - Confiança da resposta da IA
    - Satisfação implícita do cliente
    - Padrões de mensagens que indicam necessidade de escalonamento
    - Erros técnicos
    """
    
    # Threshold de confiança abaixo do qual deve escalar
    THRESHOLD_CONFIANCA_BAIXA = 0.5
    
    # Threshold para escalonamento imediato
    THRESHOLD_CONFIANCA_MUITO_BAIXA = 0.3
    
    # Palavras que indicam insatisfação
    PALAVRAS_INSATISFACAO = [
        "não resolvedor", "não resolveu", "não funcionou", "não funciona",
        "isso não ajuda", "não é isso", "errado", "falando com humano",
        "quero falar com alguém", "atendente", "suporte humano",
        "péssimo", "horrível", "nunca funciona", "de novo",
        "já tentei", "não consigo", "impossível", "não dá",
    ]
    
    # Palavras que indicam solicitação explícita de escalonamento
    PALAVRAS_ESCALONAMENTO = [
        "abrir ticket", "criar chamado", "chamar atendente",
        "falar com atendente", "contato humano", "ligar para mim",
        "me liga", "callback", "retornar ligação", "whatsapp",
    ]
    
    # Palavras que indicam erro técnico
    PALAVRAS_ERRO_TECNICO = [
        "erro", "falha", "bug", "crash", "travou", "lento",
        "não carrega", "tela branca", "500", "404", "timeout",
    ]
    
    def __init__(self, threshold_confianca: float = THRESHOLD_CONFIANCA_BAIXA):
        """
        Inicializa o detector de escalonamento.
        
        Args:
            threshold_confianca: Threshold de confiança para considerar necessária a escala
        """
        self.threshold_confianca = threshold_confianca
    
    def analisar(
        self,
        resposta_ia: Optional[RespostaIA] = None,
        mensagem_cliente: Optional[str] = None,
        numero_tentativas: int = 0,
    ) -> ResultadoDetecção:
        """
        Analisa se o atendimento precisa ser escalonado.
        
        Args:
            resposta_ia: Resposta retornada pela IA
            mensagem_cliente: Última mensagem do cliente
            numero_tentativas: Número de tentativas já realizadas
            
        Returns:
            ResultadoDetecção com a análise
        """
        logger.info("🔍 Analisando necessidade de escalonamento...")
        
        # 1. Verificar confiança da IA
        if resposta_ia and resposta_ia.confidence is not None:
            if resposta_ia.confidence < self.THRESHOLD_CONFIANCA_MUITO_BAIXA:
                return ResultadoDetecção(
                    necesita_escalonar=True,
                    motivo=MotivoEscalonamento.BAIXA_CONFIANCA,
                    confianca=resposta_ia.confidence,
                    recomendacao=TipoEscalonamento.ABRIR_TICKET,
                    mensagem="A IA está com muita baixa confiança na resposta.",
                )
            elif resposta_ia.confidence < self.threshold_confianca:
                return ResultadoDetecção(
                    necesita_escalonar=True,
                    motivo=MotivoEscalonamento.BAIXA_CONFIANCA,
                    confianca=resposta_ia.confidence,
                    recomendacao=TipoEscalonamento.REFORMULAR,
                    mensagem="A IA não está confiante o suficiente. Deseja reformular a pergunta?",
                )
        
        # 2. Verificar insatisfação do cliente
        if mensagem_cliente:
            insatisfacao = self._detectar_insatisfacao(mensagem_cliente)
            if insatisfacao:
                return ResultadoDetecção(
                    necesita_escalonar=True,
                    motivo=MotivoEscalonamento.CLIENTE_INSATISFEITO,
                    confianca=insatisfacao,
                    recomendacao=TipoEscalonamento.ATENDIMENTO_HUMANO,
                    mensagem="Parece que você não ficou satisfeito(a) com a resposta. "
                           "Posso abrir um ticket ou transferir para um atendente.",
                )
            
            # 3. Verificar solicitação explícita de escalonamento
            if self._detectar_solicitacao_escalonamento(mensagem_cliente):
                return ResultadoDetecção(
                    necesita_escalonar=True,
                    motivo=MotivoEscalonamento.SOLICITACAO_EXPLICITA,
                    confianca=1.0,
                    recomendacao=TipoEscalonamento.ATENDIMENTO_HUMANO,
                    mensagem="Entendi. Vou abrir as opções de escalonamento para você.",
                )
            
            # 4. Verificar erro técnico
            if self._detectar_erro_tecnico(mensagem_cliente):
                return ResultadoDetecção(
                    necesita_escalonar=True,
                    motivo=MotivoEscalonamento.ERRO_TECNICO,
                    confianca=0.9,
                    recomendacao=TipoEscalonamento.ABRIR_TICKET,
                    mensagem="Parece que você está enfrentando um erro técnico. "
                           "Vou abrir um ticket para nossa equipe técnica.",
                )
        
        # 5. Verificar número de tentativas
        if numero_tentativas >= 3:
            logger.info(f"🔄 Número de tentativas excedido: {numero_tentativas}")
            return ResultadoDetecção(
                necesita_escalonar=True,
                motivo=MotivoEscalonamento.BAIXA_CONFIANCA,
                confianca=0.8,
                recomendacao=TipoEscalonamento.ABRIR_TICKET,
                mensagem="Já tentamos algumas vezes e não conseguimos resolver. "
                       "Posso abrir um ticket ou transferir para um atendente.",
            )
        
        # Não precisa escalar
        return ResultadoDetecção(
            necesita_escalonar=False,
            confianca=1.0,
            mensagem="Atendimento prosseguindo normalmente.",
        )
    
    def _detectar_insatisfacao(self, mensagem: str) -> Optional[float]:
        """
        Detecta insatisfação na mensagem do cliente.
        
        Args:
            mensagem: Mensagem do cliente
            
        Returns:
            Float de 0-1 indicando nível de insatisfação, ou None
        """
        mensagem_lower = mensagem.lower()
        
        palavras_encontradas = [
            p for p in self.PALAVRAS_INSATISFACAO if p in mensagem_lower
        ]
        
        if palavras_encontradas:
            # Calcular confiança baseada no número de palavras encontradas
            confianca = min(len(palavras_encontradas) / 3, 1.0)
            logger.info(f"😕 Insatisfação detectada: {palavras_encontradas}")
            return confianca
        
        return None
    
    def _detectar_solicitacao_escalonamento(self, mensagem: str) -> bool:
        """
        Detecta solicitação explícita de escalonamento.
        
        Args:
            mensagem: Mensagem do cliente
            
        Returns:
            True se detectou solicitação de escalonamento
        """
        mensagem_lower = mensagem.lower()
        
        for palavra in self.PALAVRAS_ESCALONAMENTO:
            if palavra in mensagem_lower:
                logger.info(f"📢 Solicitação de escalonamento detectada: {palavra}")
                return True
        
        return False
    
    def _detectar_erro_tecnico(self, mensagem: str) -> bool:
        """
        Detecta menção a erro técnico.
        
        Args:
            mensagem: Mensagem do cliente
            
        Returns:
            True se detectou erro técnico
        """
        mensagem_lower = mensagem.lower()
        
        for palavra in self.PALAVRAS_ERRO_TECNICO:
            if palavra in mensagem_lower:
                logger.info(f"⚠️ Erro técnico detectado: {palavra}")
                return True
        
        return False
