import httpx
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.core.config import settings


class RerankerProvider(ABC):
    @abstractmethod
    def rerank(
        self, query: str, candidates: List[Dict[str, Any]], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Takes search candidates, sorts them by contextual relevance, and returns the top_k"""
        pass


class MockReranker(RerankerProvider):
    def rerank(
        self, query: str, candidates: List[Dict[str, Any]], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        # Sort candidates using a combined weight of cosine similarity and lexical RRF score
        candidates.sort(
            key=lambda x: x.get("similarity", 0.0) + x.get("rrf_score", 0.0), 
            reverse=True
        )
        return candidates[:top_k]


class CohereReranker(RerankerProvider):
    def __init__(self):
        self.api_key = settings.RERANK_API_KEY
        self.model = settings.RERANK_MODEL

    def rerank(
        self, query: str, candidates: List[Dict[str, Any]], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        # Fallback to mock if API key is not configured
        if not self.api_key or "your_" in self.api_key or "placeholder" in self.api_key:
            return MockReranker().rerank(query, candidates, top_k)
            
        if not candidates:
            return []
            
        try:
            url = "https://api.cohere.ai/v1/rerank"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Format inputs for Cohere rerank API
            documents = [item["chunk"].text for item in candidates]
            payload = {
                "model": self.model,
                "query": query,
                "documents": documents,
                "top_n": top_k
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                # Re-map ranked indexes back to original items
                reranked = []
                for res in data["results"]:
                    idx = res["index"]
                    score = res["relevance_score"]
                    candidate = candidates[idx]
                    candidate["rerank_score"] = score
                    reranked.append(candidate)
                return reranked
                
        except Exception as e:
            print(f"Cohere Rerank failed: {str(e)}. Falling back to mock.")
            return MockReranker().rerank(query, candidates, top_k)


def get_reranker() -> RerankerProvider:
    """Returns the active reranker based on settings configuration"""
    if settings.RERANK_PROVIDER == "cohere":
        return CohereReranker()
    return MockReranker()
