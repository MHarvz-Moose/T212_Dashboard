from __future__ import annotations

import base64
import os
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()


def _base_url() -> str:
    env = os.getenv("TRADING212_ENV", "live").strip().lower()
    if env == "demo":
        return "https://demo.trading212.com/api/v0"
    return "https://live.trading212.com/api/v0"


def _headers() -> dict[str, str]:
    key = os.getenv("TRADING212_API_KEY", "")
    secret = os.getenv("TRADING212_API_SECRET", "")
    if not key or not secret:
        raise RuntimeError("Missing TRADING212_API_KEY or TRADING212_API_SECRET. Copy .env.example to .env and fill them in.")
    token = base64.b64encode(f"{key}:{secret}".encode("utf-8")).decode("utf-8")
    return {"Authorization": f"Basic {token}"}


def fetch_instruments() -> list[dict[str, Any]]:
    url = f"{_base_url()}/equity/metadata/instruments"
    r = requests.get(url, headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def save_instruments_csv(output_path: str = "data/trading212_instruments_raw.csv") -> pd.DataFrame:
    instruments = fetch_instruments()
    df = pd.json_normalize(instruments)
    df.to_csv(output_path, index=False)
    return df


if __name__ == "__main__":
    df = save_instruments_csv()
    print(f"Saved {len(df):,} instruments to data/trading212_instruments_raw.csv")
