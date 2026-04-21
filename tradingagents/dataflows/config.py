import tradingagents.default_config as default_config
from tradingagents.default_config import apply_market_defaults
from typing import Dict, Optional

# Use default config but allow it to be overridden
_config: Optional[Dict] = None


def initialize_config():
    """Initialize the configuration with default values."""
    global _config
    if _config is None:
        _config = default_config.DEFAULT_CONFIG.copy()


def set_config(config: Dict):
    """Update the configuration with custom values.

    Automatically applies market-specific vendor defaults (e.g. when
    market='cn', switches data vendors to akshare).
    """
    global _config
    if _config is None:
        _config = default_config.DEFAULT_CONFIG.copy()
    _config.update(config)
    apply_market_defaults(_config)


def get_config() -> Dict:
    """Get the current configuration."""
    if _config is None:
        initialize_config()
    return _config.copy()


# Initialize with default config
initialize_config()
