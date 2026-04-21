"""AKShare-based fundamental data for Chinese A-shares.

Uses East Money (东方财富) APIs via AKShare for company fundamentals,
balance sheets, income statements, cash flow, and insider transactions.
Data follows Chinese Accounting Standards (CAS).
"""

import logging
from datetime import datetime
from typing import Annotated

import pandas as pd

from .utils import to_akshare_code, to_em_code, akshare_retry

logger = logging.getLogger(__name__)


def get_fundamentals(
    ticker: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "current date (unused, for API compatibility)"] = None,
) -> str:
    """Get company fundamentals overview from East Money via AKShare."""
    import akshare as ak

    code = to_akshare_code(ticker)

    try:
        df = akshare_retry(lambda: ak.stock_individual_info_em(symbol=code))
    except Exception as e:
        return f"Error retrieving fundamentals for {ticker}: {e}"

    if df is None or df.empty:
        return f"No fundamentals data found for symbol '{ticker}'"

    # stock_individual_info_em returns a 2-column DataFrame: item / value
    lines = []
    for _, row in df.iterrows():
        item = row.iloc[0]
        value = row.iloc[1]
        if pd.notna(value) and str(value).strip():
            lines.append(f"{item}: {value}")

    header = f"# Company Fundamentals for {ticker.upper()} (CAS)\n"
    header += f"# Data source: East Money via AKShare\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    return header + "\n".join(lines)


def _get_financial_statement(
    ticker: str,
    stmt_type: str,
    freq: str = "quarterly",
    curr_date: str = None,
) -> str:
    """Generic helper to fetch a financial statement."""
    import akshare as ak

    code = to_akshare_code(ticker)

    func_map = {
        "balance_sheet": ak.stock_balance_sheet_by_report_em,
        "income_statement": ak.stock_profit_sheet_by_report_em,
        "cashflow": ak.stock_cash_flow_sheet_by_report_em,
    }

    if stmt_type not in func_map:
        return f"Unknown statement type: {stmt_type}"

    try:
        # East Money APIs use SH/SZ prefix format
        em_code = to_em_code(ticker)
        df = akshare_retry(lambda: func_map[stmt_type](symbol=em_code))
    except Exception as e:
        return f"Error retrieving {stmt_type} for {ticker}: {e}"

    if df is None or df.empty:
        return f"No {stmt_type} data found for symbol '{ticker}'"

    # Filter by curr_date to prevent look-ahead bias
    if curr_date and "REPORT_DATE_NAME" in df.columns:
        try:
            cutoff = pd.Timestamp(curr_date)
            df["_report_dt"] = pd.to_datetime(df["REPORT_DATE_NAME"], errors="coerce")
            df = df[df["_report_dt"] <= cutoff]
            df = df.drop(columns=["_report_dt"])
        except Exception:
            pass

    # Keep only most recent reports
    max_rows = 4 if freq.lower() == "quarterly" else 2
    if len(df) > max_rows:
        df = df.head(max_rows)

    csv_string = df.to_csv(index=False)

    label = stmt_type.replace("_", " ").title()
    header = f"# {label} for {ticker.upper()} ({freq}, CAS)\n"
    header += f"# Data source: East Money via AKShare\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    return header + csv_string


def get_balance_sheet(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None,
) -> str:
    """Get balance sheet data for a Chinese A-share company."""
    return _get_financial_statement(ticker, "balance_sheet", freq, curr_date)


def get_cashflow(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None,
) -> str:
    """Get cash flow data for a Chinese A-share company."""
    return _get_financial_statement(ticker, "cashflow", freq, curr_date)


def get_income_statement(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None,
) -> str:
    """Get income statement data for a Chinese A-share company."""
    return _get_financial_statement(ticker, "income_statement", freq, curr_date)


def get_insider_transactions(
    ticker: Annotated[str, "ticker symbol of the company"],
) -> str:
    """Get major shareholder changes (股东增减持) for a Chinese A-share company.

    In the Chinese market this covers 大股东增减持 (major shareholder
    increases/decreases) rather than SEC-style insider transactions.
    """
    import akshare as ak

    code = to_akshare_code(ticker)

    try:
        df = akshare_retry(lambda: ak.stock_inner_trade_xq(symbol=code))
    except Exception:
        # Fallback: try East Money shareholder changes
        try:
            em_code = to_em_code(ticker)
            df = akshare_retry(lambda: ak.stock_changes_em(symbol=em_code))
        except Exception as e:
            return f"No insider/shareholder transaction data found for {ticker}: {e}"

    if df is None or df.empty:
        return f"No insider/shareholder transaction data found for symbol '{ticker}'"

    # Keep recent entries
    if len(df) > 20:
        df = df.head(20)

    csv_string = df.to_csv(index=False)

    header = f"# Shareholder Changes for {ticker.upper()}\n"
    header += f"# Data source: AKShare\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    return header + csv_string
