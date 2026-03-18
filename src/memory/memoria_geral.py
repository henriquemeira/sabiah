"""Serviço de Memória Geral - Base de Conhecimento."""

import logging
from pathlib import Path
from typing import Optional

from src.knowledge import ChromaService, IndexadorDocumentos
from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MemoriaGeral:
    """
    Memória Geral do Sabiah.
    
    Representa o conhecimento base sobre o software. Inclui documentação,
    FAQs, tutoriais, problemas conhecidos e suas soluções.
    """
    
    def __init__(
        self,
        knowledge_dir: Optional[str] = None,
        chroma_service: Optional[ChromaService] = None,
    ):
        """
        Inicializa a Memória Geral.
        
        Args:
            knowledge_dir: Diretório com arquivos de conhecimento
            chroma_service: Instância do ChromaDB (opcional)
        """
        self.knowledge_dir = knowledge_dir or "data/knowledge"
        self.chroma = chroma_service or ChromaService()
        self.indexador = IndexadorDocumentos(self.chroma)
        self._indexada = False
    
    def indexar(self, force: bool = False) -> int:
        """
        Indexa a base de conhecimento no ChromaDB.
        
        Args:
            force: Se True, força reindexação (reset + index)
            
        Returns:
            Número de documentos indexados
        """
        if force:
            logger.info("♻️ Forçando reindexação da base de conhecimento...")
            self.chroma.resetar()
        
        if self._indexada and not force:
            logger.info("Base de conhecimento já indexada.")
            return self.chroma.contar_documentos()
        
        # Indexar arquivos do diretório
        total = 0
        
        # Indexar Markdown
        total += self.indexador.indexar_diretorio(self.knowledge_dir, extensao=".md")
        
        # Indexar JSON
        total += self.indexador.indexar_diretorio(self.knowledge_dir, extensao=".json")
        
        self._indexada = True
        logger.info(f"✅ Base de conhecimento indexada: {total} documentos")
        return total
    
    def buscar(self, query: str, n_resultados: int = 5) -> list[dict]:
        """
        Busca na base de conhecimento usando busca semântica.
        
        Args:
            query: Query de busca
            n_resultados: Número máximo de resultados
            
        Returns:
            Lista de documentos relevantes
        """
        if not self._indexada:
            self.indexar()
        
        return self.chroma.buscar(query, n_results=n_resultados)
    
    def buscar_por_tipo(self, query: str, tipo: str, n_resultados: int = 3) -> list[dict]:
        """
        Busca na base de conhecimento filtrando por tipo.
        
        Args:
            query: Query de busca
            tipo: Tipo de documento (faq, tutorial, problema)
            n_resultados: Número máximo de resultados
            
        Returns:
            Lista de documentos do tipo especificado
        """
        if not self._indexada:
            self.indexar()
        
        return self.chroma.buscar(
            query,
            n_results=n_resultados,
            filtro={"tipo": tipo}
        )
    
    def formatar_resultados(self, resultados: list[dict]) -> str:
        """
        Formata os resultados da busca em texto legível.
        
        Args:
            resultados: Lista de documentos da busca
            
        Returns:
            Texto formatado com os resultados
        """
        if not resultados:
            return ""
        
        partes = ["### Informações Relevantes:\n"]
        
        for i, doc in enumerate(resultados, 1):
            metadados = doc.get("metadados", {})
            secao = metadados.get("secao", "")
            
            if secao:
                partes.append(f"**{secao}**\n")
            
            partes.append(doc.get("conteudo", ""))
            partes.append("\n" + "-" * 40 + "\n")
        
        return "\n".join(partes)
    
    def recarregar(self) -> int:
        """Recarrega a base de conhecimento (reset + index)."""
        return self.indexar(force=True)


# Instância global
_memoria_geral: Optional[MemoriaGeral] = None


def get_memoria_geral() -> MemoriaGeral:
    """Retorna a instância global da Memória Geral."""
    global _memoria_geral
    if _memoria_geral is None:
        _memoria_geral = MemoriaGeral()
    return _memoria_geral
