"""Indexador de documentos da base de conhecimento."""

import json
import logging
import re
from pathlib import Path
from typing import Optional

from src.knowledge.chroma import ChromaService

logger = logging.getLogger(__name__)


class IndexadorDocumentos:
    """Indexador de documentos Markdown/JSON para ChromaDB."""
    
    def __init__(self, chroma_service: Optional[ChromaService] = None):
        """
        Inicializa o indexador.
        
        Args:
            chroma_service: Instância do ChromaService (opcional)
        """
        self.chroma = chroma_service or ChromaService()
    
    def indexar_diretorio(
        self,
        diretorio: str,
        extensao: str = ".md",
    ) -> int:
        """
        Indexa todos os arquivos de um diretório.
        
        Args:
            diretorio: Caminho do diretório
            extensao: Extensão dos arquivos (default: .md)
            
        Returns:
            Número de documentos indexados
        """
        path = Path(diretorio)
        if not path.exists():
            logger.warning(f"⚠️ Diretório não encontrado: {diretorio}")
            return 0
        
        documentos = []
        
        # Buscar arquivos
        for arquivo in path.rglob(f"*{extensao}"):
            try:
                docs = self._processar_arquivo(arquivo)
                documentos.extend(docs)
            except Exception as e:
                logger.error(f"❌ Erro ao processar {arquivo}: {e}")
        
        if documentos:
            self.chroma.adicionar_documentos(documentos)
        
        logger.info(f"✅ {len(documentos)} documentos indexados de {diretorio}")
        return len(documentos)
    
    def _processar_arquivo(self, arquivo: Path) -> list[dict]:
        """
        Processa um arquivo e retorna documentos para indexação.
        
        Args:
            arquivo: Path do arquivo
            
        Returns:
            Lista de documentos
        """
        conteudo = arquivo.read_text(encoding="utf-8")
        tipo = arquivo.suffix.lower()
        
        # Gerar ID único baseado no caminho
        base_id = str(arquivo.relative_to(arquivo.parent)).replace("/", "_").replace("\\", "_")
        
        if tipo == ".md":
            return self._processar_markdown(arquivo, conteudo, base_id)
        elif tipo == ".json":
            return self._processar_json(arquivo, conteudo, base_id)
        else:
            return [{
                "id": base_id,
                "conteudo": conteudo,
                "metadados": {
                    "tipo": tipo,
                    "arquivo": str(arquivo),
                },
            }]
    
    def _processar_markdown(self, arquivo: Path, conteudo: str, base_id: str) -> list[dict]:
        """Processa arquivo Markdown."""
        documentos = []
        
        # Separar por títulos de nível 1 ou 2
        sections = re.split(r"^(#{1,2})\s+(.+)$", conteudo, flags=re.MULTILINE)
        
        if len(sections) > 1:
            # Há seções identificadas
            current_section = ""
            current_title = "Introdução"
            
            for i, part in enumerate(sections):
                if not part:
                    continue
                if part.startswith("#"):
                    # Salvar seção anterior
                    if current_section.strip():
                        doc_id = f"{base_id}_{len(documentos)}"
                        documentos.append({
                            "id": doc_id,
                            "conteudo": current_section.strip(),
                            "metadados": {
                                "tipo": "markdown",
                                "arquivo": str(arquivo),
                                "secao": current_title,
                            },
                        })
                    # Iniciar nova seção
                    next_idx = i + 2 if i + 2 < len(sections) else i + 1
                    current_title = sections[next_idx] if next_idx < len(sections) else "Sem título"
                    current_section = ""
                else:
                    current_section += part + "\n"
            
            # Adicionar última seção
            if current_section.strip():
                doc_id = f"{base_id}_{len(documentos)}"
                documentos.append({
                    "id": doc_id,
                    "conteudo": current_section.strip(),
                    "metadados": {
                        "tipo": "markdown",
                        "arquivo": str(arquivo),
                        "secao": current_title,
                    },
                })
        else:
            # Documento único
            documentos.append({
                "id": base_id,
                "conteudo": conteudo,
                "metadados": {
                    "tipo": "markdown",
                    "arquivo": str(arquivo),
                },
            })
        
        return documentos
    
    def _processar_json(self, arquivo: Path, conteudo: str, base_id: str) -> list[dict]:
        """Processa arquivo JSON."""
        try:
            dados = json.loads(conteudo)
        except json.JSONDecodeError:
            logger.warning(f"⚠️ JSON inválido: {arquivo}")
            return []
        
        documentos = []
        
        # Processar conforme estrutura
        if isinstance(dados, list):
            # Lista de itens
            for i, item in enumerate(dados):
                if isinstance(item, dict):
                    texto = self._json_para_texto(item)
                    documentos.append({
                        "id": f"{base_id}_{i}",
                        "conteudo": texto,
                        "metadados": {
                            "tipo": "json",
                            "arquivo": str(arquivo),
                            "indice": i,
                        },
                    })
        elif isinstance(dados, dict):
            # Objeto único
            texto = self._json_para_texto(dados)
            documentos.append({
                "id": base_id,
                "conteudo": texto,
                "metadados": {
                    "tipo": "json",
                    "arquivo": str(arquivo),
                },
            })
        
        return documentos
    
    def _json_para_texto(self, obj: dict) -> str:
        """Converte objeto JSON para texto legível."""
        partes = []
        
        for chave, valor in obj.items():
            if isinstance(valor, str):
                partes.append(f"{chave}: {valor}")
            elif isinstance(valor, (int, float, bool)):
                partes.append(f"{chave}: {valor}")
            elif isinstance(valor, list):
                partes.append(f"{chave}: {', '.join(str(v) for v in valor)}")
            elif isinstance(valor, dict):
                partes.append(f"{chave}: {self._json_para_texto(valor)}")
        
        return " | ".join(partes)
    
    def indexar_faq(self, faq: list[dict]) -> int:
        """
        Indexa FAQ diretamente.
        
        Args:
            faq: Lista de {"pergunta": "...", "resposta": "..."}
            
        Returns:
            Número de documentos indexados
        """
        documentos = []
        
        for i, item in enumerate(faq):
            pergunta = item.get("pergunta", "")
            resposta = item.get("resposta", "")
            
            if pergunta and resposta:
                documentos.append({
                    "id": f"faq_{i}",
                    "conteudo": f"Pergunta: {pergunta}\nResposta: {resposta}",
                    "metadados": {
                        "tipo": "faq",
                        "indice": i,
                    },
                })
        
        if documentos:
            self.chroma.adicionar_documentos(documentos)
        
        return len(documentos)
