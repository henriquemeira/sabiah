# 📚 Guia da Base de Conhecimento

Este documento explica como criar, editar e manter a base de conhecimento do Sabiah.

---

## O que é a Base de Conhecimento?

A base de conhecimento é um conjunto de documentos que o Sabiah usa para responder às perguntas dos clientes. Ela é indexada em um banco vetorial (ChromaDB) para permitir busca semântica.

---

## Estrutura de Arquivos

Os documentos devem ser placed na pasta `data/knowledge/`:

```
data/knowledge/
├── faq.md              # Perguntas Frequentes
├── tutoriais/
│   ├── getting-started.md
│   └── integracoes.md
├── problemas-conhecidos/
│   └── problemas.md
└── documentacao/
    └── funcionalidades.md
```

### Formatos Suportados

- **Markdown** (`.md`) - Recomendado
- **JSON** (`.json`)
- **Texto** (`.txt`)

---

## Como Adicionar Documentos

### 1. Criar um Arquivo

Crie um novo arquivo `.md` na pasta `data/knowledge/`:

```markdown
# Título do Documento

## Seção 1

Conteúdo da seção 1...

## Seção 2

Conteúdo da seção 2...
```

### 2. Regras de Formatação

- Use títulos hierárquicos (`#`, `##`, `###`)
- Use listas para passos
- Use código com idioma especificado:
  \`\`\`python
  print("Hello")
  \`\`\`
- Destaque com **negrito** ou *itálico*

---

## Exemplos de Conteúdo

### FAQ

```markdown
# Perguntas Frequentes

## Como resetar minha senha?

Para resetar sua senha:

1. Acesse a página de login
2. Clique em "Esqueci a senha"
3. Digite seu e-mail
4. Você receberá um link de recuperação

## Como exportar dados?

Para exportar seus dados:

1. Vá em Configurações
2. Clique em Exportar Dados
3. Escolha o formato (CSV ou Excel)
4. Clique em Baixar
```

### Problemas Conhecidos

```markdown
# Problemas Conhecidos

## Erro ao importar XML

**Sintoma:** Erro "Invalid XML format" ao importar

**Solução:**
1. Verifique se o XML está bem formado
2. Use o validador XML antes de importar
3. Certifique-se que encoding é UTF-8

**Status:** Corrigido na versão 2.1.0

---

## Tela branca após login

**Sintoma:** Tela branca após fazer login

**Solução:**
1. Limpe o cache do navegador
2. Use modo anônimo
3. Atualize para última versão do navegador

**Status:** Em análise
```

---

## Reindexação

Quando adicionar ou modificar documentos, é necessário reindexar a base:

```bash
cd /workspace/project/sabiah
python -m src.knowledge.indexer
```

### Opções do Indexador

```bash
# Reindexar tudo
python -m src.knowledge.indexer --rebuild

# Indexar apenas um arquivo
python -m src.knowledge.indexer --file data/knowledge/novo.md

# Ver estatísticas
python -m src.knowledge.indexer --stats
```

---

## Melhores Práticas

### 1. Conteúdo

- ✅ Escreva em linguagem clara e simples
- ✅ Use exemplos práticos
- ✅ Inclua screenshots se possível (com descrição)
- ✅ Mantenha documentos atualizados

- ❌ Evite jargão técnico desnecessário
- ❌ Não use conteúdo muito longo (divida em partes)
- ❌ Não repita informações

### 2. Estrutura

- ✅ Um documento por tema
- ✅ Títulos descritivos
- ✅ Seções bem organizadas

### 3. Busca

A IA busca porsimilaridade, então:
- ✅ Use palavras-chave relevantes
- ✅ Inclua sinônimos
- ✅ Use perguntas naturais

---

## Dicas de SEO Interno

Para melhorar a descoberta:

1. **Títulos claros**: Use perguntas que clientes reais fariam
2. **Palavras-chave**: Inclua termos que clientes usam
3. **Categorização**: Organize em pastas lógicas
4. **Metadados**: Futuramente, tags serão suportadas

---

## Troubleshooting

### Documento não aparece nas buscas

1. Verifique se o arquivo está em `data/knowledge/`
2. Execute a reindexação: `python -m src.knowledge.indexer --rebuild`
3. Verifique se o conteúdo não está vazio

### Busca retorna resultados irrelevantes

1. Adicione mais contexto aos documentos
2. Use palavras-chave mais específicas
3. Divida documentos muito longos

### Performance lenta

1. Limite documentos a 10KB cada
2. Evite arquivos muito grandes
3. Reindexe periodicamente para remover duplicatas

---

## Próximos Passos

- [ ] Adicionar sistema de tags
- [ ] Suporte a imagens
- [ ] Versionamento de documentos
- [ ] Dashboard de análise de conteúdo
