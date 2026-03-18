"""Interface abstrata para provedores de IA."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TipoProvedor(str, Enum):
    """Tipos de provedores de IA suportados."""
    GEMINI = "gemini"
    OPENAI = "openai"
    GROQ = "groq"
    OLLAMA = "ollama"


@dataclass
class RespostaIA:
    """Resposta retornada pelo provedor de IA."""
    conteudo: str
    modelo: str
    tokens_usados: Optional[int] = None
    confidence: Optional[float] = None


class ProvedorIA(ABC):
    """Interface abstrata para provedores de IA."""
    
    @property
    @abstractmethod
    def tipo(self) -> TipoProvedor:
        """Retorna o tipo do provedor."""
        pass
    
    @property
    @abstractmethod
    def modelo(self) -> str:
        """Retorna o nome do modelo utilizado."""
        pass
    
    @abstractmethod
    def chat(
        self,
        mensagem: str,
        sistema: Optional[str] = None,
        historico: Optional[list[dict]] = None,
    ) -> RespostaIA:
        """
        Envia uma mensagem para a IA e retorna a resposta.
        
        Args:
            mensagem: Mensagem do usuário
            sistema: Prompt de sistema (opcional)
            historico: Histórico de mensagens no formato [{"role": "user/assistant", "content": "..."}]
            
        Returns:
            RespostaIA com o conteúdo da resposta
        """
        pass
    
    @abstractmethod
    def validar_configuracao(self) -> bool:
        """Valida se a configuração do provedor está correta."""
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} modelo={self.modelo}>"
