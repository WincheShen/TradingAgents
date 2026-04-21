import unittest

from cli.utils import normalize_ticker_symbol
from tradingagents.agents.utils.agent_utils import build_instrument_context
from tradingagents.dataflows.cn_stock.utils import (
    is_cn_ticker,
    to_akshare_code,
    to_em_code,
    detect_exchange_suffix,
    normalize_cn_ticker,
)


class TickerSymbolHandlingTests(unittest.TestCase):
    def test_normalize_ticker_symbol_preserves_exchange_suffix(self):
        self.assertEqual(normalize_ticker_symbol(" cnc.to "), "CNC.TO")

    def test_build_instrument_context_mentions_exact_symbol(self):
        context = build_instrument_context("7203.T")
        self.assertIn("7203.T", context)
        self.assertIn("exchange suffix", context)

    # --- Chinese A-share ticker tests ---

    def test_normalize_auto_detects_shanghai(self):
        """Bare 6-digit Shanghai code gets .SS suffix."""
        self.assertEqual(normalize_ticker_symbol("600519"), "600519.SS")
        self.assertEqual(normalize_ticker_symbol("601318"), "601318.SS")
        self.assertEqual(normalize_ticker_symbol("688981"), "688981.SS")

    def test_normalize_auto_detects_shenzhen(self):
        """Bare 6-digit Shenzhen code gets .SZ suffix."""
        self.assertEqual(normalize_ticker_symbol("000858"), "000858.SZ")
        self.assertEqual(normalize_ticker_symbol("300750"), "300750.SZ")
        self.assertEqual(normalize_ticker_symbol("002594"), "002594.SZ")

    def test_normalize_preserves_existing_cn_suffix(self):
        """Already-suffixed Chinese tickers pass through unchanged."""
        self.assertEqual(normalize_ticker_symbol("600519.ss"), "600519.SS")
        self.assertEqual(normalize_ticker_symbol(" 000858.SZ "), "000858.SZ")

    def test_normalize_non_cn_codes_untouched(self):
        """Non-Chinese tickers are not modified."""
        self.assertEqual(normalize_ticker_symbol("AAPL"), "AAPL")
        self.assertEqual(normalize_ticker_symbol("0700.HK"), "0700.HK")
        self.assertEqual(normalize_ticker_symbol("SPY"), "SPY")

    def test_is_cn_ticker(self):
        self.assertTrue(is_cn_ticker("600519.SS"))
        self.assertTrue(is_cn_ticker("000858.SZ"))
        self.assertTrue(is_cn_ticker("SH600519"))
        self.assertTrue(is_cn_ticker("600519"))
        self.assertFalse(is_cn_ticker("AAPL"))
        self.assertFalse(is_cn_ticker("0700.HK"))
        self.assertFalse(is_cn_ticker("SPY"))

    def test_to_akshare_code(self):
        self.assertEqual(to_akshare_code("600519.SS"), "600519")
        self.assertEqual(to_akshare_code("000858.SZ"), "000858")
        self.assertEqual(to_akshare_code("SH600519"), "600519")
        self.assertEqual(to_akshare_code("600519"), "600519")

    def test_to_em_code(self):
        self.assertEqual(to_em_code("600519.SS"), "SH600519")
        self.assertEqual(to_em_code("000858.SZ"), "SZ000858")
        self.assertEqual(to_em_code("600519"), "SH600519")

    def test_detect_exchange_suffix(self):
        self.assertEqual(detect_exchange_suffix("600519"), ".SS")
        self.assertEqual(detect_exchange_suffix("000858"), ".SZ")
        self.assertEqual(detect_exchange_suffix("300750"), ".SZ")
        self.assertEqual(detect_exchange_suffix("688981"), ".SS")
        self.assertEqual(detect_exchange_suffix("AAPL"), "")

    def test_normalize_cn_ticker(self):
        self.assertEqual(normalize_cn_ticker("600519"), "600519.SS")
        self.assertEqual(normalize_cn_ticker("sh600519"), "600519.SS")
        self.assertEqual(normalize_cn_ticker("600519.SS"), "600519.SS")

    def test_build_instrument_context_includes_cn_suffixes(self):
        context = build_instrument_context("600519.SS")
        self.assertIn("600519.SS", context)
        self.assertIn(".SS", context)
        self.assertIn(".SZ", context)


if __name__ == "__main__":
    unittest.main()
