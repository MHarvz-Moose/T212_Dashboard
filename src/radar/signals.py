from __future__ import annotations

import numpy as np
import pandas as pd


def _rank_pct(series: pd.Series) -> pd.Series:
    return series.rank(pct=True, ascending=True)


def compute_signals(prices: pd.DataFrame, settings: dict) -> pd.DataFrame:
    close = prices.sort_index().copy()
    latest = close.iloc[-1]
    lookbacks = settings["signals"]["lookbacks"]
    rows: list[pd.Series] = []
    for ticker in close.columns:
        s = close[ticker].dropna()
        if len(s) < settings["report"].get("min_history_days", 90):
            continue
        row = {"yahoo_ticker": ticker, "last_price": s.iloc[-1], "last_date": s.index[-1].date().isoformat()}
        for name, days in lookbacks.items():
            key = name.replace("_days", "")
            row[f"ret_{key}"] = s.iloc[-1] / s.iloc[-days - 1] - 1 if len(s) > days else np.nan
        returns = s.pct_change().dropna()
        row["vol_20d"] = returns.tail(20).std() * np.sqrt(252) if len(returns) >= 20 else np.nan
        for ma in settings["signals"]["moving_averages"]:
            if len(s) >= ma:
                ma_val = s.rolling(ma).mean().iloc[-1]
                row[f"ma_{ma}"] = ma_val
                row[f"pct_above_ma_{ma}"] = s.iloc[-1] / ma_val - 1
                row[f"above_ma_{ma}"] = bool(s.iloc[-1] > ma_val)
        for window in settings["signals"]["high_windows"]:
            if len(s) >= window:
                rolling_high = s.tail(window).max()
                prev_high = s.iloc[:-1].tail(window).max() if len(s) > window else rolling_high
                row[f"near_{window}d_high"] = s.iloc[-1] >= rolling_high * 0.995
                row[f"new_{window}d_high"] = s.iloc[-1] >= prev_high
                row[f"drawdown_from_{window}d_high"] = s.iloc[-1] / rolling_high - 1
        # Rank improvement proxy: compare latest 21d return with 21d return ten trading days ago.
        if len(s) >= 35:
            row["ret_month_10d_ago"] = s.iloc[-11] / s.iloc[-32] - 1
        rows.append(pd.Series(row))
    sig = pd.DataFrame(rows)
    if sig.empty:
        return sig

    sig["rank_ret_short"] = _rank_pct(sig["ret_short"])
    sig["rank_ret_month"] = _rank_pct(sig["ret_month"])
    sig["rank_ret_quarter"] = _rank_pct(sig["ret_quarter"])
    sig["rank_ret_year"] = _rank_pct(sig.get("ret_year", pd.Series(index=sig.index, dtype=float)))
    sig["rank_vol_20d"] = _rank_pct(sig["vol_20d"])
    sig["rank_month_10d_ago"] = _rank_pct(sig["ret_month_10d_ago"])

    sig["momentum_score"] = (
        0.20 * sig["rank_ret_short"].fillna(0)
        + 0.40 * sig["rank_ret_month"].fillna(0)
        + 0.30 * sig["rank_ret_quarter"].fillna(0)
        + 0.10 * sig["rank_ret_year"].fillna(0)
        - 0.10 * sig["rank_vol_20d"].fillna(0.5)
    )
    sig["rank_jump"] = sig["rank_ret_month"] - sig["rank_month_10d_ago"]
    bonus_cols = [c for c in sig.columns if c.startswith("new_") and c.endswith("d_high")]
    sig["breakout_bonus"] = sig[bonus_cols].sum(axis=1) / max(len(bonus_cols), 1)
    sig["trend_bonus"] = sig[[c for c in sig.columns if c.startswith("above_ma_")]].sum(axis=1) / 3
    sig["emerging_score"] = (
        0.45 * sig["rank_jump"].fillna(0)
        + 0.30 * sig["rank_ret_short"].fillna(0)
        + 0.15 * sig["breakout_bonus"].fillna(0)
        + 0.10 * sig["trend_bonus"].fillna(0)
    )
    sig["overextended"] = sig.get("pct_above_ma_50", 0) > settings["signals"].get("overextended_pct_above_50dma", 20) / 100
    return sig.sort_values("emerging_score", ascending=False).reset_index(drop=True)


def enrich_with_universe(signals: pd.DataFrame, universe: pd.DataFrame) -> pd.DataFrame:
    return signals.merge(universe, on="yahoo_ticker", how="left")


def theme_summary(enriched: pd.DataFrame) -> pd.DataFrame:
    if enriched.empty:
        return pd.DataFrame()
    g = enriched.groupby("theme", dropna=False).agg(
        instruments=("yahoo_ticker", "count"),
        avg_momentum=("momentum_score", "mean"),
        avg_emerging=("emerging_score", "mean"),
        top_1m_return=("ret_month", "max"),
        new_60d_highs=("new_60d_high", "sum"),
    )
    return g.sort_values(["avg_emerging", "avg_momentum"], ascending=False).reset_index()
