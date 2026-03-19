#!/usr/bin/env python3
"""
Script de migração para adicionar a coluna atendente_telegram_id
às tabelas conversas e tickets.

Execute com: python migrations/add_atendente_telegram_id.py
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.models.database import get_engine, init_db


def run_migration():
    """Executa a migração para adicionar a coluna atendente_telegram_id."""
    engine = get_engine()
    
    # Primeiro, garante que o banco existe
    print("📦 Verificando/Criando tabelas do banco de dados...")
    init_db()
    
    with engine.connect() as conn:
        # Verificar se a coluna já existe na tabela conversas
        result = conn.execute(text("PRAGMA table_info(conversas)"))
        columns = [row[1] for row in result]
        
        if "atendente_telegram_id" not in columns:
            print("➕ Adicionando coluna 'atendente_telegram_id' na tabela 'conversas'...")
            conn.execute(text(
                "ALTER TABLE conversas ADD COLUMN atendente_telegram_id INTEGER"
            ))
            conn.commit()
            print("✅ Coluna adicionada na tabela 'conversas'!")
        else:
            print("ℹ️  Coluna 'atendente_telegram_id' já existe na tabela 'conversas'")
        
        # Verificar se a coluna já existe na tabela tickets
        result = conn.execute(text("PRAGMA table_info(tickets)"))
        columns = [row[1] for row in result]
        
        if "atendente_telegram_id" not in columns:
            print("➕ Adicionando coluna 'atendente_telegram_id' na tabela 'tickets'...")
            conn.execute(text(
                "ALTER TABLE tickets ADD COLUMN atendente_telegram_id INTEGER"
            ))
            conn.commit()
            print("✅ Coluna adicionada na tabela 'tickets'!")
        else:
            print("ℹ️  Coluna 'atendente_telegram_id' já existe na tabela 'tickets'")
        
        # Verificar se a coluna já existe na tabela telegram_cliente
        result = conn.execute(text("PRAGMA table_info(telegram_cliente)"))
        columns = [row[1] for row in result]
        
        if "atendente_telegram_id" not in columns:
            print("➕ Adicionando coluna 'atendente_telegram_id' na tabela 'telegram_cliente'...")
            conn.execute(text(
                "ALTER TABLE telegram_cliente ADD COLUMN atendente_telegram_id INTEGER"
            ))
            conn.commit()
            print("✅ Coluna adicionada na tabela 'telegram_cliente'!")
        else:
            print("ℹ️  Coluna 'atendente_telegram_id' já existe na tabela 'telegram_cliente'")
    
    print("\n🎉 Migração concluída com sucesso!")
    print("   Você já pode usar o recurso de suporte/tickets.")


if __name__ == "__main__":
    run_migration()
