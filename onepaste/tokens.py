"""Token counting with graceful degradation.

Uses tiktoken (o200k_base) when available for exact counts; falls back to a
characters/4 estimate when the optional dependency is missing or the encoding
cannot be loaded (e.g. offline first run).
"""

from typing import Any, Optional

try:
    import tiktoken as _tiktoken
except ImportError:  # pragma: no cover - exercised via fallback tests
    _tiktoken = None  # type: ignore[assignment]

CHARS_PER_TOKEN_ESTIMATE = 4
_ENCODING_NAME = "o200k_base"

_encoding: Optional[Any] = None
_encoding_failed = False


def _get_encoding() -> Optional[Any]:
    global _encoding, _encoding_failed
    if _encoding is not None or _encoding_failed:
        return _encoding
    if _tiktoken is None:
        _encoding_failed = True
        return None
    try:
        _encoding = _tiktoken.get_encoding(_ENCODING_NAME)
    except Exception:
        _encoding_failed = True
    return _encoding


def is_exact() -> bool:
    """True when counts come from tiktoken rather than the estimator."""
    return _get_encoding() is not None


def method_label() -> str:
    """Human-readable label describing the counting method."""
    if is_exact():
        return f"tiktoken {_ENCODING_NAME}"
    return f"estimate (~{CHARS_PER_TOKEN_ESTIMATE} chars/token)"


def count_tokens(text: str) -> int:
    """Count tokens in text, degrading to an estimate when needed."""
    encoding = _get_encoding()
    if encoding is not None:
        try:
            return len(encoding.encode(text))
        except Exception:
            pass
    return max(1, (len(text) + CHARS_PER_TOKEN_ESTIMATE - 1) // CHARS_PER_TOKEN_ESTIMATE)
