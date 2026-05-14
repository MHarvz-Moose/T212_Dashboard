from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

from .config import ROOT

CACHE_DIR = ROOT / "data" / "price_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def fetch_prices_yfinance(tickers: list[str], period: str = "2y") -> pd.DataFrame:
    """Return adjusted close prices indexed by date."""
    if not tickers:
        return pd.DataFrame()
    data = yf.download(
        tickers=tickers,
        period=period,
        auto_adjust=True,
        progress=False,
        group_by="column",
        threads=True,
    )
    if data.empty:
        return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        if "Close" in data.columns.get_level_values(0):
            close = data["Close"]
        elif "Adj Close" in data.columns.get_level_values(0):
            close = data["Adj Close"]
        else:
            raise ValueError("Could not find Close or Adj Close columns in yfinance output.")
    else:
        close = data[["Close"]].rename(columns={"Close": tickers[0]})
    close.index = pd.to_datetime(close.index).tz_localize(None)
    return close.dropna(how="all")


def get_prices(universe: pd.DataFrame, refresh: bool = False, period: str = "2y") -> pd.DataFrame:
    tickers = sorted(universe["yahoo_ticker"].dropna().unique().tolist())
    cache_path = CACHE_DIR / "prices_yfinance.csv"
    if cache_path.exists() and not refresh:
        prices = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        missing = [t for t in tickers if t not in prices.columns]
        if not missing:
            return prices[tickers]
    prices = fetch_prices_yfinance(tickers, period=period)
    prices.to_csv(cache_path)
    return prices
