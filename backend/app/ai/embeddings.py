import hashlib
import httpx
from abc import ABC, abstractmethod
from typing import List, Optional
from app.core.config import settings


class EmbeddingProvider(ABC):
    @abstractmethod
    def get_embedding(self, text: str) -> List[float]:
        """Generates the vector embedding for a single text string"""
        pass
        
    @abstractmethod
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates vector embeddings for a list of text strings in batch"""
        pass


class MockEmbeddingProvider(EmbeddingProvider):
    def get_embedding(self, text: str) -> List[float]:
        # Produce a deterministic vector based on the text hash for test consistency
        h = hashlib.md5(text.encode("utf-8")).hexdigest()
        seed = int(h[:8], 16) / 4294967295.0
        dim = settings.EMBEDDING_DIMENSION
        
        vec = []
        for i in range(dim):
            # Generate deterministic floats between -0.5 and 0.5
            val = (seed + (i / dim)) % 1.0 - 0.5
            vec.append(round(val, 6))
        return vec

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self.get_embedding(text) for text in texts]


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self):
        self.api_key = settings.EMBEDDING_API_KEY or settings.LLM_API_KEY
        self.api_base = settings.EMBEDDING_API_BASE
        self.model = settings.EMBEDDING_MODEL

    def get_embedding(self, text: str) -> List[float]:
        return self.get_embeddings([text])[0]

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        # Fallback to mock if API key is not configured
        if not self.api_key or "your_" in self.api_key or "placeholder" in self.api_key:
            return MockEmbeddingProvider().get_embeddings(texts)
            
        try:
            url = f"{self.api_base.rstrip('/')}/embeddings"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "input": texts,
                "model": self.model
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                # Sort items by index to guarantee input-output ordering matches
                items = sorted(data["data"], key=lambda x: x["index"])
                return [item["embedding"] for item in items]
        except Exception as e:
            print(f"Embedding API error: {str(e)}. Falling back to Mock Embeddings.")
            return MockEmbeddingProvider().get_embeddings(texts)


def get_embedding_provider() -> EmbeddingProvider:
    """Returns the active embedding provider based on settings config"""
    if settings.EMBEDDING_PROVIDER == "openai":
        return OpenAIEmbeddingProvider()
    return MockEmbeddingProvider()
