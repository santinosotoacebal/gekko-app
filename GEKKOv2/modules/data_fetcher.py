"""
data_fetcher.py
---------------
Thin wrapper around yfinance.  All network calls live here.
"""
import requests
from io import StringIO

import pandas as pd
import yfinance as yf

_WIKI_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

TECH_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "AMD",  "NFLX", "ADBE",
    "CRM",  "ORCL", "INTC", "QCOM", "AVGO",
    "TXN",  "MU",   "LRCX", "KLAC", "AMAT",
]

# Base reference prices (used as fallback / for simulated radar mode)
BASE_PRICES: dict[str, float] = {
    "AAPL": 182.0, "MSFT": 375.0, "GOOGL": 172.0, "AMZN": 178.0,
    "NVDA": 485.0, "META": 502.0, "TSLA": 248.0,  "AMD":  168.0,
    "NFLX": 612.0, "ADBE": 502.0, "CRM":  285.0,  "ORCL": 118.0,
    "INTC":  44.0, "QCOM": 168.0, "AVGO": 1285.0,
    "TXN":  168.0, "MU":    92.0, "LRCX": 918.0,
    "KLAC": 765.0, "AMAT": 212.0,
}


def get_stock_data(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """Return OHLCV DataFrame for *ticker*.  Returns empty DF on failure."""
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval)
        df.index = df.index.tz_localize(None)   # strip timezone for Plotly
        return df
    except Exception:
        return pd.DataFrame()


def get_stock_info(ticker: str) -> dict:
    """
    Return company name, current price and daily delta.
    Returns an empty dict if the ticker is invalid or data unavailable.
    """
    try:
        t    = yf.Ticker(ticker)
        hist = t.history(period="2d")

        if hist.empty:
            return {}

        price = round(float(hist["Close"].iloc[-1]), 2)
        prev  = round(float(hist["Close"].iloc[-2]), 2) if len(hist) >= 2 else price
        delta = round((price - prev) / prev * 100, 2) if prev else 0.0

        # longName can be slow; wrap it so a failure doesn't kill the whole call
        try:
            info = t.info
            name = info.get("longName") or info.get("shortName") or ticker.upper()
        except Exception:
            name = ticker.upper()

        return {"name": name, "price": price, "prev": prev, "delta": delta}
    except Exception:
        return {}


def get_current_price(ticker: str) -> dict:
    """Return current price dict (price, change %, volume)."""
    try:
        hist = yf.Ticker(ticker).history(period="2d")
        if len(hist) >= 2:
            price     = float(hist["Close"].iloc[-1])
            prev      = float(hist["Close"].iloc[-2])
            chg_pct   = (price - prev) / prev * 100
            volume    = int(hist["Volume"].iloc[-1])
        else:
            price, chg_pct, volume = BASE_PRICES.get(ticker, 100.0), 0.0, 0
        return {"ticker": ticker, "price": round(price, 2),
                "change_pct": round(chg_pct, 2), "volume": volume}
    except Exception:
        return {"ticker": ticker, "price": BASE_PRICES.get(ticker, 100.0),
                "change_pct": 0.0, "volume": 0}


def _fetch_sp500_table() -> pd.DataFrame:
    """
    Fetch the S&P 500 Wikipedia table using a browser User-Agent to avoid 403.
    Returns the first table as a DataFrame, raises on failure.
    """
    resp = requests.get(
        "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        headers=_WIKI_HEADERS,
        timeout=20,
    )
    resp.raise_for_status()
    return pd.read_html(StringIO(resp.text))[0]


def get_sp500_tickers() -> list:
    """
    Fetch current S&P 500 tickers from Wikipedia.
    Dots replaced with hyphens (e.g. BRK.B -> BRK-B) for yfinance.
    Falls back to TECH_TICKERS on failure.
    """
    try:
        df = _fetch_sp500_table()
        return [str(s).replace(".", "-") for s in df["Symbol"].tolist()]
    except Exception:
        return TECH_TICKERS


def get_sp500_universe():
    """
    Returns (tickers: list, sectors: dict) from the Wikipedia S&P 500 table.
    sectors maps ticker -> GICS Sector string.
    Falls back to (TECH_TICKERS, {}) on any failure.
    """
    try:
        df      = _fetch_sp500_table()
        tickers = [str(s).replace(".", "-") for s in df["Symbol"].tolist()]
        sectors = dict(zip(
            tickers,
            df["GICS Sector"].fillna("").astype(str).tolist(),
        ))
        return tickers, sectors
    except Exception:
        return TECH_TICKERS, {}


def bulk_download(tickers: list, period: str = "6mo") -> pd.DataFrame:
    """
    Download OHLCV data for multiple tickers in one batched request.
    Returns a MultiIndex DataFrame grouped by ticker, or empty DataFrame on failure.
    """
    try:
        return yf.download(
            tickers, period=period,
            progress=False, group_by="ticker",
        )
    except Exception:
        return pd.DataFrame()
