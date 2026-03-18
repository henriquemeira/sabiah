"""Script de inicialização do Sabiah."""

from src.models.database import init_db


def main():
    """Inicializa o banco de dados e inicia o bot."""
    print("🐦 Inicializando Sabiah...")
    
    # Inicializar banco de dados
    print("📦 Criando tabelas do banco de dados...")
    init_db()
    print("✅ Banco de dados pronto!")
    
    # Iniciar bot
    print("🤖 Iniciando bot...")
    from src.bot.bot import main as bot_main
    bot_main()


if __name__ == "__main__":
    main()
