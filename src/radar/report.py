from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil

import pandas as pd

from .config import ROOT, load_settings
from .prices import get_prices
from .signals import compute_signals, enrich_with_universe, theme_summary
from .universe import load_universe


def pct(x: float) -> str:
    if pd.isna(x):
        return ""
    return f"{x*100:,.1f}%"


def _table(df: pd.DataFrame, cols: list[str], n: int) -> str:
    if df.empty:
        return "No rows available."
    out = df.head(n).copy()
    for c in out.columns:
        if c.startswith("ret_") or c.startswith("pct_") or c.startswith("drawdown") or c == "vol_20d":
            out[c] = out[c].map(pct)
        elif c.endswith("score") or c.startswith("rank") or c.startswith("avg_"):
            out[c] = out[c].map(lambda v: f"{v:,.2f}" if pd.notna(v) else "")
    existing = [c for c in cols if c in out.columns]
    return out[existing].to_markdown(index=False)


def _narrative(themes: pd.DataFrame, emerging: pd.DataFrame) -> str:
    parts = []
    if not themes.empty:
        top_theme = themes.iloc[0]
        parts.append(
            f"The strongest emerging cluster is **{top_theme['theme']}**, with "
            f"{int(top_theme['instruments'])} tracked instrument(s) and an average emerging score of "
            f"{top_theme['avg_emerging']:.2f}."
        )
    if not emerging.empty:
        top = emerging.iloc[0]
        parts.append(
            f"The highest single-instrument emerging signal is **{top.get('name', top['yahoo_ticker'])}** "
            f"({top['yahoo_ticker']}), with a 1-month return of {pct(top.get('ret_month'))}."
        )
    if not parts:
        return "No sufficient price history was available to generate signals."
    return " ".join(parts)


def _write_outputs(enriched: pd.DataFrame, themes: pd.DataFrame, kind: str) -> None:
    """Write machine-readable outputs for the Streamlit app."""
    out_dir = ROOT / "reports" / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(out_dir / f"latest_{kind}_signals.csv", index=False)
    themes.to_csv(out_dir / f"latest_{kind}_themes.csv", index=False)


def build_report(kind: str = "daily", refresh_prices: bool = False) -> Path:
    if kind not in {"daily", "weekly"}:
        raise ValueError("kind must be 'daily' or 'weekly'")

    settings = load_settings()
    universe = load_universe(settings)
    prices = get_prices(universe, refresh=refresh_prices)
    sig = compute_signals(prices, settings)
    enriched = enrich_with_universe(sig, universe)
    themes = theme_summary(enriched)

    base_output_dir = ROOT / settings["report"].get("output_dir", "reports")
    output_dir = base_output_dir / kind
    output_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    n = settings["report"].get("daily_top_n" if kind == "daily" else "weekly_top_n", 15)

    title = settings["report"].get("title", "Market Radar")
    lines = [f"# {title} — {kind.title()} Report", "", f"Generated: {today}", ""]
    lines += ["## Executive summary", "", _narrative(themes, enriched.sort_values("emerging_score", ascending=False)), ""]

    lines += ["## Top emerging themes", ""]
    if themes.empty:
        lines += ["No theme data available.", ""]
    else:
        theme_cols = ["theme", "instruments", "avg_emerging", "avg_momentum", "top_1m_return", "new_60d_highs"]
        lines += [_table(themes, theme_cols, min(10, n)), ""]

    lines += ["## Waking up: highest emerging scores", ""]
    emerging_cols = ["name", "theme", "yahoo_ticker", "ret_short", "ret_month", "rank_jump", "emerging_score", "new_20d_high", "new_60d_high", "overextended"]
    lines += [_table(enriched.sort_values("emerging_score", ascending=False), emerging_cols, n), ""]

    lines += ["## Strongest momentum instruments", ""]
    momentum_cols = ["name", "theme", "yahoo_ticker", "ret_short", "ret_month", "ret_quarter", "ret_year", "momentum_score", "vol_20d"]
    lines += [_table(enriched.sort_values("momentum_score", ascending=False), momentum_cols, n), ""]

    lines += ["## New highs", ""]
    high_mask = pd.Series(False, index=enriched.index)
    for c in ["new_20d_high", "new_60d_high", "new_252d_high"]:
        if c in enriched.columns:
            high_mask = high_mask | enriched[c].fillna(False)
    highs = enriched[high_mask].sort_values("momentum_score", ascending=False) if not enriched.empty else enriched
    high_cols = ["name", "theme", "yahoo_ticker", "ret_month", "new_20d_high", "new_60d_high", "new_252d_high", "pct_above_ma_50"]
    lines += [_table(highs, high_cols, n), ""]

    if kind == "weekly":
        lines += ["## Weekly notes", ""]
        lines += [
            "Use this section to add manual observations after reading the automated tables. Suggested checks:",
            "",
            "- Are the top instruments part of a broad theme or isolated moves?",
            "- Are moves early-stage, mature, or overextended?",
            "- Are commodity, sector, country, and bond signals agreeing or conflicting?",
            "- Which themes deserve deeper research next week?",
            "",
        ]

    lines += [
        "## Important caveat",
        "",
        "This report is an awareness tool, not financial advice or a buy/sell recommendation. Check instrument eligibility, liquidity, spreads, tax treatment, and your own risk tolerance before acting.",
        "",
    ]

    path = output_dir / f"{today}_{kind}_market_radar.md"
    path.write_text("\n".join(lines), encoding="utf-8")

    latest_path = base_output_dir / f"latest_{kind}.md"
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, latest_path)
    _write_outputs(enriched, themes, kind)
    return path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=["daily", "weekly"], default="daily")
    parser.add_argument("--refresh-prices", action="store_true")
    args = parser.parse_args()
    output = build_report(kind=args.kind, refresh_prices=args.refresh_prices)
    print(f"Wrote {output}")
