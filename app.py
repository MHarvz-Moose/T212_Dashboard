from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
OUTPUTS = REPORTS / "outputs"

st.set_page_config(page_title="Trading 212 ISA Market Radar", page_icon="📈", layout="wide")

st.title("Trading 212 ISA Market Radar")
st.caption("Daily and weekly momentum-awareness reports. Not financial advice.")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def fmt_pct_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if col.startswith(("ret_", "pct_", "drawdown")) or col == "vol_20d":
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def show_report(kind: str) -> None:
    report_path = REPORTS / f"latest_{kind}.md"
    text = read_text(report_path)
    if not text:
        st.warning(f"No latest {kind} report found yet. Run the {kind} GitHub Action, or run `python -m radar.report --kind {kind} --refresh-prices` locally.")
        return
    st.markdown(text)


def show_tables(kind: str) -> None:
    signals = fmt_pct_cols(read_csv(OUTPUTS / f"latest_{kind}_signals.csv"))
    themes = read_csv(OUTPUTS / f"latest_{kind}_themes.csv")

    if signals.empty:
        st.info("No signal output file found yet.")
        return

    st.subheader("Theme summary")
    if not themes.empty:
        st.dataframe(themes, use_container_width=True, hide_index=True)

    st.subheader("Instrument explorer")
    col1, col2, col3 = st.columns(3)
    with col1:
        theme_options = ["All"] + sorted([x for x in signals.get("theme", pd.Series(dtype=str)).dropna().unique().tolist()])
        theme = st.selectbox("Theme", theme_options)
    with col2:
        sort_col = st.selectbox(
            "Sort by",
            [c for c in ["emerging_score", "momentum_score", "ret_short", "ret_month", "ret_quarter", "ret_year", "vol_20d"] if c in signals.columns],
        )
    with col3:
        only_breakouts = st.checkbox("Only new 20/60/252d highs")

    view = signals.copy()
    if theme != "All" and "theme" in view.columns:
        view = view[view["theme"] == theme]
    if only_breakouts:
        high_cols = [c for c in ["new_20d_high", "new_60d_high", "new_252d_high"] if c in view.columns]
        if high_cols:
            view = view[view[high_cols].fillna(False).any(axis=1)]
    view = view.sort_values(sort_col, ascending=False)

    preferred_cols = [
        "name", "theme", "asset_class", "yahoo_ticker", "ret_short", "ret_month", "ret_quarter", "ret_year",
        "emerging_score", "momentum_score", "rank_jump", "new_20d_high", "new_60d_high", "new_252d_high",
        "pct_above_ma_50", "vol_20d", "overextended",
    ]
    cols = [c for c in preferred_cols if c in view.columns]
    st.dataframe(view[cols], use_container_width=True, hide_index=True)


with st.sidebar:
    st.header("Navigation")
    page = st.radio("Page", ["Daily report", "Weekly report", "Explorer"], index=0)
    st.divider()
    st.markdown("**How it updates**")
    st.markdown("GitHub Actions generates saved reports. Streamlit displays the latest files from the repo.")

if page == "Daily report":
    show_report("daily")
elif page == "Weekly report":
    show_report("weekly")
else:
    kind = st.radio("Data set", ["daily", "weekly"], horizontal=True)
    show_tables(kind)
