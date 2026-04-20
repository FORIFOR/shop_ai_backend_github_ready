import logging

import httpx

from app.config import (
    LOCAL_DEEP_LLM_BASE_URL,
    LOCAL_DEEP_LLM_MODEL,
    LOCAL_FAST_LLM_BASE_URL,
    LOCAL_FAST_LLM_MODEL,
)

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(60.0, connect=10.0)


class LlmDispatcher:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def generate_fast(self, messages: list[dict]) -> str:
        return await self._call(
            base_url=LOCAL_FAST_LLM_BASE_URL,
            model=LOCAL_FAST_LLM_MODEL,
            messages=messages,
            label="fast",
        )

    async def generate_deep(self, messages: list[dict]) -> str:
        try:
            return await self._call(
                base_url=LOCAL_DEEP_LLM_BASE_URL,
                model=LOCAL_DEEP_LLM_MODEL,
                messages=messages,
                label="deep",
            )
        except Exception:
            logger.warning("deep LLM failed, falling back to fast LLM")
            return await self.generate_fast(messages)

    async def _call(
        self,
        base_url: str,
        model: str,
        messages: list[dict],
        label: str,
    ) -> str:
        url = f"{base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
        }
        logger.info("LLM request [%s]: %s model=%s", label, url, model)
        resp = await self._client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return content

    async def close(self) -> None:
        await self._client.aclose()
