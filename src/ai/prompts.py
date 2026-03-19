"""Serviço de construção de prompts com contexto."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ContextoCliente:
    """Contexto do cliente para o prompt."""
    nome: str
    versao_software: Optional[str] = None
    plano: Optional[str] = None
    modulos: Optional[str] = None


@dataclass
class ContextoConversa:
    """Contexto da conversa para o prompt."""
    historico: list[dict]


class PromptBuilder:
    """Construtor de prompts com contexto integrado."""
    
    # Prompt de sistema base
    SISTEMA_BASE = """Você é o Sabiah, um assistente de suporte ao cliente inteligente e prestativo.
Seu objetivo é ajudar os clientes a resolver suas dúvidas e problemas de forma eficiente e amigável.

## Diretrizes de Comunicação
- Responda de forma clara, concisa e acessível
- Seja profissional mas amigável
- Use tom caloroso e respeito
- Quando não souber a resposta, seja honesto e ofereça alternativas

## ⚠️ IMPORTANTE - Formato de Resposta para Telegram
NUNCA use formatação Markdown nas suas respostas. O Telegram não processa Markdown corretamente quando enviado via API.

O que EVITAR:
- Não use asteriscos para negrito: *texto* (o Telegram mostra os asteriscos)
- Não use underscores para itálico: _texto_ (o Telegram mostra os underscores)
- Não use crases para código: `código` (o Telegram mostra as crases)
- Não use travessões para listas: - item (use números ou bullet points simples)
- Não use # para títulos

O que FAZER:
- Use texto puro e simples
- Para ênfase, use MAIÚSCULAS ou CAPS LOCK sparingly
- Para listas, use números com ponto: 1. Item, 2. Item
- Para separações, use linhas horizontais com três traços: ---
- Use parênteses para referências: (veja documentação)

Exemplo do que a IA gera (ERRADO):
"*Olá!* Para resolver seu problema, siga estes passos:"

Exemplo do que DEVE gerar (CORRETO):
"Olá! Para resolver seu problema, siga estes passos:

1. Acesse o menu Configurações
2. Clique em Usuarios
3. Selecione o usuario desejado

Qualquer dúvida, estou à disposição!"

- Sempre tente oferecer soluções práticas
- Evite jargão técnico complexo, explique apenas quando necessário
- Evite textos longos, priorize resumos

## Limitações
- Não invente informações
- Não accessa sistemas externos além da base de conhecimento
- Se a pergunta for muito complexa, ofereça escalonamento

## Base de Conhecimento
Você tem acesso a uma base de conhecimento com documentação e FAQs do software.
Use essa base para responder perguntas técnicas.
Quando usar informações da base, cite a fonte quando apropriado.

## Contexto
O contexto do cliente (versão, plano, módulos) pode ser fornecido para personalizar a resposta."""
    
    # Prompt para escalonamento
    SISTEMA_ESCALONAMENTO = """Você está indicando que a questão do cliente não pode ser resolvida automaticamente.

NESTE CASO:
- Reconheça a limitação de forma gentil
- Ofereça as opções de escalonamento disponíveis:
  • Abrir um ticket no helpdesk
  • Falar com um atendente humano
  • Solicitar retorno telefônico
  • Reformular a pergunta
- Não tente inventar uma resposta

Aja como um bom anfitrião que sabe quando transferir para a pessoa certa."""

    # Prompt para feedback negativo
    SISTEMA_SATISFACAO = """O cliente expressou insatisfação.

NESTE CASO:
- Peça desculpas pelo transtorno
- Mostre empatia com a situação
- Ofereça alternativas concretas
- Sugira falar com um atendente se necessário
- Não seja defensivo"""

    def __init__(
        self,
        base_conhecimento: str = "",
        contexto_cliente: Optional[ContextoCliente] = None,
        contexto_conversa: Optional[ContextoConversa] = None,
    ):
        """
        Inicializa o builder de prompts.
        
        Args:
            base_conhecimento: Texto da base de conhecimento recuperada
            contexto_cliente: Contexto do cliente
            contexto_conversa: Histórico da conversa
        """
        self.base_conhecimento = base_conhecimento
        self.contexto_cliente = contexto_cliente
        self.contexto_conversa = contexto_conversa
    
    def build(self) -> tuple[str, list[dict]]:
        """
        Constrói o prompt de sistema e histórico para a IA.
        
        Returns:
            Tuple (prompt_sistema, historico)
        """
        # Construir prompt de sistema
        sistema_parts = [self.SISTEMA_BASE]
        
        # Adicionar contexto do cliente
        if self.contexto_cliente:
            sistema_parts.append(self._build_contexto_cliente())
        
        # Adicionar base de conhecimento
        if self.base_conhecimento:
            sistema_parts.append(self._build_contexto_base_conhecimento())
        
        sistema = "\n\n".join(sistema_parts)
        
        # Construir histórico
        historico = []
        if self.contexto_conversa:
            for msg in self.contexto_conversa.historico:
                historico.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })
        
        return sistema, historico
    
    def _build_contexto_cliente(self) -> str:
        """Constrói o contexto específico do cliente."""
        if not self.contexto_cliente:
            return ""
        
        parts = ["### Contexto do Cliente"]
        parts.append(f"Nome: {self.contexto_cliente.nome}")
        
        if self.contexto_cliente.versao_software:
            parts.append(f"Versão do Software: {self.contexto_cliente.versao_software}")
        
        if self.contexto_cliente.plano:
            parts.append(f"Plano: {self.contexto_cliente.plano}")
        
        if self.contexto_cliente.modulos:
            parts.append(f"Módulos Contratados: {self.contexto_cliente.modulos}")
        
        return "\n".join(parts)
    
    def _build_contexto_base_conhecimento(self) -> str:
        """Constrói o contexto da base de conhecimento."""
        if not self.base_conhecimento:
            return ""
        
        return f"""### Base de Conhecimento

{self.base_conhecimento}

Quando utilizar informações da base de conhecimento, cite a fonte quando apropriado."""

    @staticmethod
    def criar_resposta(
        base_conhecimento: str,
        cliente: Optional[ContextoCliente] = None,
        historico: Optional[list[dict]] = None,
    ) -> tuple[str, list[dict]]:
        """
        Método estático para criar prompts de forma simples.
        
        Args:
            base_conhecimento: Texto da base de conhecimento
            cliente: Contexto do cliente
            historico: Histórico de mensagens
            
        Returns:
            Tuple (prompt_sistema, historico)
        """
        contexto_cliente = None
        if cliente:
            contexto_cliente = ContextoCliente(
                nome=cliente.get("nome", "Cliente"),
                versao_software=cliente.get("versao_software"),
                plano=cliente.get("plano"),
                modulos=cliente.get("modulos"),
            )
        
        contexto_conversa = None
        if historico:
            contexto_conversa = ContextoConversa(historico=historico)
        
        builder = PromptBuilder(
            base_conhecimento=base_conhecimento,
            contexto_cliente=contexto_cliente,
            contexto_conversa=contexto_conversa,
        )
        
        return builder.build()
