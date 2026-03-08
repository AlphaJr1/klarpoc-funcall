import os
import json
from openai import OpenAI
from litellm import completion

from .config import OLLAMA_MODEL, OLLAMA_BASE_URL, _ROOT

# Load Claude API Key
key_path = os.path.join(_ROOT, "..", "api_key", "claude-api-key.txt")
try:
    with open(key_path, "r") as f:
        os.environ["ANTHROPIC_API_KEY"] = f.read().strip()
except Exception:
    pass

class ChatCompletionsWrapper:
    def create(self, model, messages, **kwargs):
        # Translate 'sonnet' vs 'haiku' requests
        if model == "sonnet":
            primary_model = "claude-3-5-sonnet-20241022"
        elif model == "haiku":
            primary_model = "claude-3-5-haiku-20241022"
        else:
            primary_model = model

        # Ensure tools are compatible formatting-wise if needed, but litellm handles it
        try:
            return completion(
                model=primary_model,
                messages=messages,
                **kwargs
            )
        except Exception as e:
            # Fallback to Ollama
            import logging
            logging.getLogger("engine").warning(f"Claude API failed ({str(e)}), falling back to Ollama {OLLAMA_MODEL}")
            
            return completion(
                model=f"openai/{OLLAMA_MODEL}",
                api_base=f"{OLLAMA_BASE_URL}/v1",
                api_key=os.environ.get("OLLAMA_API_KEY", "dummy"),
                messages=messages,
                **kwargs
            )

class ChatWrapper:
    def __init__(self):
        self.completions = ChatCompletionsWrapper()

class CustomLLMClient:
    def __init__(self):
        self.chat = ChatWrapper()
        self.api_key = "dummy"
        self.base_url = "dummy"

def get_llm_client() -> CustomLLMClient:
    return CustomLLMClient()
