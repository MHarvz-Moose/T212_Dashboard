from __future__ import annotations

"""
Simple detection-test scaffold.

This does not simulate a trading strategy. It asks: on which date would a given
instrument first have appeared in the top N emerging or momentum list?
"""

import pandas as pd

from .config import load_settings
from .prices import get_prices
from .signals import compute_signals, enrich_with_universe
from .universe import load_universe


def first_detection(target_yahoo_ticker: str, start: str | None = None, top_n: int = 10) -> pd.DataFrame:
    settings = load_settings()
    universe = load_universe(settings)
    prices = get_prices(universe)
    prices = prices.dropna(how="all")
    if start:
        prices = prices[prices.index >= pd.to_datetime(start)]
    rows = []
    for i in range(settings["report"].get("min_history_days", 90), len(prices)):
        window = prices.iloc[: i + 1]
        sig = enrich_with_universe(compute_signals(window, settings), universe)
        if sig.empty or target_yahoo_ticker not in sig["yahoo_ticker"].values:
            continue
        e_top = sig.sort_values("emerging_score", ascending=False).head(top_n)["yahoo_ticker"].tolist()
        m_top = sig.sort_values("momentum_score", ascending=False).head(top_n)["yahoo_ticker"].tolist()
        if target_yahoo_ticker in e_top or target_yahoo_ticker in m_top:
            row = sig[sig["yahoo_ticker"] == target_yahoo_ticker].iloc[0].to_dict()
            row["detection_date"] = prices.index[i].date().isoformat()
            row["in_top_emerging"] = target_yahoo_ticker in e_top
            row["in_top_momentum"] = target_yahoo_ticker in m_top
            rows.append(row)
            break
    return pd.DataFrame(rows)
