from openai import OpenAI
from typing import List
from app.config import settings


class EmbeddingService:

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.EMBEDDING_API_KEY,
            base_url=settings.EMBEDDING_BASE_URL,
        )
        self.model = settings.EMBEDDING_MODEL

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        cleaned = [t.replace("\n", " ") for t in texts if t.strip()]
        if not cleaned:
            return []
        response = self.client.embeddings.create(
            model=self.model,
            input=cleaned,
        )
        return [item.embedding for item in response.data]

    def embed_query(self, query: str) -> List[float]:
        results = self.embed_texts([query])
        return results[0] if results else []
