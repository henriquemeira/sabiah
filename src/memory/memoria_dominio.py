"""Serviço de Memória do Domínio - Dados do Ambiente do Cliente."""

import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from src.models import Cliente

logger = logging.getLogger(__name__)


class MemoriaDominio:
    """
    Memória do Domínio do Cliente do Sabiah.
    
    Contém informações específicas do ambiente de cada cliente:
    versão do software utilizada, módulos contratados, configurações ativas e integrações habilitadas.
    """
    
    def __init__(self, db: Session):
        """
        Inicializa a Memória do Domínio.
        
        Args:
            db: Sessão do banco de dados
        """
        self.db = db
    
    def get_dados(self, cliente: Cliente) -> dict:
        """
        Retorna os dados do domínio do cliente.
        
        Args:
            cliente: Cliente
            
        Returns:
            Dicionário com dados do domínio
        """
        dados = {
            "versao_software": cliente.versao_software,
            "plano": cliente.plano,
            "modulos": self._parse_modulos(cliente.modulos),
        }
        
        # Filtrar valores None
        return {k: v for k, v in dados.items() if v is not None}
    
    def _parse_modulos(self, modulos_str: Optional[str]) -> list[str]:
        """
        Parses the modulos string into a list.
        
        Args:
            modulos_str: String JSON com módulos
            
        Returns:
            Lista de módulos
        """
        if not modulos_str:
            return []
        
        try:
            modulos = json.loads(modulos_str)
            if isinstance(modulos, list):
                return modulos
        except json.JSONDecodeError:
            pass
        
        # Se não for JSON, tratar como string única
        return [modulos_str] if modulos_str else []
    
    def atualizar_versao(self, cliente: Cliente, versao: str) -> None:
        """
        Atualiza a versão do software do cliente.
        
        Args:
            cliente: Cliente
            versao: Versão do software
        """
        cliente.versao_software = versao
        self.db.commit()
        logger.info(f"📌 Versão atualizada para {cliente.id}: {versao}")
    
    def atualizar_plano(self, cliente: Cliente, plano: str) -> None:
        """
        Atualiza o plano do cliente.
        
        Args:
            cliente: Cliente
            plano: Nome do plano
        """
        cliente.plano = plano
        self.db.commit()
        logger.info(f"💳 Plano atualizado para {cliente.id}: {plano}")
    
    def atualizar_modulos(self, cliente: Cliente, modulos: list[str]) -> None:
        """
        Atualiza os módulos do cliente.
        
        Args:
            cliente: Cliente
            modulos: Lista de módulos
        """
        cliente.modulos = json.dumps(modulos)
        self.db.commit()
        logger.info(f"📦 Módulos atualizados para {cliente.id}: {modulos}")
    
    def adicionar_modulo(self, cliente: Cliente, modulo: str) -> None:
        """
        Adiciona um módulo ao cliente.
        
        Args:
            cliente: Cliente
            modulo: Nome do módulo
        """
        modulos = self._parse_modulos(cliente.modulos)
        if modulo not in modulos:
            modulos.append(modulo)
            self.atualizar_modulos(cliente, modulos)
    
    def remover_modulo(self, cliente: Cliente, modulo: str) -> None:
        """
        Remove um módulo do cliente.
        
        Args:
            cliente: Cliente
            modulo: Nome do módulo
        """
        modulos = self._parse_modulos(cliente.modulos)
        if modulo in modulos:
            modulos.remove(modulo)
            self.atualizar_modulos(cliente, modulos)
    
    def formatar_para_ia(self, cliente: Cliente) -> str:
        """
        Formata os dados do domínio para inclusão no prompt da IA.
        
        Args:
            cliente: Cliente
            
        Returns:
            Texto formatado com informações do domínio
        """
        dados = self.get_dados(cliente)
        
        if not dados:
            return ""
        
        partes = ["### Contexto do Ambiente do Cliente"]
        
        if dados.get("versao_software"):
            partes.append(f"**Versão do Software**: {dados['versao_software']}")
        
        if dados.get("plano"):
            partes.append(f"**Plano**: {dados['plano']}")
        
        modulos = dados.get("modulos", [])
        if modulos:
            partes.append(f"**Módulos Contratados**: {', '.join(modulos)}")
        
        return "\n".join(partes)
    
    def tem_modulo(self, cliente: Cliente, modulo: str) -> bool:
        """
        Verifica se o cliente tem um módulo específico.
        
        Args:
            cliente: Cliente
            modulo: Nome do módulo
            
        Returns:
            True se o cliente tem o módulo
        """
        modulos = self._parse_modulos(cliente.modulos)
        return modulo in modulos
    
    def get_plano_tier(self, cliente: Cliente) -> int:
        """
        Retorna o tier do plano (1=Básico, 2=Intermediário, 3=Avançado).
        
        Args:
            cliente: Cliente
            
        Returns:
            Tier do plano
        """
        plano = (cliente.plano or "").lower()
        
        if "basic" in plano or "basico" in plano or "iniciante" in plano:
            return 1
        elif "pro" in plano or "avancado" in plano or "premium" in plano:
            return 3
        elif "intermediario" in plano or "medio" in plano or "business" in plano:
            return 2
        
        return 0  # Desconhecido
