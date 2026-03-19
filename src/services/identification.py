"""Serviço de identificação e vinculação de clientes."""

import re
from typing import Optional, List

from sqlalchemy.orm import Session

from src.models import Cliente, TelegramCliente


class ClienteNaoEncontrado(Exception):
    """Exceção levantada quando o cliente não é encontrado."""
    pass


class IdentificacaoService:
    """Serviço para identificar e vincular clientes."""
    
    # Regex para validar CNPJ
    CNPJ_REGEX = re.compile(r"^\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}$")
    
    # Regex para validar e-mail
    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    
    def __init__(self, db: Session):
        """Inicializa o serviço com sessão do banco de dados."""
        self.db = db
    
    def identificar(self, texto: str) -> Optional[Cliente]:
        """
        Identifica um cliente com base em CNPJ, código, e-mail ou Telegram ID.
        
        Args:
            texto: Texto contendo CNPJ, código de cliente, e-mail ou ID numérico
            
        Returns:
            Cliente encontrado ou None
        """
        texto = texto.strip()
        
        # Tentar identificar por CNPJ
        if self._eh_cnpj(texto):
            return self.buscar_por_cnpj(texto)
        
        # Tentar identificar por e-mail
        if self._eh_email(texto):
            return self.buscar_por_email(texto)
        
        # Tentar identificar por código de cliente
        if self._eh_codigo(texto):
            return self.buscar_por_codigo(texto)
        
        # Tentar identificar por Telegram ID (número)
        if texto.isdigit():
            return self.buscar_por_telegram_id(int(texto))
        
        return None
    
    def _eh_cnpj(self, texto: str) -> bool:
        """Verifica se o texto parece um CNPJ."""
        return bool(self.CNPJ_REGEX.match(texto))
    
    def _eh_email(self, texto: str) -> bool:
        """Verifica se o texto parece um e-mail."""
        return bool(self.EMAIL_REGEX.match(texto))
    
    def _eh_codigo(self, texto: str) -> bool:
        """Verifica se o texto parece um código de cliente."""
        # Código de cliente: geralmente alfanumérico, 4-20 caracteres
        return 3 <= len(texto) <= 20
    
    def buscar_por_cnpj(self, cnpj: str) -> Optional[Cliente]:
        """Busca cliente por CNPJ."""
        return self.db.query(Cliente).filter(Cliente.cnpj == cnpj).first()
    
    def buscar_por_email(self, email: str) -> Optional[Cliente]:
        """Busca cliente por e-mail."""
        return self.db.query(Cliente).filter(Cliente.email == email.lower()).first()
    
    def buscar_por_codigo(self, codigo: str) -> Optional[Cliente]:
        """Busca cliente por código de cliente."""
        return self.db.query(Cliente).filter(Cliente.codigo_cliente == codigo).first()
    
    def buscar_por_telegram_id(self, telegram_id: int) -> Optional[Cliente]:
        """
        Busca cliente por Telegram ID.
        
        Primeiro verifica na tabela de vínculos TelegramCliente (múltiplos),
        depois verifica no campo telegram_id do Cliente (legado).
        
        Args:
            telegram_id: ID do Telegram do usuário
            
        Returns:
            Cliente encontrado ou None
        """
        # Primeiro, buscar na tabela de vínculos múltiplos
        vinculo = self.db.query(TelegramCliente).filter(
            TelegramCliente.telegram_id == telegram_id
        ).first()
        
        if vinculo:
            return vinculo.cliente
        
        # Fallback: buscar no campo direto do cliente (legado)
        return self.db.query(Cliente).filter(Cliente.telegram_id == telegram_id).first()
    
    def buscar_vinculos_por_telegram_id(self, telegram_id: int) -> List[TelegramCliente]:
        """
        Busca todos os vínculos de um Telegram ID (para múltiplas empresas).
        
        Args:
            telegram_id: ID do Telegram do usuário
            
        Returns:
            Lista de vínculos encontrados
        """
        return self.db.query(TelegramCliente).filter(
            TelegramCliente.telegram_id == telegram_id
        ).all()
    
    def listar_telegram_vinculados(self, cliente_id: int) -> List[TelegramCliente]:
        """
        Lista todos os Telegrams vinculados a um cliente.
        
        Args:
            cliente_id: ID do cliente
            
        Returns:
            Lista de vínculos
        """
        return self.db.query(TelegramCliente).filter(
            TelegramCliente.cliente_id == cliente_id
        ).all()
    
    def vincular_telegram(
        self, 
        cliente: Cliente, 
        telegram_id: int, 
        nome_atendente: Optional[str] = None
    ) -> TelegramCliente:
        """
        Vincula um Telegram ID a um cliente existente.
        
        Agora permite múltiplos vínculos - um Telegram pode estar vinculado
        a múltiplos clientes e um cliente pode ter múltiplos Telegrams.
        
        Args:
            cliente: Cliente a ser vinculado
            telegram_id: ID do Telegram do usuário
            nome_atendente: Nome do atendente (opcional)
            
        Returns:
            Vinculo criado
        """
        # Verificar se já existe vínculo entre este cliente e este telegram_id
        vinculo_existente = self.db.query(TelegramCliente).filter(
            TelegramCliente.cliente_id == cliente.id,
            TelegramCliente.telegram_id == telegram_id
        ).first()
        
        if vinculo_existente:
            # Já vinculado, retorna o vínculo existente
            return vinculo_existente
        
        # Criar novo vínculo na tabela intermediária
        vinculo = TelegramCliente(
            cliente_id=cliente.id,
            telegram_id=telegram_id,
            nome_atendente=nome_atendente
        )
        self.db.add(vinculo)
        
        # Também mantém o campo legadowebsite (para compatibilidade)
        if cliente.telegram_id is None:
            cliente.telegram_id = telegram_id
        
        self.db.commit()
        self.db.refresh(vinculo)
        return vinculo
    
    def desvincular_telegram(self, cliente: Cliente, telegram_id: int) -> bool:
        """
        Desvincula um Telegram ID de um cliente.
        
        Args:
            cliente: Cliente que terá o vínculo removido
            telegram_id: ID do Telegram do usuário
            
        Returns:
            True se desvinculado com sucesso, False se não existia vínculo
        """
        vinculo = self.db.query(TelegramCliente).filter(
            TelegramCliente.cliente_id == cliente.id,
            TelegramCliente.telegram_id == telegram_id
        ).first()
        
        if not vinculo:
            return False
        
        self.db.delete(vinculo)
        
        # Se não houver mais vínculos, limpar o campo legado
        vinculos_restantes = self.db.query(TelegramCliente).filter(
            TelegramCliente.telegram_id == telegram_id
        ).count()
        
        if vinculos_restantes == 0:
            cliente.telegram_id = None
        
        self.db.commit()
        return True
    
    def criar_cliente(
        self,
        nome: str,
        cnpj: Optional[str] = None,
        email: Optional[str] = None,
        codigo_cliente: Optional[str] = None,
        telefone: Optional[str] = None,
    ) -> Cliente:
        """
        Cria um novo cliente no sistema.
        
        Args:
            nome: Nome do cliente
            cnpj: CNPJ (opcional)
            email: E-mail (opcional)
            codigo_cliente: Código do cliente (opcional)
            telefone: Telefone (opcional)
            
        Returns:
            Cliente criado
        """
        # Normalizar dados
        if cnpj:
            cnpj = self._normalizar_cnpj(cnpj)
        if email:
            email = email.lower()
        
        # Verificar duplicatas
        if cnpj and self.buscar_por_cnpj(cnpj):
            raise ValueError(f"CNPJ {cnpj} já está cadastrado")
        if email and self.buscar_por_email(email):
            raise ValueError(f"E-mail {email} já está cadastrado")
        if codigo_cliente and self.buscar_por_codigo(codigo_cliente):
            raise ValueError(f"Código {codigo_cliente} já está cadastrado")
        
        cliente = Cliente(
            nome=nome,
            cnpj=cnpj,
            email=email,
            codigo_cliente=codigo_cliente,
            telefone=telefone,
        )
        self.db.add(cliente)
        self.db.commit()
        self.db.refresh(cliente)
        return cliente
    
    def _normalizar_cnpj(self, cnpj: str) -> str:
        """Normaliza o CNPJ removendo caracteres especiais."""
        return re.sub(r"[^\d]", "", cnpj)
    
    def obter_tipo_identificador(self, texto: str) -> str:
        """
        Retorna o tipo de identificador baseado no formato do texto.
        
        Args:
            texto: Texto a ser analisado
            
        Returns:
            Tipo do identificador: 'cnpj', 'email', 'codigo' ou 'desconhecido'
        """
        texto = texto.strip()
        
        if self._eh_cnpj(texto):
            return "cnpj"
        if self._eh_email(texto):
            return "email"
        if self._eh_codigo(texto):
            return "codigo"
        
        return "desconhecido"


def formatar_cnpj(cnpj: str) -> str:
    """Formata CNPJ no padrão XX.XXX.XXX/XXXX-XX."""
    cnpj = re.sub(r"[^\d]", "", cnpj)
    if len(cnpj) != 14:
        return cnpj
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
