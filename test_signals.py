import pandas as pd
import numpy as np

from radar.signals import compute_signals


def test_compute_signals_basic():
    idx = pd.date_range("2024-01-01", periods=260, freq="B")
    prices = pd.DataFrame({"AAA.L": np.linspace(100, 150, len(idx)), "BBB.L": np.linspace(100, 90, len(idx))}, index=idx)
    settings = {
        "report": {"min_history_days": 90},
        "signals": {
            "lookbacks": {"short_days": 5, "month_days": 21, "quarter_days": 63, "year_days": 252},
            "high_windows": [20, 60, 252],
            "moving_averages": [20, 50, 200],
            "overextended_pct_above_50dma": 20,
        },
    }
    sig = compute_signals(prices, settings)
    assert not sig.empty
    assert "momentum_score" in sig.columns
    assert "emerging_score" in sig.columns
