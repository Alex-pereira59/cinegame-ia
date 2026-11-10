"""Cliente de modelo de lenguaje.

Se usa la API compatible con OpenAI, por lo que sirve para Groq, OpenAI,
Together, OpenRouter, etc. cambiando LLM_BASE_URL / LLM_MODEL / LLM_API_KEY.
El consumo de tokens se toma del campo `usage` que devuelve el proveedor.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from ..config import get_settings

log = logging.getLogger(__name__)


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: str  # JSON


@dataclass
class LLMResponse:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0


def estimate_tokens(text: str) -> int:
    """Estimación de respaldo (~4 caracteres por token) si el proveedor no reporta usage."""
    return max(1, len(text) // 4) if text else 0


class LLMClient:
    def chat(self, messages: list[dict], tools: list[dict] | None = None,
             model: str | None = None, temperature: float = 0.3) -> LLMResponse:
        raise NotImplementedError


class OpenAICompatibleLLM(LLMClient):
    def __init__(self, api_key: str, base_url: str, model: str):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=60)
        self.model = model

    def chat(self, messages, tools=None, model=None, temperature=0.3) -> LLMResponse:
        from openai import BadRequestError

        kwargs: dict[str, Any] = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        try:
            resp = self.client.chat.completions.create(**kwargs)
        except BadRequestError as e:
            # Algunos modelos generan llamadas a herramientas mal formadas (tool_use_failed).
            # Se reintenta una vez; si vuelve a fallar se pide respuesta sin herramientas.
            log.warning("Error del proveedor, reintentando: %s", e)
            try:
                resp = self.client.chat.completions.create(**kwargs)
            except BadRequestError:
                kwargs.pop("tools", None)
                kwargs.pop("tool_choice", None)
                kwargs["messages"] = _strip_tool_messages(messages)
                resp = self.client.chat.completions.create(**kwargs)

        choice = resp.choices[0].message
        calls = [
            ToolCall(id=tc.id, name=tc.function.name, arguments=tc.function.arguments or "{}")
            for tc in (choice.tool_calls or [])
        ]
        usage = resp.usage
        content = choice.content or ""
        return LLMResponse(
            content=content,
            tool_calls=calls,
            tokens_in=usage.prompt_tokens if usage else estimate_tokens(json.dumps(messages)),
            tokens_out=usage.completion_tokens if usage else estimate_tokens(content),
        )


def _strip_tool_messages(messages: list[dict]) -> list[dict]:
    """Convierte el historial con herramientas en texto plano para un último intento sin tools."""
    out = []
    for m in messages:
        if m["role"] == "tool":
            out.append({"role": "user", "content": f"Resultado de herramienta: {m['content'][:3000]}"})
        elif m["role"] == "assistant" and m.get("tool_calls"):
            names = ", ".join(tc["function"]["name"] for tc in m["tool_calls"])
            out.append({"role": "assistant", "content": m.get("content") or f"(consulté: {names})"})
        else:
            out.append(m)
    return out


class FakeLLM(LLMClient):
    """Modelo simulado: permite probar la app sin API key (LLM_PROVIDER=fake)."""

    def chat(self, messages, tools=None, model=None, temperature=0.3) -> LLMResponse:
        system = messages[0]["content"] if messages else ""
        question = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        tool_results = [m["content"] for m in messages if m["role"] == "tool"]
        if tools and not tool_results:
            first = tools[0]["function"]
            args = {}
            props = first.get("parameters", {}).get("properties", {})
            for name in ("consulta", "texto", "titulo"):
                if name in props:
                    args[name] = question[:80]
                    break
            return LLMResponse(content="", tool_calls=[ToolCall("call_1", first["name"], json.dumps(args))],
                               tokens_in=estimate_tokens(system + question), tokens_out=10)
        if tool_results:
            content = "[Modo demo] Resultados obtenidos de las herramientas:\n" + tool_results[-1][:600]
        elif "\n\nCONTEXTO" in system and "SIN RESULTADOS" not in system:
            ctx = system.split("\n\nCONTEXTO", 1)[1][:700]
            content = f"[Modo demo] Según el catálogo:\n{ctx}"
        else:
            content = "[Modo demo] No tengo información suficiente en el catálogo para responder."
        return LLMResponse(content=content, tokens_in=estimate_tokens(system + question),
                           tokens_out=estimate_tokens(content))


_client: LLMClient | None = None


def get_llm() -> LLMClient:
    """Dependencia FastAPI. En las pruebas se reemplaza con dependency_overrides."""
    global _client
    if _client is None:
        s = get_settings()
        if s.llm_provider == "fake" or not s.llm_api_key:
            log.warning("Usando FakeLLM (sin API key o LLM_PROVIDER=fake)")
            _client = FakeLLM()
        else:
            _client = OpenAICompatibleLLM(s.llm_api_key, s.llm_base_url, s.llm_model)
    return _client
