"""Serviço de identificação e vinculação de clientes."""

import re
from typing import Optional

from sqlalchemy.orm import Session

from src.models import Cliente


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
        """Busca cliente por Telegram ID."""
        return self.db.query(Cliente).filter(Cliente.telegram_id == telegram_id).first()
    
    def vincular_telegram(self, cliente: Cliente, telegram_id: int) -> Cliente:
        """
        Vincula um Telegram ID a um cliente existente.
        
        Args:
            cliente: Cliente a ser vinculado
            telegram_id: ID do Telegram do usuário
            
        Returns:
            Cliente atualizado
        """
        # Verificar se o Telegram ID já está vinculado a outro cliente
        cliente_existente = self.buscar_por_telegram_id(telegram_id)
        if cliente_existente and cliente_existente.id != cliente.id:
            raise ValueError(
                f"Telegram ID {telegram_id} já está vinculado a outro cliente"
            )
        
        cliente.telegram_id = telegram_id
        self.db.commit()
        self.db.refresh(cliente)
        return cliente
    
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
