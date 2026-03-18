"""Serviço de banco vetorial usando ChromaDB."""

import logging
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ChromaService:
    """Serviço de banco vetorial para busca semântica."""
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "knowledge",
    ):
        """
        Inicializa o serviço ChromaDB.
        
        Args:
            persist_directory: Diretório para persistência (default: config)
            collection_name: Nome da coleção de documentos
        """
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self.collection_name = collection_name
        self._client: Optional[chromadb.PersistentClient] = None
        self._collection: Optional[chromadb.Collection] = None
        
        # Criar diretório se não existir
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
    
    def _get_client(self) -> chromadb.PersistentClient:
        """Retorna o cliente do ChromaDB (lazy loading)."""
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )
            logger.info(f"✅ ChromaDB conectado: {self.persist_directory}")
        return self._client
    
    def _get_collection(self) -> chromadb.Collection:
        """Retorna a coleção de documentos."""
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Base de conhecimento do Sabiah"},
            )
        return self._collection
    
    def adicionar_documento(
        self,
        id: str,
        conteudo: str,
        metadados: Optional[dict] = None,
    ) -> None:
        """
        Adiciona um documento ao banco vetorial.
        
        Args:
            id: Identificador único do documento
            conteudo: Texto do documento
            metadados: Metadados opcionais (fonte, tipo, etc.)
        """
        collection = self._get_collection()
        collection.add(
            documents=[conteudo],
            ids=[id],
            metadatas=[metadados or {}],
        )
        logger.info(f"📄 Documento adicionado: {id}")
    
    def adicionar_documentos(
        self,
        documentos: list[dict],
    ) -> None:
        """
        Adiciona múltiplos documentos ao banco vetorial.
        
        Args:
            documentos: Lista de documentos [{"id", "conteudo", "metadados"}]
        """
        ids = [doc["id"] for doc in documentos]
        conteudos = [doc["conteudo"] for doc in documentos]
        metadados = [doc.get("metadados", {}) for doc in documentos]
        
        collection = self._get_collection()
        collection.add(
            documents=conteudos,
            ids=ids,
            metadatas=metadados,
        )
        logger.info(f"📄 {len(documentos)} documentos adicionados")
    
    def buscar(
        self,
        query: str,
        n_results: int = 5,
        filtro: Optional[dict] = None,
    ) -> list[dict]:
        """
        Busca documentos similares usando busca semântica.
        
        Args:
            query: Query de busca
            n_results: Número de resultados
            filtro: Filtro opcional de metadados
            
        Returns:
            Lista de documentos similares
        """
        collection = self._get_collection()
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filtro,
            include=["documents", "metadatas", "distances"],
        )
        
        documentos = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                documentos.append({
                    "id": results["ids"][0][i],
                    "conteudo": doc,
                    "metadados": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distancia": results["distances"][0][i] if results["distances"] else 0,
                })
        
        return documentos
    
    def buscar_por_ids(self, ids: list[str]) -> list[dict]:
        """
        Busca documentos por IDs.
        
        Args:
            ids: Lista de IDs
            
        Returns:
            Lista de documentos
        """
        collection = self._get_collection()
        
        results = collection.get(
            ids=ids,
            include=["documents", "metadatas"],
        )
        
        documentos = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"]):
                documentos.append({
                    "id": results["ids"][i],
                    "conteudo": doc,
                    "metadados": results["metadatas"][i] if results["metadatas"] else {},
                })
        
        return documentos
    
    def excluir_documento(self, id: str) -> None:
        """
        Exclui um documento do banco vetorial.
        
        Args:
            id: ID do documento
        """
        collection = self._get_collection()
        collection.delete(ids=[id])
        logger.info(f"🗑️ Documento excluído: {id}")
    
    def contar_documentos(self) -> int:
        """Retorna o número de documentos na coleção."""
        collection = self._get_collection()
        return collection.count()
    
    def resetar(self) -> None:
        """Remove todos os documentos da coleção."""
        client = self._get_client()
        client.delete_collection(self.collection_name)
        self._collection = None
        logger.warning("♻️ ChromaDB resetado")


# Instância global
_chroma_service: Optional[ChromaService] = None


def get_chroma_service() -> ChromaService:
    """Retorna a instância global do ChromaService."""
    global _chroma_service
    if _chroma_service is None:
        _chroma_service = ChromaService()
    return _chroma_service
