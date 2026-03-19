# 🐦 Sabiah

**SuportIA inteligente via Telegram**

Sabiah é um bot de suporte ao cliente alimentado por inteligência artificial, projetado para operar via Telegram. Ele realiza o primeiro atendimento de forma autônoma, resolve questões conhecidas com base em uma base de conhecimento estruturada e, quando necessário, escalona o atendimento para um humano ou abre chamados automaticamente no Freshdesk.

O nome **Sabiah** é inspirado no sabiá, pássaro brasileiro símbolo de inteligência e comunicação — qualidades essenciais para um assistente de suporte eficiente.

---

## Visão Geral da Arquitetura

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Cliente   │────▶│ Telegram Bot │────▶│   Motor de IA   │
│  (Telegram) │◀────│   (Python)   │◀────│ (Multi-provedor)│
└─────────────┘     └──────┬───────┘     └────────┬────────┘
                           │                      │
                    ┌──────▼───────┐       ┌──────▼────────┐
                    │  SQLite      │       │   ChromaDB    │
                    │  (Dados)     │       │   (Vetores)   │
                    └──────────────┘       └───────────────┘
                           │
                    ┌──────▼───────┐
                    │  Helpdesk    │
                    │ (Multi-canal)│
                    └──────────────┘
```

---

## Stack Tecnológica

| Componente | Tecnologia | Justificativa |
|---|---|---|
| **Linguagem** | Python | Ecossistema rico para IA, chatbots e integrações |
| **Canal principal** | Telegram Bot API | Plataforma gratuita, com recursos nativos de bot, botões e menus |
| **Provedor de IA inicial** | Google Gemini (free tier) | Generoso limite gratuito, boa qualidade de resposta |
| **Arquitetura de IA** | Multi-provedor | Preparado para trocar ou adicionar provedores (OpenAI, Groq, Ollama, etc.) |
| **Banco de dados** | SQLite | Simples, sem servidor, ideal para validação. Migração futura para PostgreSQL |
| **Banco vetorial** | ChromaDB | Busca semântica na base de conhecimento, persistência automática, metadados integrados |
| **Base de conhecimento** | Arquivos Markdown/JSON | Fácil edição e atualização da documentação do software |
| **Canal de helpdesk** | Multi-canal de suporte | Interface abstrata para múltiplos canais (Freshdesk, JIRA, Zoho, E-mail, etc.) |

---

## Camadas de Memória

O Sabiah opera com três camadas de memória distintas, garantindo respostas contextualizadas e personalizadas:

### Memória Geral

Representa o conhecimento base sobre o software atendido. Inclui documentação, FAQs, tutoriais, problemas conhecidos e suas soluções. Essa memória é compartilhada entre todos os clientes e é alimentada por arquivos Markdown e JSON indexados no ChromaDB para busca semântica. Atualizada pela equipe de suporte conforme o software evolui.

### Memória do Cliente

Armazena o histórico de interação individual de cada cliente. Inclui conversas anteriores, tickets abertos, preferências e nível de satisfação. Permite que o bot ofereça um atendimento personalizado, lembrando de interações passadas e evitando que o cliente repita informações. Persistida no SQLite, vinculada ao ID do Telegram do cliente.

### Memória do Domínio do Cliente

Contém informações específicas do ambiente de cada cliente: versão do software utilizada, módulos contratados, configurações ativas e integrações habilitadas. Essa camada permite que o bot forneça respostas precisas e contextualizadas ao ambiente real do cliente, sem respostas genéricas. Persistida no SQLite, alimentada pelo cadastro do cliente.

---

## Fluxo de Atendimento

```
Cliente inicia conversa no Telegram
        │
        ▼
  Identificação do cliente
  (CNPJ, código ou e-mail)
        │
        ▼
  ┌─────────────────────────────────────┐
  │ Cliente encontrado no banco de dados │──▶ Vinculação ao cadastro
  │         (Memória do cliente + domínio)          │
  └─────────────────────────────────────┘
        │
        ▼
  ┌─────────────────────────────────────┐
  │ Cliente NÃO encontrado              │──▶ Fluxo de Auto-cadastro
  │ (primeiro contato)                  │    │
  └─────────────────────────────────────┘    │
        │                                   │
        ▼                                   ▼
  IA tenta resolver a questão    1. Solicitar nome completo
  (Busca semântica + contexto)   2. Solicitar e-mail
                                   3. Solicitar telefone
                                   4. Confirmar dados
                                   5. Criar cliente + vincular Telegram
        │                                   │
        ▼                                   ▼
  ├── ✅ Resolvido ──▶ Pesquisa de satisfação
  │
  └── ❌ Não resolvido
          │
          ▼
  Opções de escalonamento:
  ├── 🔄 Reformular pergunta
  ├── 🎫 Abrir ticket no Helpdesk (automático, via canal configurado)
  ├── 👤 Atendimento humano (notifica equipe)
  └── 📞 Solicitar callback (coleta telefone)
```

---

## Funcionalidades e Automações

### Atendimento ao Cliente (via Telegram)

- Atendimento autônomo por IA com busca semântica na base de conhecimento
- Identificação e vinculação automática do cliente pelo Telegram
- **Auto-cadastro**: clientes não encontrados podem se cadastrar diretamente pelo bot (coleta nome, e-mail e telefone com confirmação)
- Respostas contextualizadas com base no domínio do cliente (versão, plano, módulos)
- Histórico de conversas preservado para continuidade do atendimento
- Consulta de status de tickets do Helpdesk (via canal configurado) diretamente pelo bot

### Escalonamento

- Abertura automática de ticket no Helpdesk (via canal configurado) com histórico da conversa anexado
- Escalonamento para atendimento humano com notificação da equipe
- Solicitação de callback telefônico

### Automações Internas (via Telegram — grupo da equipe)

- Pesquisa de satisfação automática após encerramento do atendimento
- Relatórios periódicos (diários/semanais) enviados no grupo interno da equipe
- Métricas: atendimentos realizados, taxa de resolução pela IA, escalonamentos, temas frequentes, satisfação média

---

## Preparação para o Futuro

Embora o foco inicial seja o Telegram, a arquitetura do Sabiah é modular e preparada para evolução:

| Evolução | Descrição |
|---|---|
| **WhatsApp** | Adicionar canal via API (Twilio, Z-API ou Evolution API) |
| **Chat Web** | Página de chat própria no domínio da empresa |
| **JIRA** | Adicionar canal via API |
| **Zoho Desk** | Adicionar canal via API |
| **E-mail** | Adicionar canal de abertura de tickets via e-mail (sem API) |
| **PostgreSQL** | Migração do SQLite quando o volume crescer |
| **Dashboard Web** | Painel com gráficos e métricas em tempo real |
| **Múltiplos provedores de IA** | Trocar ou combinar Gemini, OpenAI, Groq, Ollama |

---

## Checklist de Implementação

### Fase 1 — Estrutura Base
- [ ] Estrutura do projeto Python (pastas, dependências, configuração)
- [ ] Configuração do bot no Telegram (BotFather, token)
- [ ] Conexão básica: bot recebe e responde mensagens no Telegram
- [ ] Configuração do SQLite (schema de tabelas)
- [ ] Módulo de identificação e vinculação do cliente

### Fase 2 — Motor de IA
- [ ] Integração com Google Gemini API (free tier)
- [ ] Arquitetura multi-provedor (interface abstrata para trocar provedores)
- [ ] Configuração do ChromaDB para busca vetorial
- [ ] Indexação da base de conhecimento (Markdown/JSON → ChromaDB)
- [ ] Lógica de construção de prompt com contexto (memória geral + cliente + domínio)

### Fase 3 — Camadas de Memória
- [ ] Memória Geral: carregamento e indexação de arquivos de documentação
- [ ] Memória do Cliente: registro de histórico de conversas no SQLite
- [ ] Memória do Domínio: cadastro e consulta de dados do ambiente do cliente
- [ ] Lógica de contexto combinado nas respostas da IA

### Fase 4 — Escalonamento
- [x] Detecção de necessidade de escalonamento (baixa confiança, insatisfação)
- [x] Menu de opções de escalonamento (botões no Telegram)
- [x] Notificação da equipe de suporte (grupo interno no Telegram)
- [x] Solicitação de callback (coleta de telefone)
- [x] Integração com Helpdesk (interface abstrata): criação de tickets (implementação inicial com Freshdesk)
- [x] Integração com Helpdesk (interface abstrata): consulta de status de tickets (implementação inicial com Freshdesk)

### Fase 5 — Automações e Métricas
- [x] Pesquisa de satisfação pós-atendimento (botões no Telegram)
- [x] Armazenamento de métricas de atendimento
- [x] Relatório diário automático no grupo da equipe
- [x] Relatório semanal com métricas consolidadas

### Fase 6 — Refinamento e Testes
- [x] Testes com cenários reais de suporte
- [x] Ajuste de prompts e qualidade das respostas
- [x] Tratamento de edge cases (mensagens vazias, spam, idiomas, etc.)
- [x] Documentação de uso para a equipe de suporte
- [x] Documentação de como atualizar a base de conhecimento

### Fase Futura
- [ ] Canal WhatsApp
- [ ] Chat web próprio
- [ ] Migração para PostgreSQL
- [ ] Dashboard web com métricas
- [ ] Suporte a múltiplos idiomas

---

## Como Contribuir

Este projeto está em fase inicial de desenvolvimento. Contribuições, sugestões e feedbacks são bem-vindos. Abra uma issue ou envie um pull request.

---

## Licença

A definir.
