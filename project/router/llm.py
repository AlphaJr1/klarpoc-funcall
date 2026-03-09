import os
from openai import OpenAI

from .config import OLLAMA_MODEL, OLLAMA_BASE_URL

class ChatCompletionsWrapper:
    def __init__(self, raw_completions):
        self.raw_completions = raw_completions

    def create(self, model, messages, **kwargs):
        # Always force the model to Ollama's model
        return self.raw_completions.create(
            model=OLLAMA_MODEL,
            messages=messages,
            **kwargs
        )

class ChatWrapper:
    def __init__(self, raw_chat):
        self.completions = ChatCompletionsWrapper(raw_chat.completions)

class CustomLLMClient:
    def __init__(self):
        self._client = OpenAI(
            api_key=os.environ.get("OLLAMA_API_KEY", "dummy"),
            base_url=f"{OLLAMA_BASE_URL}/v1"
        )
        self.chat = ChatWrapper(self._client.chat)

def get_llm_client() -> CustomLLMClient:
    return CustomLLMClient()
