"""AKShare-based technical indicators for Chinese A-shares.

Reuses the stockstats library for indicator calculation, but sources
OHLCV data from AKShare instead of yfinance.
"""

import logging
from datetime import datetime
from typing import Annotated

import pandas as pd
from dateutil.relativedelta import relativedelta
from stockstats import wrap

from .akshare_stock import load_ohlcv_akshare
from .utils import to_akshare_code

logger = logging.getLogger(__name__)

# Same indicator descriptions as the yfinance implementation for consistency
_INDICATOR_INFO = {
    "close_50_sma": (
        "50 SMA: A medium-term trend indicator. "
        "Usage: Identify trend direction and serve as dynamic support/resistance."
    ),
    "close_200_sma": (
        "200 SMA: A long-term trend benchmark. "
        "Usage: Confirm overall market trend and identify golden/death cross setups."
    ),
    "close_10_ema": (
        "10 EMA: A responsive short-term average. "
        "Usage: Capture quick shifts in momentum and potential entry points."
    ),
    "macd": "MACD: Momentum via differences of EMAs. Look for crossovers and divergence.",
    "macds": "MACD Signal: EMA smoothing of the MACD line.",
    "macdh": "MACD Histogram: Gap between MACD line and its signal.",
    "rsi": (
        "RSI: Measures momentum to flag overbought/oversold conditions. "
        "Apply 70/30 thresholds and watch for divergence."
    ),
    "boll": "Bollinger Middle: 20 SMA serving as basis for Bollinger Bands.",
    "boll_ub": "Bollinger Upper Band: 2 std devs above the middle line.",
    "boll_lb": "Bollinger Lower Band: 2 std devs below the middle line.",
    "atr": "ATR: Average true range measuring volatility.",
    "vwma": "VWMA: Moving average weighted by volume.",
    "mfi": "MFI: Money Flow Index using price and volume to measure buying/selling pressure.",
}


def _get_bulk_indicators(symbol: str, indicator: str, curr_date: str) -> dict:
    """Calculate indicator values for all available dates in one pass."""
    data = load_ohlcv_akshare(symbol, curr_date)
    df = wrap(data)
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    df[indicator]  # trigger stockstats calculation

    result = {}
    for _, row in df.iterrows():
        val = row[indicator]
        result[row["Date"]] = "N/A" if pd.isna(val) else str(val)
    return result


def get_indicators(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[str, "The current trading date, YYYY-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    """Retrieve technical indicator data for an A-share stock via AKShare + stockstats."""
    if indicator not in _INDICATOR_INFO:
        raise ValueError(
            f"Indicator {indicator} is not supported. Choose from: {list(_INDICATOR_INFO.keys())}"
        )

    curr_date_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    before = curr_date_dt - relativedelta(days=look_back_days)

    try:
        bulk = _get_bulk_indicators(symbol, indicator, curr_date)

        date_values = []
        dt = curr_date_dt
        while dt >= before:
            ds = dt.strftime("%Y-%m-%d")
            date_values.append((ds, bulk.get(ds, "N/A: Not a trading day (weekend or holiday)")))
            dt -= relativedelta(days=1)

        ind_string = "".join(f"{d}: {v}\n" for d, v in date_values)
    except Exception as e:
        logger.error("Error getting AKShare indicator data: %s", e)
        ind_string = f"Error: {e}\n"

    desc = _INDICATOR_INFO.get(indicator, "No description available.")
    return (
        f"## {indicator} values from {before.strftime('%Y-%m-%d')} to {curr_date}:\n\n"
        + ind_string
        + "\n\n"
        + desc
    )
