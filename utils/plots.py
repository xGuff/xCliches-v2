from __future__ import annotations
import pandas as pd
import plotly.express as px


# Expect columns in aggregates_manager_gw.csv
# manager_id, club_id, gw, pressers, cliche_count_total, words_total, cliches_per_10k


def leaderboard_bar(frag, min_pressers: int = 2, gw_range=(1, 38)):
    df = frag.aggregates_manager_gw.copy()
    if df.empty:
        return px.bar(title="No data")
    lo, hi = gw_range
    df = df[(df.gw >= lo) & (df.gw <= hi)]
    agg = (
        df.groupby(["manager_id", "club_id"], as_index=False)
        .agg({"pressers": "sum", "cliche_count_total": "sum", "words_total": "sum"})
    )
    agg = agg[agg["pressers"] >= min_pressers]
    if agg.empty:
        return px.bar(title="No managers meet the min pressers filter")
    agg["cliches_per_10k"] = 10000 * agg["cliche_count_total"] / agg["words_total"].clip(lower=1)
    fig = px.bar(
        agg.sort_values("cliches_per_10k", ascending=False),
        x="manager_id", y="cliches_per_10k", color="club_id",
        title="Clichés per 10k words (season to date)",
        labels={"manager_id": "Manager", "cliches_per_10k": "Per 10k words", "club_id": "Club"},
    )
    fig.update_layout(margin=dict(l=10, r=10, t=60, b=10))
    return fig


def trend_lines(frag, rolling4: bool = True, gw_range=(1, 38)):
    df = frag.aggregates_manager_gw.copy()
    if df.empty:
        return px.line(title="No data")
    lo, hi = gw_range
    df = df[(df.gw >= lo) & (df.gw <= hi)]
    df = df.sort_values(["manager_id", "gw"]).copy()
    if rolling4:
        df["cliches_per_10k_r4"] = (
            df.groupby("manager_id")["cliches_per_10k"]
            .rolling(4, min_periods=1)
            .mean()
            .reset_index(level=0, drop=True)
        )
        y = "cliches_per_10k_r4"
        title = "Rolling 4‑GW cliché rate"
    else:
        y = "cliches_per_10k"
        title = "Cliché rate by GW"
    fig = px.line(
        df, x="gw", y=y, color="manager_id", markers=True, title=title,
        labels={"gw": "Gameweek", y: "Per 10k words", "manager_id": "Manager"}
    )
    fig.update_layout(margin=dict(l=10, r=10, t=60, b=10))
    return fig