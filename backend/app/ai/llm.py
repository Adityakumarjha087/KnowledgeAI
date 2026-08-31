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
        import re
        import time

        cleaned_user = re.sub(r"[^\w\s]", "", user_prompt.strip().lower())
        greeting_set = {
            "hi", "hey", "hello", "hola", "greetings", "good morning", 
            "good afternoon", "good evening", "howdy", "sup", "yo",
            "how are you", "how are you doing", "whats up", "what's up",
            "hi there", "hello there", "hey there"
        }
        
        if cleaned_user in greeting_set:
            response_text = (
                "Hello! 👋 I am your Enterprise AI Knowledge Assistant. "
                "How can I help you today? You can ask me any questions about your company's uploaded "
                "policies, guidelines, technical documentation, or contracts."
            )
        elif cleaned_user in {"who are you", "what can you do", "help", "what is this", "what do you do"}:
            response_text = (
                "I am your Enterprise AI Knowledge Assistant. I help you instantly find answers, summarize "
                "policies, and retrieve verified citations across all your organization's uploaded documents. "
                "Feel free to ask a question or upload a file in the Documents section!"
            )
        elif cleaned_user in {"thanks", "thank you", "thx", "appreciate it"}:
            response_text = "You're very welcome! Let me know if there is anything else I can help you look up."
        else:
            # Extract context block between --- CONTEXT START --- and --- CONTEXT END ---
            context_match = re.search(
                r"--- CONTEXT START ---\s*(.*?)\s*--- CONTEXT END ---", 
                system_prompt, 
                re.DOTALL
            )
            context_raw = context_match.group(1).strip() if context_match else ""

            if not context_raw or context_raw == "":
                response_text = (
                    "I could not find any information regarding your query in the uploaded documents. "
                    "Please make sure your relevant document is uploaded and processed in the Documents section."
                )
            else:
                # Parse individual source blocks: [1] File: ... Content: ...
                source_blocks = re.split(r"(?=\[\d+\]\s+File:)", context_raw)
                source_blocks = [b.strip() for b in source_blocks if b.strip()]
                
                # Extract question keywords
                query_words = set(w.lower() for w in re.findall(r"\w+", user_prompt) if len(w) > 2)
                # Remove common stop words
                stopwords = {"what", "when", "where", "which", "who", "whom", "whose", "why", "how", "the", "and", "for", "are", "is", "about", "tell", "give", "please", "with", "does", "from", "can", "you", "much", "many"}
                keywords = query_words - stopwords
                
                matched_points = []
                for block in source_blocks:
                    header_match = re.match(r"(\[\d+\])\s+File:\s*([^\n]+)", block)
                    cite_tag = header_match.group(1) if header_match else "[1]"
                    
                    # Split content into sentences/lines
                    lines = block.split("\n")
                    content_lines = [l.replace("Content:", "").strip() for l in lines if not l.startswith("[") and l.strip()]
                    
                    for line in content_lines:
                        # Clean bullets
                        clean_line = re.sub(r"^[•\-\*\d\.]+\s*", "", line).strip()
                        if not clean_line or len(clean_line) < 10:
                            continue
                        line_words = set(w.lower() for w in re.findall(r"\w+", clean_line))
                        overlap = len(keywords & line_words)
                        if overlap > 0 or not keywords:
                            matched_points.append((overlap, f"{clean_line} {cite_tag}"))

                if matched_points:
                    # Sort by keyword match relevance
                    matched_points.sort(key=lambda x: x[0], reverse=True)
                    top_facts = [p[1] for p in matched_points[:4]]
                    response_text = (
                        "Based on your uploaded documents:\n\n"
                        + "\n\n".join(f"• {fact}" for fact in top_facts)
                    )
                else:
                    # Fallback to returning relevant top excerpts with citations
                    first_block = source_blocks[0] if source_blocks else ""
                    lines = [l for l in first_block.split("\n") if not l.startswith("[") and len(l.strip()) > 15]
                    snippet = lines[0] if lines else first_block[:200]
                    response_text = f"According to your uploaded documents [1]:\n\n{snippet}"

        # Stream the extracted response token by token
        words = response_text.split(" ")
        for i, word in enumerate(words):
            time.sleep(0.02)
            suffix = " " if i < len(words) - 1 else ""
            yield word + suffix


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
