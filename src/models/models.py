"""Modelos de dados do Sabiah."""

from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Classe base para todos os modelos."""
    pass


class Cliente(Base):
    """Modelo de Cliente."""
    
    __tablename__ = "clientes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Telegram ID não é mais unique=True - permite múltiplos vínculos por CNPJ e um Telegram para múltiplas empresas
    telegram_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    cnpj: Mapped[str] = mapped_column(String(18), unique=True, nullable=True)
    codigo_cliente: Mapped[str] = mapped_column(String(50), unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=True, index=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    telefone: Mapped[str] = mapped_column(String(20), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Domínio do cliente
    versao_software: Mapped[str] = mapped_column(String(20), nullable=True)
    plano: Mapped[str] = mapped_column(String(50), nullable=True)
    modulos: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    conversas: Mapped[list["Conversa"]] = relationship(
        "Conversa", back_populates="cliente", cascade="all, delete-orphan"
    )
    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="cliente", cascade="all, delete-orphan"
    )
    # Novos relacionamentos para múltiplos Telegrams por cliente
    telegram_vinculos: Mapped[list["TelegramCliente"]] = relationship(
        "TelegramCliente", back_populates="cliente", cascade="all, delete-orphan"
    )


class TelegramCliente(Base):
    """Modelo de vínculo entre Telegram e Cliente (permite múltiplos vínculos)."""
    
    __tablename__ = "telegram_cliente"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    telegram_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    nome_atendente: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Timestamps
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Relacionamentos
    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="telegram_vinculos")


class Conversa(Base):
    """Modelo de Histórico de Conversa."""
    
    __tablename__ = "conversas"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.id"), nullable=True, index=True)
    telegram_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    # Campo para isolar conversas por atendente - cada atendente vê apenas suas próprias conversas
    atendente_telegram_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    
    # Mensagens
    mensagem_usuario: Mapped[str] = mapped_column(Text, nullable=False)
    mensagem_bot: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Contexto
    fonte: Mapped[str] = mapped_column(String(20), default="telegram")  # telegram, whatsapp, web
    resolvido: Mapped[bool] = mapped_column(Boolean, default=False)
    satisfacao: Mapped[int] = mapped_column(Integer, nullable=True)  # 1-5
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Relacionamentos
    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="conversas")


class Ticket(Base):
    """Modelo de Ticket do Helpdesk."""
    
    __tablename__ = "tickets"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.id"), nullable=True, index=True)
    telegram_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    # Campo para isolar tickets por atendente - cada atendente vê apenas seus próprios tickets
    atendente_telegram_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    
    # Dados do ticket externo
    ticket_externo_id: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    canal: Mapped[str] = mapped_column(String(20), default="telegram")  # telegram, freshdesk, email
    
    # Informações
    assunto: Mapped[str] = mapped_column(String(500), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="aberto")  # aberto, pendente, resolvido, fechado
    prioridade: Mapped[str] = mapped_column(String(20), default="media")  # baixa, media, alta, critica
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    closed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Relacionamentos
    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="tickets")


class Metrica(Base):
    """Modelo de Métricas de Atendimento."""
    
    __tablename__ = "metricas"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    data: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    
    # Contadores
    total_atendimentos: Mapped[int] = mapped_column(Integer, default=0)
    resolvidos_ia: Mapped[int] = mapped_column(Integer, default=0)
    escalonamentos: Mapped[int] = mapped_column(Integer, default=0)
    tickets_criados: Mapped[int] = mapped_column(Integer, default=0)
    
    # Satisfação (média)
    satisfacao_media: Mapped[float] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
