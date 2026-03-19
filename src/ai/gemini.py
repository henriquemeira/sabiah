"""Provedor Google Gemini."""

import logging
from typing import Optional

import google.genai as genai

from src.ai.base import ProvedorIA, RespostaIA, TipoProvedor
from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GeminiProvedor(ProvedorIA):
    """Provedor de IA usando Google Gemini."""
    
    def __init__(self, modelo: str = "gemini-2.0-flash"):
        """
        Inicializa o provedor Gemini.
        
        Args:
            modelo: Modelo do Gemini a ser usado (default: gemini-2.0-flash)
        """
        self._modelo = modelo
        self._client = None
        
        # Configurar API key
        if settings.gemini_api_key:
            logger.info(f"✅ Gemini configurado com modelo: {modelo}")
        else:
            logger.warning("⚠️ GEMINI_API_KEY não configurada!")
    
    @property
    def tipo(self) -> TipoProvedor:
        return TipoProvedor.GEMINI
    
    @property
    def modelo(self) -> str:
        return self._modelo
    
    def _get_client(self):
        """Retorna o cliente do Gemini (lazy loading)."""
        if self._client is None:
            self._client = genai.Client(api_key=settings.gemini_api_key)
        return self._client
    
    def chat(
        self,
        mensagem: str,
        sistema: Optional[str] = None,
        historico: Optional[list[dict]] = None,
    ) -> RespostaIA:
        """
        Envia uma mensagem para o Gemini e retorna a resposta.
        
        Args:
            mensagem: Mensagem do usuário
            sistema: Prompt de sistema (opcional)
            historico: Histórico de mensagens
            
        Returns:
            RespostaIA com o conteúdo da resposta
        """
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY não configurada!")
        
        client = self._get_client()
        
        # Configurar geração
        generation_config = {
            "temperature": 0.7,
            "max_output_tokens": 2048,
        }
        
        # Adicionar system_instruction ao config se fornecido
        if sistema:
            generation_config["system_instruction"] = sistema
        
        # Preparar conteúdo com histórico
        contents = []
        
        # Adicionar histórico se houver
        if historico:
            for msg in historico:
                role = msg.get("role", "user")
                # O modelo usa "user" e "model" (não "assistant")
                if role == "assistant":
                    role = "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.get("content", "")}]
                })
        
        # Adicionar mensagem atual
        contents.append({
            "role": "user",
            "parts": [{"text": mensagem}]
        })
        
        # Fazer a requisição
        response = client.models.generate_content(
            model=self._modelo,
            contents=contents,
            config=generation_config,
        )
        
        # Extrair texto da resposta
        conteudo = ""
        if hasattr(response, "text") and response.text:
            conteudo = response.text
        elif hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "content") and candidate.content:
                for part in candidate.content.parts:
                    if hasattr(part, "text") and part.text:
                        conteudo += part.text
        
        return RespostaIA(
            conteudo=conteudo,
            modelo=self._modelo,
        )
    
    def validar_configuracao(self) -> bool:
        """Valida se a configuração do Gemini está correta."""
        if not settings.gemini_api_key:
            return False
        
        try:
            client = self._get_client()
            # Tentar listar modelos para validar
            list(client.models.list())
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao validar Gemini: {e}")
            return False
