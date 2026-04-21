"""AKShare-based news data for Chinese A-shares.

Uses East Money (东方财富) for stock-specific news and CCTV/macro
sources for global Chinese economic news.
"""

import logging
from datetime import datetime
from typing import Annotated

from dateutil.relativedelta import relativedelta

from .utils import to_akshare_code, akshare_retry

logger = logging.getLogger(__name__)


def get_news(
    ticker: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """Retrieve news for a Chinese A-share stock from East Money."""
    import akshare as ak

    code = to_akshare_code(ticker)

    try:
        df = akshare_retry(lambda: ak.stock_news_em(symbol=code))
    except Exception as e:
        return f"Error fetching news for {ticker}: {e}"

    if df is None or df.empty:
        return f"No news found for {ticker}"

    # Normalize column names (AKShare may return Chinese or English)
    col_map = {
        "新闻标题": "title",
        "新闻内容": "summary",
        "发布时间": "pub_date",
        "文章来源": "source",
        "新闻链接": "link",
    }
    df = df.rename(columns=col_map)

    # Filter by date range if pub_date is available
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    if "pub_date" in df.columns:
        try:
            df["_dt"] = df["pub_date"].apply(
                lambda x: datetime.strptime(str(x)[:10], "%Y-%m-%d") if x else None
            )
            df = df[df["_dt"].notna()]
            df = df[(df["_dt"] >= start_dt) & (df["_dt"] <= end_dt + relativedelta(days=1))]
            df = df.drop(columns=["_dt"])
        except Exception:
            pass  # keep all if date parsing fails

    if df.empty:
        return f"No news found for {ticker} between {start_date} and {end_date}"

    # Format output
    news_str = ""
    for _, row in df.head(20).iterrows():
        title = row.get("title", "No title")
        source = row.get("source", "Unknown")
        summary = row.get("summary", "")
        link = row.get("link", "")

        news_str += f"### {title} (source: {source})\n"
        if summary:
            # Truncate long summaries
            if len(str(summary)) > 500:
                summary = str(summary)[:500] + "..."
            news_str += f"{summary}\n"
        if link:
            news_str += f"Link: {link}\n"
        news_str += "\n"

    return f"## {ticker} News, from {start_date} to {end_date}:\n\n{news_str}"


def get_global_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back"] = 7,
    limit: Annotated[int, "Maximum number of articles"] = 10,
) -> str:
    """Retrieve Chinese macro economic news.

    Tries multiple sources: CCTV economic news, East Money macro news.
    Covers PBOC policy, A-share market sentiment, and China economic indicators.
    """
    import akshare as ak

    curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    start_dt = curr_dt - relativedelta(days=look_back_days)
    start_date = start_dt.strftime("%Y-%m-%d")

    all_articles = []

    # Source 1: CCTV news (联播)
    try:
        date_str = curr_dt.strftime("%Y%m%d")
        cctv_df = akshare_retry(lambda: ak.news_cctv(date=date_str))
        if cctv_df is not None and not cctv_df.empty:
            for _, row in cctv_df.iterrows():
                title = row.get("title", "")
                # Only keep economy-related news
                keywords = ("经济", "金融", "央行", "利率", "通胀", "GDP", "PMI",
                            "股市", "A股", "市场", "政策", "改革", "贸易")
                if any(kw in str(title) for kw in keywords):
                    all_articles.append({
                        "title": title,
                        "source": "CCTV",
                        "summary": row.get("content", "")[:300] if row.get("content") else "",
                    })
    except Exception as e:
        logger.debug("CCTV news unavailable: %s", e)

    # Source 2: East Money financial news (财经要闻)
    try:
        em_df = akshare_retry(lambda: ak.stock_info_global_em())
        if em_df is not None and not em_df.empty:
            for _, row in em_df.head(limit).iterrows():
                title = row.get("标题", row.get("title", ""))
                summary = row.get("内容", row.get("content", ""))
                if title:
                    all_articles.append({
                        "title": title,
                        "source": "East Money",
                        "summary": str(summary)[:300] if summary else "",
                    })
    except Exception as e:
        logger.debug("East Money global news unavailable: %s", e)

    if not all_articles:
        return f"No global/macro news found for {curr_date}"

    # Deduplicate by title
    seen = set()
    unique = []
    for a in all_articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)

    news_str = ""
    for a in unique[:limit]:
        news_str += f"### {a['title']} (source: {a['source']})\n"
        if a["summary"]:
            news_str += f"{a['summary']}\n"
        news_str += "\n"

    return f"## Chinese Market & Macro News, from {start_date} to {curr_date}:\n\n{news_str}"
