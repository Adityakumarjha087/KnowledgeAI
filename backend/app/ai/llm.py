import json
import httpx
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator
from app.core.config import settings

# Enterprise Model Pricing Table (prices per 1M tokens)
MODEL_PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "default": {"input": 0.50, "output": 1.50}
}


def calculate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """Calculates approximate request dollar cost based on model tokens pricing"""
    prices = MODEL_PRICING.get(model_name, MODEL_PRICING["default"])
    input_cost = (input_tokens / 1_000_000) * prices["input"]
    output_cost = (output_tokens / 1_000_000) * prices["output"]
    return round(input_cost + output_cost, 6)


class LLMProvider(ABC):
    @abstractmethod
    def generate_stream(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        history: List[Dict[str, str]]
    ) -> Generator[str, None, None]:
        """Yields text tokens as they generate in real time from the LLM"""
        pass


class MockLLMProvider(LLMProvider):
    def generate_stream(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        history: List[Dict[str, str]]
    ) -> Generator[str, None, None]:
        # Yield a simulated streaming text response
        response_text = (
            "According to the policy documents, regular employees get 20 days of annual leave. "
            "Managers require 2 weeks notice before approvals.\n\n"
            "Sources:\n1. HR_Policy.txt — Page 1"
        )
        import time
        words = response_text.split(" ")
        for word in words:
            time.sleep(0.04)  # Simulate human-like network typing latency
            yield word + " "


class OpenAILLMProvider(LLMProvider):
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.api_base = settings.LLM_API_BASE
        self.model = settings.LLM_MODEL

    def generate_stream(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        history: List[Dict[str, str]]
    ) -> Generator[str, None, None]:
        # Fallback to mock if API key is not configured
        if not self.api_key or "your_" in self.api_key or "placeholder" in self.api_key:
            yield from MockLLMProvider().generate_stream(system_prompt, user_prompt, history)
            return

        try:
            url = f"{self.api_base.rstrip('/')}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                # OpenRouter-specific headers (ignored by other providers)
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "Enterprise AI Knowledge Assistant"
            }
            
            # Format message list
            messages = [{"role": "system", "content": system_prompt}]
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": user_prompt})

            payload = {
                "model": self.model,
                "messages": messages,
                "stream": True
            }

            # Call API using httpx streaming client
            with httpx.stream(
                "POST", url, json=payload, headers=headers, timeout=60.0
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            token = chunk["choices"][0]["delta"].get("content", "")
                            if token:
                                yield token
                        except Exception:
                            pass
        except Exception as e:
            print(f"LLM API error: {str(e)}. Falling back to Mock.")
            yield f"Error in LLM Provider: {str(e)}. (Fallback Active): "
            yield from MockLLMProvider().generate_stream(system_prompt, user_prompt, history)


def get_llm_provider() -> LLMProvider:
    """Returns active LLM provider based on settings configurations"""
    if settings.LLM_PROVIDER == "openai":
        return OpenAILLMProvider()
    return MockLLMProvider()
