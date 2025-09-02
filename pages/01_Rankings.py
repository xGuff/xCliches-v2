import streamlit as st
import pandas as pd
import altair as alt
from utils.sidebar import sidebar_filters

st.title("Expected Clichés Rankings")

# Load data
transcripts_df = pd.read_csv("data/raw/transcripts.csv")
cliches_df = pd.read_csv("data/processed/cliche_hits.csv")

# Sidebar filters
season, league, club, start_date, end_date = sidebar_filters(transcripts_df)

# Filter by dates/club
cliches_df['publish_date'] = pd.to_datetime(cliches_df['publish_date'])
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)
cliches_df = cliches_df[(cliches_df['publish_date'] >= start_date) &
                        (cliches_df['publish_date'] <= end_date)]
if club != "All Clubs":
    cliches_df = cliches_df[cliches_df['club'] == club]
    transcripts_df = transcripts_df[transcripts_df['club'] == club]

# Aggregates
word_counts = transcripts_df.groupby('club')['transcript_cleaned'] \
    .apply(lambda texts: sum(len(str(t).split()) for t in texts)).astype(int)

cliche_counts = cliches_df.groupby('club').size().reindex(word_counts.index, fill_value=0)

rankings = pd.DataFrame({
    'Total Words': word_counts,
    'Total Clichés': cliche_counts,
})
rankings['Clichés per 10,000 Words'] = (
    cliche_counts.div(word_counts.replace(0, pd.NA)) * 10000
).fillna(0)

# ---------- Altair helper for horizontal, sorted, colored bars ----------
def hbar_sorted(series: pd.Series, title: str, x_title: str, fmt: str | None = None,
                scheme: str = "plasma", reverse: bool = True, show_legend: bool = False):
    data = series.reset_index()
    data.columns = ["club", "value"]

    # Enough height so every label can be drawn; prevents Altair from dropping some labels
    height = max(320, 32 * len(data))

    return (
        alt.Chart(data)
        .mark_bar()
        .encode(
            y=alt.Y(
                "club:N",
                sort="-x",                 # sort by bar length descending
                title="",
                axis=alt.Axis(
                    labelOverlap=False,   # don't drop labels
                    labelLimit=300        # avoid '...' truncation of long names
                ),
            ),
            x=alt.X(
                "value:Q",
                title=x_title,
                axis=alt.Axis(format=fmt) if fmt else alt.Axis()
            ),
            color=alt.Color(
                "value:Q",
                title=x_title if show_legend else None,
                scale=alt.Scale(scheme=scheme, reverse=reverse),  # plasma_r
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

# ---------- Charts ----------
st.subheader("Clichés per 10,000 Words")
st.altair_chart(
    hbar_sorted(
        rankings['Clichés per 10,000 Words'],
        title="",
        x_title="Clichés per 10,000 Words",
        fmt=".1f",
        scheme="plasma",   # base scheme
        reverse=True       # reversed -> plasma_r
    ),
    use_container_width=True
)

st.subheader("Total Words")
st.altair_chart(
    hbar_sorted(
        rankings['Total Words'],
        title="",
        x_title="Total Words",
        fmt=",.0f",
        scheme="plasma",
        reverse=True
    ),
    use_container_width=True
)

st.subheader("Full Rankings Table")
rankings_sorted = rankings.sort_values('Clichés per 10,000 Words', ascending=False).reset_index()
rankings_sorted.rename(columns={'club': 'Club'}, inplace=True)
rankings_sorted.insert(0, "Rank", rankings_sorted.index + 1)
st.dataframe(rankings_sorted, hide_index=True, height=len(rankings_sorted) * 35 + 40)
