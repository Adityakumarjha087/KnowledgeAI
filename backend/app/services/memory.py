from typing import List, Dict
from app.ai.llm import get_llm_provider


def format_history_for_rewrite(history: List[Dict[str, str]]) -> str:
    """Formats list of message roles and contents into a clear text prompt block"""
    formatted_lines = []
    for msg in history:
        role = "User" if msg["role"] == "user" else "Assistant"
        formatted_lines.append(f"{role}: {msg['content']}")
    return "\n".join(formatted_lines)


def rewrite_query(original_query: str, history: List[Dict[str, str]]) -> str:
    """
    Analyzes conversation history and uses the LLM to rewrite follow-up questions 
    into standalone search queries. Returns the original query if no history is present
    or if running in local/mock mode without an external LLM API key.
    """
    from app.core.config import settings

    if not history:
        return original_query

    # If no real external LLM API key is configured, preserve user's original query
    api_key = settings.LLM_API_KEY
    if not api_key or "your_" in api_key or "placeholder" in api_key:
        return original_query
        
    # Grab the last 4 messages to keep context window compact and fast
    history_text = format_history_for_rewrite(history[-4:])
    
    system_prompt = (
        "You are an AI query rewriting assistant. Given a conversation history and a follow-up question, "
        "your job is to rewrite the follow-up question into a standalone, complete search query term. "
        "The standalone query must preserve the intent and context of the conversation. "
        "Do not write paragraphs or answer the question; only return the rewritten standalone query string. "
        "If the follow-up question is already complete and doesn't depend on history, return it exactly."
    )
    
    user_prompt = f"History:\n{history_text}\n\nFollow-up Question: {original_query}\nStandalone Query:"
    
    try:
        llm = get_llm_provider()
        tokens = llm.generate_stream(system_prompt, user_prompt, [])
        rewritten = "".join(list(tokens)).strip().strip('"').strip("'")
        if rewritten and len(rewritten) < 200 and not rewritten.lower().startswith("i could not"):
            print(f"Rewrote query '{original_query}' -> '{rewritten}'")
            return rewritten
    except Exception as e:
        print(f"Failed to rewrite query: {str(e)}")
        
    return original_query
