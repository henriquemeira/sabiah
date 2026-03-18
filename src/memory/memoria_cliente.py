"""Serviço de Memória do Cliente - Histórico de Conversas."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from src.models import Cliente, Conversa

logger = logging.getLogger(__name__)


class MemoriaCliente:
    """
    Memória do Cliente do Sabiah.
    
    Armazena o histórico de interação individual de cada cliente.
    Inclui conversas anteriores, tickets abertos, preferências e nível de satisfação.
    """
    
    def __init__(self, db: Session):
        """
        Inicializa a Memória do Cliente.
        
        Args:
            db: Sessão do banco de dados
        """
        self.db = db
    
    def adicionar_mensagem(
        self,
        cliente: Cliente,
        mensagem_usuario: str,
        mensagem_bot: Optional[str] = None,
        resolvido: bool = False,
    ) -> Conversa:
        """
        Adiciona uma mensagem ao histórico do cliente.
        
        Args:
            cliente: Cliente
            mensagem_usuario: Mensagem enviada pelo usuário
            mensagem_bot: Resposta do bot (opcional)
            resolvido: Se a questão foi resolvida
            
        Returns:
            Conversa criada
        """
        conversa = Conversa(
            cliente_id=cliente.id,
            telegram_id=cliente.telegram_id,
            mensagem_usuario=mensagem_usuario,
            mensagem_bot=mensagem_bot,
            fonte="telegram",
            resolvido=resolvido,
        )
        
        self.db.add(conversa)
        self.db.commit()
        self.db.refresh(conversa)
        
        logger.info(f"💬 Mensagem adicionada ao histórico do cliente {cliente.id}")
        return conversa
    
    def buscar_historico(
        self,
        cliente: Cliente,
        limite: int = 10,
    ) -> list[Conversa]:
        """
        Busca o histórico de conversas do cliente.
        
        Args:
            cliente: Cliente
            limite: Número máximo de mensagens a retornar
            
        Returns:
            Lista de conversas
        """
        return (
            self.db.query(Conversa)
            .filter(Conversa.cliente_id == cliente.id)
            .order_by(Conversa.created_at.desc())
            .limit(limite)
            .all()
        )
    
    def buscar_historico_formatado(
        self,
        cliente: Cliente,
        limite: int = 10,
    ) -> list[dict]:
        """
        Busca o histórico de conversas formatado para a IA.
        
        Args:
            cliente: Cliente
            limite: Número máximo de mensagens
            
        Returns:
            Lista de mensagens no formato [{"role": "user/assistant", "content": "..."}]
        """
        conversas = self.buscar_historico(cliente, limite)
        
        historico = []
        # Converter para formato da IA (mais antigas primeiro)
        for conversa in reversed(conversas):
            historico.append({
                "role": "user",
                "content": conversa.mensagem_usuario,
            })
            if conversa.mensagem_bot:
                historico.append({
                    "role": "assistant",
                    "content": conversa.mensagem_bot,
                })
        
        return historico
    
    def definir_satisfacao(
        self,
        cliente: Cliente,
        satisfacao: int,
    ) -> None:
        """
        Define a satisfação do último atendimento.
        
        Args:
            cliente: Cliente
            satisfacao: Nota de 1 a 5
        """
        # Buscar última conversa não avaliada
        conversa = (
            self.db.query(Conversa)
            .filter(Conversa.cliente_id == cliente.id)
            .filter(Conversa.satisfacao.is_(None))
            .order_by(Conversa.created_at.desc())
            .first()
        )
        
        if conversa:
            conversa.satisfacao = satisfacao
            self.db.commit()
            logger.info(f"⭐ Satisfação definida: {satisfacao} para cliente {cliente.id}")
    
    def get_ultima_conversa(self, cliente: Cliente) -> Optional[Conversa]:
        """Retorna a última conversa do cliente."""
        return (
            self.db.query(Conversa)
            .filter(Conversa.cliente_id == cliente.id)
            .order_by(Conversa.created_at.desc())
            .first()
        )
    
    def get_estatisticas(self, cliente: Cliente) -> dict:
        """
        Retorna estatísticas do cliente.
        
        Args:
            cliente: Cliente
            
        Returns:
            Dicionário com estatísticas
        """
        conversas = self.db.query(Conversa).filter(Conversa.cliente_id == cliente.id).all()
        
        total = len(conversas)
        resolvidas = sum(1 for c in conversas if c.resolvido)
        
        satisfacoes = [c.satisfacao for c in conversas if c.satisfacao is not None]
        satisfacao_media = sum(satisfacoes) / len(satisfacoes) if satisfacoes else None
        
        return {
            "total_atendimentos": total,
            "resolvidos": resolvidas,
            "taxa_resolucao": resolvidas / total if total > 0 else 0,
            "satisfacao_media": satisfacao_media,
            "ultima_conversa": conversas[0].created_at.isoformat() if conversas else None,
        }


def formatar_historico_para_ia(historico: list[Conversa]) -> list[dict]:
    """
    Formata o histórico de conversas para envio à IA.
    
    Args:
        historico: Lista de conversas
        
    Returns:
        Lista de mensagens no formato para IA
    """
    msgs = []
    for c in historico:
        msgs.append({"role": "user", "content": c.mensagem_usuario})
        if c.mensagem_bot:
            msgs.append({"role": "assistant", "content": c.mensagem_bot})
    return msgs
