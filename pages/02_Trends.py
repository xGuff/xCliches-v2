import streamlit as st
import pandas as pd
import altair as alt
from utils.sidebar import sidebar_filters
import math

st.title("Cliché trends over time")

# -------------------- Data loaders --------------------
@st.cache_data
def load_core():
    transcripts_df = pd.read_csv("data/raw/transcripts.csv")
    cliches_df     = pd.read_csv("data/processed/cliche_hits.csv")
    managers_df    = pd.read_csv("data/raw/managers.csv")  # optional for other pages
    # standardise columns
    for df in (transcripts_df, cliches_df, managers_df):
        df.columns = [c.strip().lower() for c in df.columns]
    return transcripts_df, cliches_df, managers_df

@st.cache_data
def load_club_colours():
    df = pd.read_csv("data/raw/club_colours.csv")
    df.columns = [c.strip().lower() for c in df.columns]

    club_col = next((c for c in df.columns if "club" in c), df.columns[0])
    color_col_candidates = [c for c in df.columns if any(k in c for k in ["colour", "color", "hex"])]
    color_col = color_col_candidates[0] if color_col_candidates else df.columns[-1]

    # ensure leading '#'
    df[color_col] = df[color_col].astype(str).str.strip()
    df[color_col] = df[color_col].str.replace(r"^((?!#).+)$", r"#\1", regex=True)

    return {row[club_col]: row[color_col] for _, row in df.iterrows() if pd.notna(row[color_col])}

transcripts_df, cliches_df, managers_df = load_core()
club_color_map = load_club_colours()

# -------------------- Sidebar filters --------------------
season, league, club, start_date, end_date = sidebar_filters(transcripts_df)

# -------------------- Date handling + filter --------------------
transcripts_df["publish_date"] = pd.to_datetime(transcripts_df["publish_date"])
cliches_df["publish_date"]     = pd.to_datetime(cliches_df["publish_date"])

start_date = pd.to_datetime(start_date)
end_date   = pd.to_datetime(end_date)

t_mask = (transcripts_df["publish_date"] >= start_date) & (transcripts_df["publish_date"] <= end_date)
c_mask = (cliches_df["publish_date"] >= start_date) & (cliches_df["publish_date"] <= end_date)
if club != "All Clubs":
    t_mask &= (transcripts_df["club"] == club)
    c_mask &= (cliches_df["club"] == club)

t = transcripts_df.loc[t_mask].copy()
c = cliches_df.loc[c_mask].copy()

# -------------------- Per-day aggregates (then cumulative) --------------------
# Words per (club, date)
t["words"] = t["transcript_cleaned"].astype(str).apply(lambda s: len(s.split()))
words_per_day = (
    t.groupby(["club", "publish_date"], as_index=False)["words"]
     .sum()
     .rename(columns={"words": "total_words"})
)

# Cliché hits per (club, date)
hits_per_day = (
    c.groupby(["club", "publish_date"], as_index=False)
     .size()
     .rename(columns={"size": "total_cliches"})
)

# Predominant manager per date (for change detection)
def predominant_manager(series: pd.Series):
    if series.empty:
        return None
    m = series.mode()
    return (m.sort_values().iloc[0] if not m.empty else series.iloc[0])

mgr_per_day = (
    t.groupby(["club", "publish_date"], as_index=False)["manager"]
     .agg(predominant_manager)
     .rename(columns={"manager": "manager_name"})
)

# Merge daily + sort
ts = (
    words_per_day
    .merge(hits_per_day, on=["club", "publish_date"], how="left")
    .merge(mgr_per_day,  on=["club", "publish_date"], how="left")
    .sort_values(["club", "publish_date"])
)

ts["total_cliches"] = ts["total_cliches"].fillna(0).astype(int)

# Cumulative sums within each club
ts["cum_words"]   = ts.groupby("club")["total_words"].cumsum()
ts["cum_cliches"] = ts.groupby("club")["total_cliches"].cumsum()

# Cumulative rate per 10k words
ts["cliches_per_10k"] = ts.apply(
    lambda r: (r["cum_cliches"] / r["cum_words"] * 10000) if r["cum_words"] > 0 else 0,
    axis=1
)

# -------------------- Manager-change flags & labels --------------------
ts["prev_manager"] = ts.groupby("club")["manager_name"].shift()
ts["is_manager_change"] = (
    ts["manager_name"].notna()
    & ts["prev_manager"].notna()
    & (ts["manager_name"] != ts["prev_manager"])
)
ts["change_label"] = ts.apply(
    lambda r: f"{r['prev_manager']} → {r['manager_name']}" if r["is_manager_change"] else "",
    axis=1
)

# -------------------- Shared domains --------------------
# Shared Y-domain for all plots
y_max = float(ts["cliches_per_10k"].max() if len(ts) else 0.0)
y_domain = [0, max(2, math.ceil(y_max / 2) * 2)]  # step to nearest 2 (tweak as desired)

# Shared X-limits: compute once and force each facet to use them,
# while keeping x-axes visible on every subplot by using "independent" scales.
x_min = pd.to_datetime(ts["publish_date"].min()) if len(ts) else start_date
x_max = pd.to_datetime(ts["publish_date"].max()) if len(ts) else end_date
x_domain = [x_min, x_max]

# Padding for rule to stop below label (3% of y-range)
top_pad = (y_domain[1] - y_domain[0]) * 0.03

# -------------------- Chart --------------------
clubs_in_view = sorted(ts["club"].dropna().unique().tolist())
domain = clubs_in_view
range_ = [club_color_map.get(c, "#999999") for c in domain]  # fallback grey if missing

base = alt.Chart(ts).encode(
    x=alt.X(
        "publish_date:T",
        title="Date",
        scale=alt.Scale(domain=x_domain)  # same x-limits everywhere
    ),
    y=alt.Y(
        "cliches_per_10k:Q",
        title="Cumulative clichés per 10,000 words",
        scale=alt.Scale(domain=y_domain)  # shared y-limits
    ),
).properties(width="container")

line = base.mark_line().encode(
    color=alt.Color("club:N", scale=alt.Scale(domain=domain, range=range_), legend=None),
    tooltip=[
        alt.Tooltip("publish_date:T", title="Date"),
        alt.Tooltip("club:N", title="Club"),
        alt.Tooltip("manager_name:N", title="Manager on this date"),
        alt.Tooltip("cum_cliches:Q", title="Cumulative cliché hits"),
        alt.Tooltip("cum_words:Q", title="Cumulative words", format=",.0f"),
        alt.Tooltip("cliches_per_10k:Q", title="Cum. clichés /10k", format=".2f"),
    ],
)

points = base.mark_point(size=38, filled=True, opacity=0.85).encode(
    color=alt.Color("club:N", scale=alt.Scale(domain=domain, range=range_), legend=None),
)

# Dashed rules that stop just below the top label
rules = alt.Chart(ts).transform_filter(
    alt.datum.is_manager_change == True
).mark_rule(strokeDash=[4, 4], opacity=0.8).encode(
    x=alt.X("publish_date:T", scale=alt.Scale(domain=x_domain)),
    y=alt.Y("cliches_per_10k:Q"),
    y2=alt.value(y_domain[1] - top_pad),  # stop just below top
    color=alt.Color("club:N", scale=alt.Scale(domain=domain, range=range_), legend=None),
    tooltip=[
        alt.Tooltip("publish_date:T", title="Manager change on"),
        alt.Tooltip("prev_manager:N", title="From"),
        alt.Tooltip("manager_name:N", title="To"),
    ],
)

# Labels perfectly centered at top of the rule
labels = alt.Chart(ts).transform_filter(
    alt.datum.is_manager_change == True
).mark_text(
    angle=0,
    align="center",
    baseline="bottom",  # ensures text sits exactly at y-value
    dy=-2,              # slight upward offset for perfect alignment
    fontSize=11,
    fontWeight="bold"
).encode(
    x=alt.X("publish_date:T", scale=alt.Scale(domain=x_domain)),
    y=alt.value(y_domain[1] - top_pad),  # match rule's top
    text="change_label:N",
    color=alt.Color("club:N", scale=alt.Scale(domain=domain, range=range_), legend=None),
)

layered = alt.layer(rules, line, points, labels, data=ts)

chart = layered.facet(
    row=alt.Row("club:N", header=alt.Header(title=None, labelFontWeight="bold")),
    spacing=60,
).resolve_scale(
    x="independent",
    y="shared",
    color="independent"
)


# 4) Let Streamlit stretch the iframe to the column width
st.altair_chart(chart, use_container_width=True)



# -------------------- Help text --------------------
with st.expander("How this is calculated"):
    st.markdown(
        """
**Metric:** For each club and date we compute:
- daily words = sum of transcript word counts that day;
- daily cliché hits = count of cliché matches that day;
- cumulative words and cumulative hits (within each club);
- **cumulative clichés per 10,000 words = (cum_hits / cum_words) × 10,000**.

**Manager changes:** A dashed vertical line marks dates where the mode manager changes.
The label sits centered at the top of that line.
        """
    )
