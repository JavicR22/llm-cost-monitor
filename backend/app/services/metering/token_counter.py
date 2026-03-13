"""
Token counting — 2.2

Uses tiktoken for OpenAI models. Falls back to a character-based estimate
for unknown models (1 token ≈ 4 chars is the standard approximation).

OpenAI chat format overhead (from their cookbook):
  - Each message: 3 tokens
  - Each key in a message dict: varies (role, content, name)
  - Reply priming: 3 tokens appended by the API
"""
from __future__ import annotations

import structlog

log = structlog.get_logger()

# Tiktoken encoding per model family.
# cl100k_base  → GPT-4, GPT-3.5-turbo, text-embedding-ada-002
# o200k_base   → GPT-4o, GPT-4o-mini, o1, o3
_MODEL_ENCODING: dict[str, str] = {
    "gpt-4o": "o200k_base",
    "gpt-4o-mini": "o200k_base",
    "o1": "o200k_base",
    "o1-mini": "o200k_base",
    "o3": "o200k_base",
    "o3-mini": "o200k_base",
    "gpt-4": "cl100k_base",
    "gpt-4-turbo": "cl100k_base",
    "gpt-4-turbo-preview": "cl100k_base",
    "gpt-3.5-turbo": "cl100k_base",
    "gpt-3.5-turbo-16k": "cl100k_base",
}

_FALLBACK_ENCODING = "cl100k_base"
_CHARS_PER_TOKEN = 4  # rough estimate for unknown models


def _get_encoding(model: str):
    """Return a tiktoken encoding, falling back gracefully."""
    import tiktoken

    encoding_name = _MODEL_ENCODING.get(model)
    if encoding_name:
        return tiktoken.get_encoding(encoding_name)

    # Try tiktoken's own model lookup before our fallback
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        log.debug("token_counter_unknown_model", model=model, fallback=_FALLBACK_ENCODING)
        return tiktoken.get_encoding(_FALLBACK_ENCODING)


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count tokens in a plain string."""
    if not text:
        return 0
    try:
        enc = _get_encoding(model)
        return len(enc.encode(text))
    except Exception:
        return max(1, len(text) // _CHARS_PER_TOKEN)


def count_messages_tokens(messages: list[dict], model: str = "gpt-4o") -> int:
    """
    Count tokens for a list of chat messages (the input to /chat/completions).

    Applies OpenAI's per-message overhead:
      - 3 tokens per message (message framing)
      - 1 extra token if the message has a 'name' field
      - 3 tokens for reply priming (appended by the API)
    """
    if not messages:
        return 0

    try:
        enc = _get_encoding(model)
    except Exception:
        # Pure fallback — sum raw chars / 4
        total = sum(len(str(m)) // _CHARS_PER_TOKEN for m in messages)
        return total + 3

    token_count = 3  # reply priming
    for message in messages:
        token_count += 3  # per-message overhead
        for key, value in message.items():
            if isinstance(value, str):
                token_count += len(enc.encode(value))
            if key == "name":
                token_count += 1  # name field adds 1 token
    return token_count


def extract_usage_from_response(response: dict) -> tuple[int, int]:
    """
    Extract (input_tokens, output_tokens) from an OpenAI JSON response.

    The 'usage' object is always present in non-streaming responses.
    Returns (0, 0) if missing — caller should fall back to tiktoken counting.
    """
    usage = response.get("usage")
    if not usage:
        return 0, 0
    return usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def extract_usage_from_streaming_chunks(chunks: list[str], model: str = "gpt-4o") -> tuple[int, int]:
    """
    Parse SSE chunks to extract token usage.

    OpenAI streaming with stream_options.include_usage=true sends a final
    chunk with a usage object. If not present, we count output tokens from
    the content deltas using tiktoken.

    Returns (prompt_tokens, completion_tokens).
    Note: prompt_tokens from streaming is always 0 unless include_usage=true.
    """
    import json

    prompt_tokens = 0
    completion_tokens = 0
    content_pieces: list[str] = []

    for raw in chunks:
        for line in raw.splitlines():
            if not line.startswith("data: "):
                continue
            payload = line[6:].strip()
            if payload in ("", "[DONE]"):
                continue
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                continue

            # Final chunk with usage (requires stream_options.include_usage=true)
            if data.get("usage"):
                u = data["usage"]
                return u.get("prompt_tokens", 0), u.get("completion_tokens", 0)

            # Accumulate content deltas for fallback counting
            for choice in data.get("choices", []):
                delta = choice.get("delta", {})
                piece = delta.get("content") or ""
                if piece:
                    content_pieces.append(piece)

    # Fallback — count accumulated content with tiktoken
    if content_pieces:
        completion_tokens = count_tokens("".join(content_pieces), model)

    return prompt_tokens, completion_tokens
