import streamlit as st
import pandas as pd
from datetime import date, datetime

def get_season_dates(season_str):
    # Example: "2024/25" -> start: 2024-08-01, end: 2025-05-31
    start_year = int(season_str.split('/')[0])
    start_date = date(start_year, 8, 1)
    end_date = date(start_year + 1, 5, 31)
    return start_date, end_date

def sidebar_filters(df):
    st.sidebar.header("Filters")

    # Season filter
    season = st.sidebar.selectbox(
        "Select Season",
        options=["2025/26", "2024/25"],
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

    # Filter clubs by selected season and league
    filtered_df = df[(df['season'] == season)]
    club_options = ["All Clubs"] + sorted(filtered_df['club'].unique())

    # Get season start/end dates
    season_start, season_end = get_season_dates(season)
    today = date.today()
    default_start = season_start
    default_end = min(today, season_end)

    # Club filter
    club = st.sidebar.selectbox(
        "Select Club",
        options=club_options,
        index=club_options.index(st.session_state.get("club", "All Clubs")) if st.session_state.get("club", "All Clubs") in club_options else 0,
        key="club",
        help="Choose a club to filter the data."
    )

    # Date range filter
    start_date, end_date = st.sidebar.date_input(
        "Select Date Range",
        value=(default_start, default_end),
        min_value=season_start,
        max_value=default_end,
        key="date_range"
    )

    return season, league, club, start_date, end_date
