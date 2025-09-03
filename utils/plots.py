import altair as alt
import pandas as pd

def hbar_sorted(series: pd.Series, title: str, x_title: str, fmt: str | None = None,
                scheme: str = "plasma", reverse: bool = True, show_legend: bool = False):
    data = series.reset_index()
    data.columns = ["club", "value"]
    height = max(320, 32 * len(data))
    return (
        alt.Chart(data)
        .mark_bar()
        .encode(
            y=alt.Y(
                "club:N",
                sort="-x",
                title="",
                axis=alt.Axis(labelOverlap=False, labelLimit=300),
            ),
            x=alt.X(
                "value:Q",
                title=x_title,
                axis=alt.Axis(format=fmt) if fmt else alt.Axis()
            ),
            color=alt.Color(
                "value:Q",
                title=x_title if show_legend else None,
                scale=alt.Scale(scheme=scheme, reverse=reverse),
                legend=alt.Legend() if show_legend else None
            ),
            tooltip=[
                alt.Tooltip("club:N", title="Club"),
                alt.Tooltip("value:Q", title=x_title, format=fmt) if fmt
                else alt.Tooltip("value:Q", title=x_title),
            ],
        )
        .properties(title=title, width="container", height=height)
    )
