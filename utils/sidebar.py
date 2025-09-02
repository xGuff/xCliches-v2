import streamlit as st
import pandas as pd
from datetime import date

def sidebar_filters(df):
    st.sidebar.header("Filters")

    # Compute defaults
    min_date = pd.to_datetime(df['publish_date']).min().date()
    max_date = pd.to_datetime(df['publish_date']).max().date()
    default_start = min_date if min_date else date(2025, 8, 1)
    default_end = max_date if max_date else date.today()
    club_options = ["All Clubs"] + sorted(df['club'].unique())

    # Initialize session_state defaults if not set (before widgets)
    if "season" not in st.session_state:
        st.session_state["season"] = "2025/26"
    if "league" not in st.session_state:
        st.session_state["league"] = "Premier League"
    if "club" not in st.session_state:
        st.session_state["club"] = "All Clubs"
    if "date_range" not in st.session_state:
        st.session_state["date_range"] = (default_start, default_end)

    # Season filter
    season = st.sidebar.selectbox(
        "Select Season",
        options=["2024/25","2025/26"],
        index=0,
        key="season",
        help="More seasons coming soon!"
    )

    # League filter
    league = st.sidebar.selectbox(
        "Select League",
        options=["Premier League"],
        index=0,
        key="league",
        help="More leagues coming soon!"
    )

    # Club filter
    club = st.sidebar.selectbox(
        "Select Club",
        options=club_options,
        index=club_options.index(st.session_state["club"]) if st.session_state["club"] in club_options else 0,
        key="club",
        help="Choose a club to filter the data."
    )

    # Date range filter
    start_date, end_date = st.sidebar.date_input(
        "Select Date Range",
        value=st.session_state["date_range"],
        min_value=default_start,
        max_value=default_end,
        key="date_range"
    )

    # Do NOT update st.session_state after widget creation

    return season, league, club, start_date, end_date