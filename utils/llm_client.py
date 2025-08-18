#!/usr/bin/env python3
"""
LLM Provider Abstraction (Additive, non-invasive)
- Claude (Anthropic) primary
- OpenAI fallback (optional)

Security:
- Reads API keys from environment variables only:
  * ANTHROPIC_API_KEY
  * OPENAI_API_KEY
- Does NOT write keys to repo/config.

This module is self-contained and safe to import even if keys are missing.
It will raise a clear RuntimeError when a provider is used without a key.
"""
from __future__ import annotations
import os
import json
from typing import Any, Dict, Iterable, List, Optional

try:
    import requests
except Exception:  # requests should already be present in project
    requests = None  # type: ignore


class LLMResponse:
    def __init__(self, text: str, raw: Optional[Dict[str, Any]] = None):
        self.text = text
        self.raw = raw or {}


class BaseLLMClient:
    def __init__(self, model: str, temperature: float = 0.2, timeout: int = 30):
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

    def generate(self, system: str, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None,
                 tool_choice: Optional[str] = None, stream: bool = False) -> LLMResponse:
        raise NotImplementedError


class ClaudeClient(BaseLLMClient):
    """Anthropic Claude client using the HTTP API."""
    def __init__(self, model: str = "claude-3-5-sonnet-20240620", temperature: float = 0.2, timeout: int = 30):
        super().__init__(model, temperature, timeout)
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set in environment.")
        self.base_url = os.getenv("ANTHROPIC_API_BASE", "https://api.anthropic.com")

    def generate(self, system: str, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None,
                 tool_choice: Optional[str] = None, stream: bool = False) -> LLMResponse:
        if requests is None:
            raise RuntimeError("requests library is required for ClaudeClient")

        url = f"{self.base_url}/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "system": system,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": 2048,
        }
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice

        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        # Extract concatenated text from output content blocks
        text_parts: List[str] = []
        for block in data.get("content", []) or []:
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
        return LLMResponse(text="\n".join(text_parts), raw=data)


class OpenAIClient(BaseLLMClient):
    """OpenAI Chat Completions client via REST (no openai SDK dependency)."""
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.2, timeout: int = 30):
        super().__init__(model, temperature, timeout)
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY not set in environment.")
        self.base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com")

    def generate(self, system: str, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None,
                 tool_choice: Optional[str] = None, stream: bool = False) -> LLMResponse:
        if requests is None:
            raise RuntimeError("requests library is required for OpenAIClient")

        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": messages,
            "stream": False,
            "max_tokens": 2048,
        }
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice

        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return LLMResponse(text=text, raw=data)


def build_llm_from_config(config: Dict[str, Any]) -> Optional[BaseLLMClient]:
    """Create an LLM client from a cloud_config-like dict. Returns None if disabled."""
    llm_cfg = config.get("llm", {})
    if not llm_cfg or not llm_cfg.get("enabled", False):
        return None

    provider = llm_cfg.get("provider", "claude").lower()
    model = llm_cfg.get("model") or ("claude-3-5-sonnet-20240620" if provider == "claude" else "gpt-4o")
    temperature = float(llm_cfg.get("temperature", 0.2))
    timeout = int(llm_cfg.get("timeout", 30))

    if provider == "claude":
        return ClaudeClient(model=model, temperature=temperature, timeout=timeout)
    elif provider == "openai":
        return OpenAIClient(model=model, temperature=temperature, timeout=timeout)
    else:
        raise ValueError(f"Unsupported llm.provider: {provider}")
