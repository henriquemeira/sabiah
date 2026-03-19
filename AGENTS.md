# AGENTS.md - Sabiah

## Purpose

**Sabiah** is an AI-powered customer support bot designed to operate via Telegram. It provides intelligent first-line support by:
- Resolving known issues using a structured knowledge base
- Performing semantic search on documentation
- Escalating to human agents or creating tickets in Freshdesk when needed

The name is inspired by the "sabiá", a Brazilian bird symbolizing intelligence and communication.

## Setup

### Environment Variables

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
```

### Dependencies

Install with:
```bash
pip install -r requirements.txt
```

### Running

```bash
python run.py
```

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

## CI/CD

**No GitHub workflows configured.** The repository does not have a `.github/workflows` folder.

Consider adding:
- Linting (e.g., flake8, pylint)
- Pre-commit hooks
- Test automation
