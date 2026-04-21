"""Chinese A-share data vendor powered by AKShare.

Provides the same interface as the yfinance and alpha_vantage vendors
so it can be plugged into the vendor routing system in interface.py.

Requires: pip install akshare  (or: pip install tradingagents[cn])
"""

from .akshare_stock import get_stock_data
from .akshare_indicator import get_indicators
from .akshare_fundamental import (
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement,
    get_insider_transactions,
)
from .akshare_news import get_news, get_global_news

# Ticker utilities (no akshare dependency)
from .utils import is_cn_ticker, normalize_cn_ticker, to_akshare_code, detect_exchange_suffix

__all__ = [
    "get_stock_data",
    "get_indicators",
    "get_fundamentals",
    "get_balance_sheet",
    "get_cashflow",
    "get_income_statement",
    "get_insider_transactions",
    "get_news",
    "get_global_news",
    "is_cn_ticker",
    "normalize_cn_ticker",
    "to_akshare_code",
    "detect_exchange_suffix",
]
