# 1. OBJECTIVE

Avaliar o fluxo de atendimento ao cliente quanto à política de vinculação entre Telegram ID e dados do cliente (CNPJ), e propor uma solução para permitir que:
- Uma mesma pessoa possa iniciar atendimento para diferentes empresas/clientes
- Empresas com único Telegram possam atender por múltiplos funcionários

**Problema identificado:** Ao tentar criar novo cadastro com CNPJ diferente usando um Telegram ID já vinculado, o sistema retorna erro "Telegram ID X já está vinculado a outro cliente".

# 2. CONTEXT SUMMARY

**Componentes relevantes:**
- `src/models/models.py` - Modelo Cliente com campo `telegram_id` (unique=True, linha 21)
- `src/services/identification.py` - Método `vincular_telegram()` que valida e impeça vínculo duplicado (linhas 88-109)
- `src/bot/handlers/mensagens.py` - Fluxo de cadastro que tenta vincular Telegram ID após criar cliente (linha 304)

**Restrição atual:**
- O banco de dados tem constraint `unique=True` em `telegram_id`
- O método `vincular_telegram()` verifica se ID já está vinculado e levanta `ValueError`

**Cenários afetados:**
- Empresas com múltiplos funcionários usando o mesmo Telegram para suporte
- Pessoas que desejam fazer atendimento para diferentes empresas/filiais
- Reset de cadastro para testes

# 3. APPROACH OVERVIEW

Após análise do código, identifiquei **4 abordagens possíveis** para resolver a questão. A abordagem mais flexível seria a **Opção C (Vínculo por CNPJ)**, que permite:
- Um Telegram ID vinculado a múltiplos CNPJs
- Cada CNPJ pode ter múltiplos Telegrams vinculados
- Manter rastreabilidade de quem está atendendo

# 4. IMPLEMENTATION STEPS

## Análise das Alternativas (para decisão do usuário):

### Opção A: Manter comportamento atual (vínculo 1:1)
- **Prós:** Simplicidade, controle rígido
- **Contras:** Não suporta casos de uso descritos
- **Impacto:** Nenhuma modificação necessária

### Opção B: Permitir reatribuição de vínculo
- Adicionar comando `/desvincular` ou permitir sobrescrever
- Usuário pode "libertar" o Telegram ID antes de novo cadastro

### Opção C: Múltiplos vínculos por CNPJ (RECOMENDADA)
- Remover `unique=True` do campo `telegram_id`
- Criar tabela intermediária `cliente_telegram` (cliente_id, telegram_id, nome_atendente, data_vinculo)
- Permitir múltiplos Telegrams por CNPJ
- Adicionar campo para identificar "atendente" na conversa

### Opção D: Allowlist de Telegrams por cliente
- Adicionar campo `telegram_ids_permitidos` (JSON array) no Cliente
- Validar se Telegram ID está na allowlist antes de vincular

---

## Passos para Implementação da Opção C (se selecionada):

1. **Modificar modelo de dados**
   - Remover `unique=True` de `telegram_id` em Cliente
   - Criar tabela `telegram_cliente` com campos: id, cliente_id, telegram_id, nome_atendente, criado_em

2. **Atualizar IdentificacaoService**
   - Modificar método `vincular_telegram()` para inserir na nova tabela
   - Criar método `listar_telegram_vinculados(cliente_id)`
   - Criar método `desvincular_telegram(cliente_id, telegram_id)`

3. **Atualizar handlers de mensagens**
   - No fluxo de cadastro, perguntar "nome do atendente" (opcional)
   - Salvar histórico de atendimentos por atendente

4. **Migração de dados**
   - Migrar vínculos existentes para nova tabela

# 5. TESTING AND VALIDATION

**Cenários de teste (após modificação):**

1. ✅ Usuário com Telegram vinculado a Cliente A tenta se identificar com Cliente B
   - Resultado: Sucesso - vincula Telegram também ao Cliente B

2. ✅ Empresa com 3 funcionários no mesmo Telegram
   - Resultado: Cada funcionário pode atender por CNPJ diferente

3. ✅ Tentativa de acesso não autorizado (Telegram sem vínculo)
   - Resultado: Solicita identificação/cadastro normalmente

4. ✅ Listar atendimentos por atendente
   - Resultado: Histórico filtrável por Telegram ID
