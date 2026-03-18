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
            genai.configure(api_key=settings.gemini_api_key)
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
            self._client = genai.GenerativeModel(self._modelo)
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
        
        # Construir conteúdo da conversa
        contents = []
        
        # Adicionar histórico se houver
        if historico:
            for msg in historico:
                role = "user" if msg.get("role") == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.get("content", "")}]
                })
        
        # Adicionar mensagem atual
        contents.append({
            "role": "user",
            "parts": [{"text": mensagem}]
        })
        
        # Criar chat
        client = self._get_client()
        
        # Configurar geração
        generation_config = {
            "temperature": 0.7,
            "max_output_tokens": 2048,
        }
        
        # Adicionar sistema se houver
        if sistema:
            # O Gemini usa safety_settings e system_instruction
            response = client.generate_content(
                contents,
                system_instruction=sistema,
                generation_config=generation_config,
            )
        else:
            response = client.generate_content(
                contents,
                generation_config=generation_config,
            )
        
        # Extrair texto da resposta
        conteudo = ""
        if hasattr(response, "text"):
            conteudo = response.text
        elif hasattr(response, "parts"):
            conteudo = "".join([part.text for part in response.parts if hasattr(part, "text")])
        
        return RespostaIA(
            conteudo=conteudo,
            modelo=self._modelo,
        )
    
    def validar_configuracao(self) -> bool:
        """Valida se a configuração do Gemini está correta."""
        if not settings.gemini_api_key:
            return False
        
        try:
            # Testar conexão listando modelos
            list(genai.list_models())
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao validar Gemini: {e}")
            return False
