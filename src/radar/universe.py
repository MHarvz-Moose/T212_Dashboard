from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

from .config import ROOT, load_settings


def load_seed_universe() -> pd.DataFrame:
    path = ROOT / "data" / "universe_seed.csv"
    return pd.read_csv(path)


def load_trading212_universe() -> pd.DataFrame:
    raw_path = ROOT / "data" / "trading212_instruments_raw.csv"
    if not raw_path.exists():
        raise FileNotFoundError("Run `python -m radar.trading212` first to fetch Trading 212 instruments.")
    df = pd.read_csv(raw_path)
    # Trading 212 field names may evolve. This normalises common columns when present.
    cols = {c.lower(): c for c in df.columns}
    ticker_col = cols.get("ticker") or cols.get("shortname") or df.columns[0]
    name_col = cols.get("name") or cols.get("fullname") or ticker_col
    currency_col = cols.get("currencycode") or cols.get("currency")
    exchange_col = cols.get("exchangeid") or cols.get("exchange")
    out = pd.DataFrame({
        "ticker": df[ticker_col],
        "name": df[name_col],
        "exchange": df[exchange_col] if exchange_col else "",
        "currency": df[currency_col] if currency_col else "",
        "asset_class": "Unknown",
        "theme": "Unclassified",
        "yahoo_ticker": "",
        "include": 0,
    })
    out_path = ROOT / "data" / "universe_from_trading212_needs_mapping.csv"
    out.to_csv(out_path, index=False)
    return out


def apply_filters(df: pd.DataFrame, settings: dict) -> pd.DataFrame:
    df = df.copy()
    df = df[df.get("include", 1).astype(int) == 1]
    keywords = settings.get("filters", {}).get("exclude_keywords", [])
    if keywords:
        pat = "|".join(re.escape(k) for k in keywords)
        mask = ~df["name"].fillna("").str.contains(pat, case=False, regex=True)
        df = df[mask]
    df = df[df["yahoo_ticker"].fillna("").astype(str).str.len() > 0]
    return df.reset_index(drop=True)


def load_universe(settings: dict | None = None) -> pd.DataFrame:
    settings = settings or load_settings()
    source = settings.get("data", {}).get("universe_source", "seed")
    if source == "trading212":
        df = load_trading212_universe()
    else:
        df = load_seed_universe()
    return apply_filters(df, settings)
