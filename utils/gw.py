from __future__ import annotations
from pathlib import Path
import pandas as pd


def _read(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def current_gw(data_dir: Path) -> int:
    g = _read(data_dir / "gameweeks.csv")
    if g.empty:
        return 1
    # naive: return max GW present
    return int(g["gw"].max())


def last_n_gw_range(data_dir: Path, n: int = 38):
    g = _read(data_dir / "gameweeks.csv")
    if g.empty:
        return (1, 4)
    lo = max(1, int(g["gw"].max()) - n + 1)
    hi = int(g["gw"].max())
    return (lo, hi)
