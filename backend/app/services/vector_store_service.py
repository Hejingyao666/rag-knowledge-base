import uuid
from typing import List, Optional
import chromadb
from app.config import settings
from app.services.embedding_service import EmbeddingService


class VectorStoreService:

    def __init__(self):
        self.embedding_svc = EmbeddingService()
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: List[dict]) -> int:
        if not chunks:
            return 0
        texts     = [c["content"]  for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        ids       = [str(uuid.uuid4()) for _ in chunks]
        batch_size = 100
        total = 0
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_metas = metadatas[i:i+batch_size]
            batch_ids   = ids[i:i+batch_size]
            embeddings  = self.embedding_svc.embed_texts(batch_texts)
            self.collection.add(
                ids=batch_ids,
                embeddings=embeddings,
                documents=batch_texts,
                metadatas=batch_metas,
            )
            total += len(batch_texts)
        return total

    def search(self, query: str, top_k: int = None, doc_ids: Optional[List[str]] = None) -> List[dict]:
        k = top_k or settings.TOP_K
        query_embedding = self.embedding_svc.embed_query(query)
        where = None
        if doc_ids and len(doc_ids) == 1:
            where = {"doc_id": doc_ids[0]}
        elif doc_ids and len(doc_ids) > 1:
            where = {"doc_id": {"$in": doc_ids}}
        count = self.collection.count()
        if count == 0:
            return []
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, count),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        output = []
        if not results["documents"] or not results["documents"][0]:
            return output
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            output.append({
                "content":  doc,
                "metadata": meta,
                "score":    round(1 - dist, 4),
            })
        return output

    def delete_by_doc_id(self, doc_id: str) -> bool:
        try:
            results = self.collection.get(where={"doc_id": doc_id})
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
            return True
        except Exception:
            return False

    def get_stats(self) -> dict:
        return {
            "total_chunks":    self.collection.count(),
            "collection_name": settings.CHROMA_COLLECTION,
        }
