"""Serviço de Contexto Unificado - Combina todas as camadas de memória."""

import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from src.models import Cliente
from src.ai.prompts import PromptBuilder
from src.memory.memoria_geral import MemoriaGeral
from src.memory.memoria_cliente import MemoriaCliente
from src.memory.memoria_dominio import MemoriaDominio

logger = logging.getLogger(__name__)


@dataclass
class ContextoAtendimento:
    """Contexto completo para um atendimento."""
    cliente: Cliente
    mensagem: str
    prompt_sistema: str
    historico: list[dict]
    base_conhecimento: str


class ServicoContexto:
    """
    Serviço unificado de contexto que combina todas as camadas de memória.
    
    Este serviço é responsável por:
    1. Buscar contexto na memória geral (base de conhecimento)
    2. Buscar contexto na memória do cliente (histórico)
    3. Buscar contexto na memória do domínio (ambiente do cliente)
    4. Construir o prompt completo para a IA
    """
    
    def __init__(self, db: Session):
        """
        Inicializa o serviço de contexto.
        
        Args:
            db: Sessão do banco de dados
        """
        self.db = db
        self.memoria_geral = MemoriaGeral()
        self.memoria_cliente = MemoriaCliente(db)
        self.memoria_dominio = MemoriaDominio(db)
    
    def preparar_atendimento(
        self,
        cliente: Cliente,
        mensagem: str,
        n_resultados_busca: int = 5,
        limite_historico: int = 10,
    ) -> ContextoAtendimento:
        """
        Prepara o contexto completo para um atendimento.
        
        Args:
            cliente: Cliente
            mensagem: Mensagem do usuário
            n_resultados_busca: Número de resultados da busca na base de conhecimento
            limite_historico: Limite de mensagens do histórico
            
        Returns:
            ContextoAtendimento com todas as informações necessárias
        """
        logger.info(f"📋 Preparando contexto para cliente {cliente.id}")
        
        # 1. Buscar na memória geral (base de conhecimento)
        resultados_gerais = self.memoria_geral.buscar(
            mensagem,
            n_resultados=n_resultados_busca
        )
        base_conhecimento = self.memoria_geral.formatar_resultados(resultados_gerais)
        
        # 2. Buscar na memória do cliente (histórico)
        historico = self.memoria_cliente.buscar_historico_formatado(
            cliente,
            limite=limite_historico
        )
        
        # 3. Construir contexto do cliente para o prompt
        contexto_cliente = {
            "nome": cliente.nome,
            "versao_software": cliente.versao_software,
            "plano": cliente.plano,
            "modulos": self.memoria_dominio._parse_modulos(cliente.modulos),
        }
        
        # 4. Construir o prompt usando o PromptBuilder
        prompt_sistema, historico_ia = PromptBuilder.criar_resposta(
            base_conhecimento=base_conhecimento,
            cliente=contexto_cliente,
            historico=historico,
        )
        
        return ContextoAtendimento(
            cliente=cliente,
            mensagem=mensagem,
            prompt_sistema=prompt_sistema,
            historico=historico_ia,
            base_conhecimento=base_conhecimento,
        )
    
    def salvar_atendimento(
        self,
        cliente: Cliente,
        mensagem_usuario: str,
        mensagem_bot: str,
        resolvido: bool = False,
    ) -> None:
        """
        Salva o atendimento no histórico do cliente.
        
        Args:
            cliente: Cliente
            mensagem_usuario: Mensagem do usuário
            mensagem_bot: Resposta do bot
            resolvido: Se foi resolvido
        """
        self.memoria_cliente.adicionar_mensagem(
            cliente=cliente,
            mensagem_usuario=mensagem_usuario,
            mensagem_bot=mensagem_bot,
            resolvido=resolvido,
        )
    
    def processar_mensagem(
        self,
        cliente: Cliente,
        mensagem: str,
        provedor_ia,
    ) -> tuple[str, ContextoAtendimento]:
        """
        Processa uma mensagem do cliente e retorna a resposta da IA.
        
        Args:
            cliente: Cliente
            mensagem: Mensagem do usuário
            provedor_ia: Instância do provedor de IA
            
        Returns:
            Tuple (resposta_da_ia, contexto)
        """
        # Preparar contexto
        contexto = self.preparar_atendimento(cliente, mensagem)
        
        # Enviar para a IA
        resposta = provedor_ia.chat(
            mensagem=mensagem,
            sistema=contexto.prompt_sistema,
            historico=contexto.historico,
        )
        
        # Salvar no histórico
        self.salvar_atendimento(
            cliente=cliente,
            mensagem_usuario=mensagem,
            mensagem_bot=resposta.conteudo,
        )
        
        return resposta.conteudo, contexto
