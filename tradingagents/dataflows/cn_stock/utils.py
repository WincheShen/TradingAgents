"""Utilities for Chinese A-share ticker handling.

This module has NO akshare dependency so it can be imported safely
even when akshare is not installed (e.g. for ticker detection in the CLI).
"""

import re
import time
import logging

logger = logging.getLogger(__name__)

# Shanghai Stock Exchange prefixes
_SSE_PREFIXES = ("600", "601", "603", "605", "688", "689")

# Shenzhen Stock Exchange prefixes
_SZSE_PREFIXES = ("000", "001", "002", "003", "300", "301")


def to_akshare_code(symbol: str) -> str:
    """Convert any ticker format to bare 6-digit AKShare code.

    Examples:
        600519.SS -> 600519
        000858.SZ -> 000858
        sh600519  -> 600519
        600519    -> 600519
    """
    s = symbol.strip().upper()
    # Strip yfinance-style exchange suffix (.SS, .SZ, .SH)
    s = re.sub(r"\.(SS|SH|SZ)$", "", s)
    # Strip prefix (SH/SZ)
    s = re.sub(r"^(SH|SZ)", "", s)
    return s


def to_em_code(symbol: str) -> str:
    """Convert to East Money format: SH600519 or SZ000858."""
    code = to_akshare_code(symbol)
    if code.startswith(_SSE_PREFIXES):
        return f"SH{code}"
    elif code.startswith(_SZSE_PREFIXES):
        return f"SZ{code}"
    return code


def detect_exchange_suffix(code: str) -> str:
    """Return yfinance-style exchange suffix (.SS or .SZ) for a bare A-share code.

    Returns empty string if the code is not a recognized A-share prefix.
    """
    bare = to_akshare_code(code)
    if bare.startswith(_SSE_PREFIXES):
        return ".SS"
    elif bare.startswith(_SZSE_PREFIXES):
        return ".SZ"
    return ""


def is_cn_ticker(symbol: str) -> bool:
    """Check if a symbol looks like a Chinese A-share ticker.

    Recognizes formats:
      - 600519.SS / 000858.SZ  (yfinance style)
      - SH600519 / SZ000858    (East Money style)
      - 600519 / 000858        (bare 6-digit code)
    """
    s = symbol.strip().upper()
    # Already has .SS or .SZ suffix
    if re.search(r"\.(SS|SZ)$", s):
        return True
    # Has SH/SZ prefix
    if re.match(r"^(SH|SZ)\d{6}$", s):
        return True
    # Bare 6-digit code matching known prefixes
    bare = re.sub(r"^(SH|SZ)", "", re.sub(r"\.(SS|SH|SZ)$", "", s))
    if re.match(r"^\d{6}$", bare):
        return bare.startswith(_SSE_PREFIXES + _SZSE_PREFIXES)
    return False


def normalize_cn_ticker(symbol: str) -> str:
    """Normalize a Chinese ticker to yfinance-compatible format (e.g. 600519.SS).

    Returns the original symbol unchanged if it's not a recognized A-share code.
    """
    code = to_akshare_code(symbol)
    suffix = detect_exchange_suffix(code)
    if suffix:
        return f"{code}{suffix}"
    return symbol.strip().upper()


def akshare_retry(func, max_retries: int = 3, base_delay: float = 2.0):
    """Execute an AKShare call with exponential backoff on rate limits.

    Retries on common transient errors (rate limiting, network hiccups).
    Other exceptions propagate immediately.
    """
    retryable_keywords = ("频率", "rate", "限制", "timeout", "timed out", "connection")
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            msg = str(e).lower()
            is_retryable = any(kw in msg for kw in retryable_keywords)
            if is_retryable and attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    "AKShare error (%s), retrying in %.0fs (attempt %d/%d)",
                    e, delay, attempt + 1, max_retries,
                )
                time.sleep(delay)
            else:
                raise
