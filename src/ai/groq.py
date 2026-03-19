"""Provedor Groq (LLM gratuito com GPUs rápidas)."""

import logging
from typing import Optional

from openai import OpenAI

from src.ai.base import ProvedorIA, RespostaIA, TipoProvedor
from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GroqProvedor(ProvedorIA):
    """Provedor de IA usando Groq (API gratuita com GPUs NVIDIA)."""
    
    def __init__(self, modelo: str = None):
        """
        Inicializa o provedor Groq.
        
        Args:
            modelo: Modelo do Groq a ser usado (padrão: usa GROQ_MODEL das config)
        """
        # Usar configuração das settings se não informado
        if modelo is None:
            modelo = settings.groq_model
        
        self._modelo = modelo
        self._client = None
        
        if settings.groq_api_key:
            logger.info(f"✅ Groq configurado com modelo: {modelo}")
        else:
            logger.warning("⚠️ GROQ_API_KEY não configurada!")
    
    @property
    def tipo(self) -> TipoProvedor:
        return TipoProvedor.GROQ
    
    @property
    def modelo(self) -> str:
        return self._modelo
    
    def _get_client(self):
        """Retorna o cliente do Groq (lazy loading)."""
        if self._client is None:
            self._client = OpenAI(
                api_key=settings.groq_api_key,
                base_url="https://api.groq.com/openai/v1"
            )
        return self._client
    
    def chat(
        self,
        mensagem: str,
        sistema: Optional[str] = None,
        historico: Optional[list[dict]] = None,
    ) -> RespostaIA:
        """
        Envia uma mensagem para o Groq e retorna a resposta.
        
        Args:
            mensagem: Mensagem do usuário
            sistema: Prompt de sistema (opcional)
            historico: Histórico de mensagens
            
        Returns:
            RespostaIA com o conteúdo da resposta
        """
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY não configurada!")
        
        client = self._get_client()
        
        # Preparar mensagens
        messages = []
        
        # Adicionar system message se houver
        if sistema:
            messages.append({"role": "system", "content": sistema})
        
        # Adicionar histórico se houver
        if historico:
            for msg in historico:
                role = msg.get("role", "user")
                # Groq usa "user" e "assistant"
                if role == "assistant":
                    role = "assistant"
                messages.append({
                    "role": role,
                    "content": msg.get("content", "")
                })
        
        # Adicionar mensagem atual
        messages.append({"role": "user", "content": mensagem})
        
        # Fazer a requisição
        response = client.chat.completions.create(
            model=self._modelo,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
        )
        
        # Extrair texto da resposta
        conteudo = response.choices[0].message.content or ""
        
        return RespostaIA(
            conteudo=conteudo,
            modelo=self._modelo,
            tokens_usados=response.usage.total_tokens if response.usage else None,
        )
    
    def validar_configuracao(self) -> bool:
        """Valida se a configuração do Groq está correta."""
        if not settings.groq_api_key:
            return False
        
        try:
            client = self._get_client()
            # Tentar listar modelos para validar
            client.models.list()
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao validar Groq: {e}")
            return False
