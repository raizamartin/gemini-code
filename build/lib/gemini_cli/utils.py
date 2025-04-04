"""
Utility functions for the Gemini CLI tool.
"""

import tiktoken
import json

def count_tokens(text):
    """
    Count the number of tokens in a text string.
    
    This is a rough estimate for Gemini 2.5 Pro, using GPT-4 tokenizer as a proxy.
    For production, you'd want to use model-specific token counting.
    """
    try:
        encoding = tiktoken.encoding_for_model("gpt-4")
        return len(encoding.encode(text))
    except Exception:
        # Fallback method: roughly 4 chars per token
        return len(text) // 4