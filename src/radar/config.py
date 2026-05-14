from __future__ import annotations

from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_settings(path: str | Path | None = None) -> dict:
    settings_path = Path(path) if path else ROOT / "config" / "settings.yaml"
    with settings_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)
