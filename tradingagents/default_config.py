import os

_TRADINGAGENTS_HOME = os.path.join(os.path.expanduser("~"), ".tradingagents")

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", os.path.join(_TRADINGAGENTS_HOME, "logs")),
    "data_cache_dir": os.getenv("TRADINGAGENTS_CACHE_DIR", os.path.join(_TRADINGAGENTS_HOME, "cache")),
    # LLM settings
    "llm_provider": "openai",
    "deep_think_llm": "gpt-5.3-chat",
    "quick_think_llm": "gpt-5.3-chat",
    "backend_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    # Provider-specific thinking configuration
    "google_thinking_level": None,      # "high", "minimal", etc.
    "openai_reasoning_effort": None,    # "medium", "high", "low"
    "anthropic_effort": None,           # "high", "medium", "low"
    # Output language for analyst reports and final decision
    # Internal agent debate stays in English for reasoning quality
    "output_language": "English",
    # Market setting: "us" (default) or "cn" (Chinese A-share)
    # When set to "cn", data vendors automatically switch to akshare
    "market": "us",
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # Data vendor configuration
    # Category-level configuration (default for all tools in category)
    "data_vendors": {
        "core_stock_apis": "yfinance",       # Options: alpha_vantage, yfinance, akshare
        "technical_indicators": "yfinance",  # Options: alpha_vantage, yfinance, akshare
        "fundamental_data": "yfinance",      # Options: alpha_vantage, yfinance, akshare
        "news_data": "yfinance",             # Options: alpha_vantage, yfinance, akshare
    },
    # Tool-level configuration (takes precedence over category-level)
    "tool_vendors": {
        # Example: "get_stock_data": "alpha_vantage",  # Override category default
    },
}


def apply_market_defaults(config: dict) -> dict:
    """Apply market-specific vendor defaults when market is set to 'cn'.

    If the user explicitly configured a vendor for a category, that takes
    precedence. Only categories still on the factory default are switched.
    """
    if config.get("market") != "cn":
        return config

    default_vendors = DEFAULT_CONFIG["data_vendors"]
    vendors = config.get("data_vendors", {})
    for category in default_vendors:
        # Only override if still on the original default (yfinance)
        if vendors.get(category) == default_vendors[category]:
            vendors[category] = "akshare"
    config["data_vendors"] = vendors
    return config
