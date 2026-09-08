import logging
import json
from typing import List, Dict, Any, AsyncGenerator, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger("ev.llm_router")

class LLMRouter:
    """
    OpenRouter LLM Gateway Client featuring dynamic automatic model fallback.
    Automatically handles rate limits, token exhaustion, context limits, and model outages.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/ev-ai/ev-backend",
            "X-Title": "EV Omnipresent AI Assistant",
            "Content-Type": "application/json"
        }

    def get_fallback_chain(self, primary_override: Optional[str] = None) -> List[str]:
        primary = primary_override or settings.PRIMARY_MODEL
        fallbacks = settings.FALLBACK_MODELS if isinstance(settings.FALLBACK_MODELS, list) else []
        chain = [primary] + [m for m in fallbacks if m != primary]
        return chain

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 2048,
        preferred_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes chat completion with automatic model fallback failover.
        If a model fails due to token limits, rate limits, or server errors,
        it automatically attempts the next model in the fallback chain.
        """
        model_chain = self.get_fallback_chain(preferred_model)
        last_error = None

        for model in model_chain:
            logger.info(f"[LLMRouter] Attempting chat completion with model: {model}")
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
            if max_tokens:
                payload["max_tokens"] = max_tokens
            if tools:
                payload["tools"] = tools

            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self.headers,
                        json=payload
                    )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"[LLMRouter] Success with model: {model}")
                    data["_used_model"] = model
                    return data

                error_body = response.text
                logger.warning(
                    f"[LLMRouter] Model {model} failed with status {response.status_code}: {error_body}"
                )

                # Check retryable status codes: 429 (Rate limit), 402 (Payment/Credits), 400 (Token limit), 5xx
                if response.status_code in (429, 402, 400, 500, 502, 503, 504):
                    last_error = f"Model {model} HTTP {response.status_code}: {error_body}"
                    continue
                else:
                    # Non-retryable client error
                    response.raise_for_status()

            except Exception as e:
                logger.error(f"[LLMRouter] Exception during execution with model {model}: {e}")
                last_error = str(e)
                continue

        raise RuntimeError(f"All models in fallback chain failed. Last error: {last_error}")

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        preferred_model: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streaming chat completion with automatic fallback initialization.
        """
        model_chain = self.get_fallback_chain(preferred_model)
        
        for model in model_chain:
            logger.info(f"[LLMRouter Stream] Attempting streaming with model: {model}")
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": True
            }
            if tools:
                payload["tools"] = tools

            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}/chat/completions",
                        headers=self.headers,
                        json=payload
                    ) as response:

                        if response.status_code != 200:
                            err_content = await response.aread()
                            logger.warning(
                                f"[LLMRouter Stream] Model {model} stream failed ({response.status_code}): {err_content.decode('utf-8', errors='ignore')}"
                            )
                            continue

                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:].strip()
                                if data_str == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(data_str)
                                    chunk["_used_model"] = model
                                    yield chunk
                                except json.JSONDecodeError:
                                    continue
                        return

            except Exception as e:
                logger.error(f"[LLMRouter Stream] Error streaming from model {model}: {e}")
                continue

        raise RuntimeError("All models in streaming fallback chain failed.")

# Global Router Instance
llm_router = LLMRouter()
