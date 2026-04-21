"""AKShare-based Chinese A-share stock data (OHLCV)."""

import os
import logging
from datetime import datetime
from typing import Annotated

import pandas as pd

from ..config import get_config
from ..stockstats_utils import _clean_dataframe
from .utils import to_akshare_code, akshare_retry

logger = logging.getLogger(__name__)


def load_ohlcv_akshare(symbol: str, curr_date: str) -> pd.DataFrame:
    """Fetch A-share OHLCV data with caching, filtered to prevent look-ahead bias.

    Downloads 5 years of daily data and caches per symbol.
    Rows after *curr_date* are filtered out for backtest safety.
    """
    import akshare as ak

    config = get_config()
    curr_date_dt = pd.to_datetime(curr_date)
    code = to_akshare_code(symbol)

    today_date = pd.Timestamp.today()
    start_date = today_date - pd.DateOffset(years=5)
    start_str = start_date.strftime("%Y%m%d")
    end_str = today_date.strftime("%Y%m%d")

    os.makedirs(config["data_cache_dir"], exist_ok=True)
    data_file = os.path.join(
        config["data_cache_dir"],
        f"{code}-AKShare-data-{start_str}-{end_str}.csv",
    )

    if os.path.exists(data_file):
        data = pd.read_csv(data_file, on_bad_lines="skip")
    else:
        df = akshare_retry(lambda: ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start_str,
            end_date=end_str,
            adjust="qfq",
        ))
        col_map = {
            "日期": "Date",
            "开盘": "Open",
            "收盘": "Close",
            "最高": "High",
            "最低": "Low",
            "成交量": "Volume",
        }
        df = df.rename(columns=col_map)
        keep = [c for c in ["Date", "Open", "High", "Low", "Close", "Volume"] if c in df.columns]
        data = df[keep]
        data.to_csv(data_file, index=False)

    data = _clean_dataframe(data)
    data = data[data["Date"] <= curr_date_dt]
    return data


def get_stock_data(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """Retrieve A-share OHLCV stock data via AKShare."""
    import akshare as ak

    code = to_akshare_code(symbol)
    start_fmt = start_date.replace("-", "")
    end_fmt = end_date.replace("-", "")

    try:
        df = akshare_retry(lambda: ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start_fmt,
            end_date=end_fmt,
            adjust="qfq",
        ))
    except Exception as e:
        return f"No data found for symbol '{symbol}' between {start_date} and {end_date}: {e}"

    if df is None or df.empty:
        return f"No data found for symbol '{symbol}' between {start_date} and {end_date}"

    col_map = {
        "日期": "Date",
        "开盘": "Open",
        "收盘": "Close",
        "最高": "High",
        "最低": "Low",
        "成交量": "Volume",
        "成交额": "Amount",
        "振幅": "Amplitude",
        "涨跌幅": "Change%",
        "涨跌额": "Change",
        "换手率": "Turnover%",
    }
    df = df.rename(columns=col_map)

    keep = [c for c in ["Date", "Open", "High", "Low", "Close", "Volume"] if c in df.columns]
    df = df[keep]

    for col in ["Open", "High", "Low", "Close"]:
        if col in df.columns:
            df[col] = df[col].round(2)

    csv_string = df.to_csv(index=False)

    header = f"# Stock data for {symbol.upper()} from {start_date} to {end_date}\n"
    header += f"# Total records: {len(df)}\n"
    header += f"# Data source: AKShare (A-share, forward-adjusted)\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    return header + csv_string
