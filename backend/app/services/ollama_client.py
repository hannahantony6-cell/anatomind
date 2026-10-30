"""Thin, defensive client for the local Ollama server. The browser never talks to Ollama."""
import time

import httpx

from ..config import get_settings
from ..core.errors import AppError
from ..database import SessionLocal
from ..models import LLMTelemetry


class LLMUnavailable(AppError):
    def __init__(self):
        s = get_settings()
        super().__init__(503, "ollama_unavailable",
                         f"The local AI model server is not reachable at {s.ollama_base_url}. "
                         "Start it with `ollama serve` and try again.")


class ModelNotInstalled(AppError):
    def __init__(self):
        m = get_settings().ollama_model
        super().__init__(503, "model_not_installed",
                         f"The model '{m}' is not installed. Run `ollama pull {m}` and try again.")


class LLMTimeout(AppError):
    def __init__(self):
        super().__init__(504, "llm_timeout", "The local AI model took too long to respond. Please try again.")


class LLMBadOutput(AppError):
    def __init__(self, msg="The AI model returned an unusable response. Please try again."):
        super().__init__(502, "generation_failed", msg)


def record_telemetry(task: str, started: float, success: bool, error_type: str | None = None,
                     validation_failures: int = 0) -> None:
    """Own session so telemetry survives a rolled-back request transaction."""
    try:
        with SessionLocal() as s:
            s.add(LLMTelemetry(task_type=task, model=get_settings().ollama_model,
                               latency_ms=int((time.monotonic() - started) * 1000), success=success,
                               error_type=error_type, validation_failures=validation_failures))
            s.commit()
    except Exception:  # telemetry must never break a request
        pass


def chat(system: str, user: str, *, fmt=None, temperature: float = 0.2, num_predict: int = 2048) -> str:
    """Return the assistant message text. `fmt` may be a JSON schema dict or "json"."""
    s = get_settings()
    payload = {
        "model": s.ollama_model, "stream": False,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "options": {"temperature": temperature, "num_ctx": s.ollama_num_ctx, "num_predict": num_predict},
    }
    if fmt is not None:
        payload["format"] = fmt
    last_err: Exception | None = None
    for attempt in range(s.ollama_max_retries + 1):
        try:
            r = httpx.post(f"{s.ollama_base_url}/api/chat", json=payload, timeout=s.ollama_timeout_seconds)
            if r.status_code == 404:
                raise ModelNotInstalled()
            if r.status_code == 400 and isinstance(fmt, dict):   # older Ollama: no JSON-schema support
                payload["format"] = "json"
                continue
            r.raise_for_status()
            content = (r.json().get("message") or {}).get("content", "")
            if not content.strip():
                raise LLMBadOutput("The AI model returned an empty response.")
            return content
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            last_err = e
        except httpx.ReadTimeout as e:
            last_err = e
        except httpx.HTTPStatusError as e:
            last_err = e
        if attempt < s.ollama_max_retries:
            time.sleep(min(2 ** attempt, 4))
    if isinstance(last_err, (httpx.ConnectError, httpx.ConnectTimeout)):
        raise LLMUnavailable()
    if isinstance(last_err, httpx.ReadTimeout):
        raise LLMTimeout()
    raise LLMBadOutput("The AI model server returned an error. Please try again.")
