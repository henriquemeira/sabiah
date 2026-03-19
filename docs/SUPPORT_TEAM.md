# 📖 Documentação do Sabiah - Equipe de Suporte

## Visão Geral

O **Sabiah** é um assistente de suporte inteligente que utiliza inteligência artificial para atender clientes de forma autônoma via Telegram. Ele é capaz de:

- Identificar clientes automaticamente
- Responder perguntas usando a base de conhecimento
- Escalonar atendimentos quando necessário
- Abrir tickets no sistema de helpdesk
- Coletar feedback de satisfação

---

## Primeiros Passos

### 1. Configuração Inicial

Antes de usar o Sabiah, configure as seguintes variáveis de ambiente:

```bash
# Token do Bot (obtido via @BotFather no Telegram)
TELEGRAM_BOT_TOKEN=seu_token_aqui

# ID do grupo da equipe para notificações
TELEGRAM_GRUPO_ID=seu_grupo_id_aqui

# API do Gemini (Google AI Studio)
GEMINI_API_KEY=sua_api_key_aqui

# Freshdesk (opcional)
FRESHDESK_API_KEY=sua_api_key_aqui
FRESHDESK_SUBDOMAIN=sua_empresa
```

### 2. Iniciando o Bot

```bash
cd /workspace/project/sabiah
python -m src.bot.bot
```

---

## Fluxo de Atendimento

### 2.1 Cliente Inicia Conversa

O cliente envia `/start` ou uma mensagem no Telegram. O Sabiah solicita identificação:

```
🐦 Olá! Sou o Sabiah, seu assistente de suporte.

Para começar, preciso identificar sua conta. 
Por favor, informe seu CNPJ, código de cliente ou e-mail.
```

### 2.2 Identificação do Cliente

O cliente pode se identificar por:
- **CNPJ**: `12.345.678/0001-90`
- **E-mail**: `cliente@empresa.com`
- **Código**: `CLI12345`

Após identificado, o cliente pode fazer perguntas normalmente.

### 2.3 Atendimento pela IA

A IA tenta resolver a questão usando:
1. Base de conhecimento (documentação)
2. Histórico do cliente
3. Dados do domínio (versão, plano, módulos)

### 2.4 Resolução ou Escalonamento

- **Resolvido**: Pesquisa de satisfação é enviada
- **Não resolvido**: Menu de escalonamento é apresentado

---

## Escalonamento

### Opções Disponíveis

O cliente pode escolher entre:

| Opção | Descrição |
|-------|-----------|
| 🎫 Abrir Ticket | Cria um ticket no helpdesk |
| 👤 Falar com Atendente | Transfere para atendimento humano |
| 📞 Solicitar Callback | Coleta telefone para retorno |
| 🔄 Reformular Pergunta | Tenta novamente |

### Notificações da Equipe

Quando um cliente solicita escalonamento, o grupo da equipe recebe uma notificação com:
- Dados do cliente
- Tipo de solicitação
- Ticket ID (se criado)

---

## Pesquisas de Satisfação

Após cada atendimento, o cliente avalia com estrelas:

```
📊 Pesquisa de Satisfação

Por favor, avalie seu atendimento de hoje:

😁 Muito Satisfeito  |  🙂 Satisfeito  |  😐 Neutro
😕 Insatisfeito     |  😞 Muito Insatisfeito
```

As avaliações são armazenadas e podem ser consultadas nos relatórios.

---

## Relatórios

### Relatório Diário

Enviado automaticamente todos os dias às 19:00, contém:
- Total de atendimentos
- Taxa de resolução pela IA
- Número de escalonamentos
- Satisfação média
- Temas mais frequentes

### Relatório Semanal

Enviado toda segunda-feira às 9:00, contém:
- Métricas da semana
- Comparação com semana anterior
- Temas mais frequentes
- Tendências

---

## Comandos do Bot

| Comando | Descrição |
|---------|-----------|
| `/start` | Iniciar atendimento |
| `/help` | Ver ajuda |
| `/status` | Ver tickets do cliente |

---

## Troubleshooting

### Bot não responde

1. Verificar se o bot está em execução
2. Verificar token do Telegram
3. Verificar logs em `logs/sabiah.log`

### Cliente não identificado

1. Verificar se CNPJ/e-mail está cadastrado
2. Verificar dados no banco SQLite

### Tickets não criados no Freshdesk

1. Verificar credenciais da API
2. Verificar subdomain está correto
3. Verificar permissões da API

---

## Perguntas Frequentes

**P: O Sabiah substitui o atendimento humano?**
R: Não. O Sabiah faz o primeiro atendimento e resolve questões simples. Questões complexas são escalonadas.

**P: Como atualizar a base de conhecimento?**
R: Edite os arquivos em `data/knowledge/` e reindexe com o script de indexação.

**P: O que fazer se a IA der respostas erradas?**
R: Ajuste o prompt em `src/ai/prompts.py` ou adicione mais documentos na base de conhecimento.

---

## Contato

Para dúvidas ou problemas, entre em contato com a equipe de desenvolvimento.
