# AGENTS.md - Sabiah

## Purpose

**Sabiah** is an AI-powered customer support bot designed to operate via Telegram. It provides intelligent first-line support by:
- Resolving known issues using a structured knowledge base
- Performing semantic search on documentation
- Escalating to human agents or creating tickets in Freshdesk when needed

The name is inspired by the "sabiá", a Brazilian bird symbolizing intelligence and communication.

## Quick Start

### Prerequisites

- Python 3.10+
- Telegram Bot Token (get from @BotFather)

### Environment Setup

Create a `.env` file based on `.env.example`:

```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_token_here

# AI Providers (choose one):
# Option 1: Groq (recommended - free and fast)
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.1-70b-versatile

# Option 2: Google Gemini
GEMINI_API_KEY=your_gemini_key

# Optional: Freshdesk integration
FRESHDESK_API_KEY=your_freshdesk_key
FRESHDESK_SUBDOMAIN=yourcompany
```

### Installation & Running

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python run.py
```

## Build & Test Commands

```bash
# Initialize database (done automatically by run.py)
python -c "from src.models.database import init_db; init_db()"

# Run with custom database path
DATABASE_PATH=data/sabiah.db python run.py

# Run with debug mode (enable SQL logging)
# Edit src/models/database.py and set echo=True

# Install dev dependencies (future)
# pip install -r requirements-dev.txt

# Run tests (future)
# pytest tests/
```

## Code Patterns & Conventions

### Project Structure

```
src/
├── ai/           # AI providers (Strategy pattern)
├── bot/          # Telegram bot handlers
├── config/       # Configuration (Pydantic Settings)
├── knowledge/    # Knowledge base processing
├── memory/       # 3-layer memory system
├── models/       # SQLAlchemy ORM models
└── services/    # Business logic services
```

### Key Design Patterns

1. **Factory Pattern** (`src/ai/factory.py`): Creates AI provider instances based on configuration
2. **Strategy Pattern**: Abstract base class (`ProvedorIA`) allows swapping AI providers
3. **Repository Pattern**: Memory layers abstract data access
4. **Dependency Injection**: Settings and database sessions injected via factory functions

### Coding Standards

- **Language**: Portuguese (Brazilian) for code comments and documentation
- **Type Hints**: Use Python type hints for all function signatures
- **Dataclasses**: Use `@dataclass` for data transfer objects (e.g., `RespostaIA`)
- **Pydantic**: Use Pydantic `BaseSettings` for configuration
- **SQLAlchemy**: Use ORM with explicit relationships
- **Error Handling**: Raise specific exceptions, log errors

### File Naming

- Use Portuguese names: `memoria_cliente.py`, `identificacao.py`
- Use snake_case for Python files and functions
- Use PascalCase for classes

### Git Conventions

- Branch naming: `feature/`, `fix/`, `docs/`
- Commit messages: Clear, concise descriptions in Portuguese
- See `.gitignore` for excluded patterns (venv, .env, *.db, chroma_db/)

## Project Structure

```
/workspace/project/sabiah/
├── src/
│   ├── ai/                    # AI providers
│   │   ├── base.py           # Abstract base class for AI providers
│   │   ├── factory.py        # Factory for creating AI provider instances
│   │   ├── gemini.py         # Google Gemini integration
│   │   ├── groq.py           # Groq integration
│   │   └── prompts.py        # Prompt templates
│   ├── bot/                   # Telegram bot
│   │   ├── bot.py            # Main bot setup
│   │   └── handlers/         # Message handlers
│   │       ├── mensagens.py  # Main message handler
│   │       ├── escalonamento.py  # Escalation logic
│   │       ├── satisfacao.py     # Satisfaction surveys
│   │       └── edge_cases.py     # Edge case handling
│   ├── config/               # Configuration
│   │   ├── settings.py       # Settings management
│   │   └── logging.py        # Logging configuration
│   ├── knowledge/            # Knowledge base processing
│   ├── memory/               # Memory layers
│   │   ├── memoria_geral.py      # General knowledge (shared)
│   │   ├── memoria_cliente.py    # Client-specific history
│   │   └── memoria_dominio.py    # Client domain info
│   ├── models/               # Database models
│   │   ├── models.py         # SQLAlchemy models
│   │   └── database.py      # Database connection
│   └── services/            # Business services
│       ├── identificacao.py     # Client identification
│       ├── escalonamento.py     # Ticket creation
│       ├── metricas.py          # Metrics/reporting
│       └── notificacao_equipe.py # Team notifications
├── data/knowledge/          # Knowledge base files (Markdown/JSON)
├── docs/                   # Documentation
├── migrations/             # Database migrations
├── run.py                  # Entry point
└── requirements.txt       # Python dependencies
```

### Key Architecture Components

- **Telegram Bot API**: Main communication channel
- **Multi-provider AI**: Supports Groq (recommended) and Gemini
- **ChromaDB**: Vector database for semantic search
- **SQLite**: Relational database for client data
- **3-layer Memory System**:
  1. General Memory - Shared documentation/FAQ
  2. Client Memory - Individual conversation history
  3. Domain Memory - Client-specific environment data

## Testing Requirement

**IMPORTANT**: Each feature must include corresponding tests.

Currently, the repository has **no test files**. When implementing features:
- Create tests under a `tests/` directory
- Use pytest or unittest framework
- Test both unit and integration scenarios

## Technical Decisions

### Architecture Choices

| Decision | Rationale |
|----------|-----------|
| **SQLite** | Simple, serverless, ideal for MVP/validation. Future migration to PostgreSQL planned |
| **ChromaDB** | Semantic search for knowledge base, automatic persistence, integrated metadata |
| **Multi-provider AI** | Allows swapping providers (Groq/Gemini/OpenAI/Ollama) without changing core logic |
| **Factory Pattern** | Dynamic AI provider instantiation based on available API keys |
| **3-layer Memory** | Separation of concerns: general knowledge, client history, domain context |

### Why Groq?

- **Free tier**: ~60 requests/minute
- **Speed**: Low latency responses
- **Recommendation**: Use Groq as default, Gemini as fallback

### Database Schema

- **SQLAlchemy ORM** with explicit relationships
- **Alembic** ready for future migrations
- See `src/models/models.py` for entity definitions

### Message Handling Flow

```
Telegram Message → Handler → Identification → AI Service → Memory Layers → Response
                      ↓                                    ↓
              Client Lookup                    Knowledge Base (ChromaDB)
```

## Relevant Documentation

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Groq API](https://console.groq.com/docs)
- [Google Gemini](https://ai.google.dev/docs)
- [ChromaDB](https://docs.trychroma.com/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [python-telegram-bot](https://python-telegram-bot.org/)

## CI/CD

**No GitHub workflows configured.** The repository does not have a `.github/workflows` folder.

Consider adding:
- Linting (e.g., flake8, pylint)
- Pre-commit hooks
- Test automation
