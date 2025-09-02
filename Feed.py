import streamlit as st
import pandas as pd
from utils.wordcloud import show_wordcloud
from utils.video_feed import show_video_feed
from utils.sidebar import sidebar_filters  # <-- Import your sidebar filter function

st.set_page_config(layout="centered", page_title="Expected Clichés")
st.title("Expected Clichés")

st.markdown(
    """
    Welcome to the Expected Clichés dashboard, brought to you by [xGuff.substack.com](https://xguff.substack.com)<br>
    
    Inspired by the likes of Bryan's Gunn and the Football Clichés Podcast, I'm on a mission to develop the definitive database of football managers saying things that football managers usually say.<br>
    
    Please explore my world leading data through the feed below, and the various charting options on the left sidebar.
    """,
    unsafe_allow_html=True
)

transcripts_df = pd.read_csv("data/raw/transcripts.csv")
cliches_df = pd.read_csv("data/processed/cliche_hits.csv")

# Get persistent sidebar filters
season, league, club, start_date, end_date = sidebar_filters(transcripts_df)

# Filter dataframe by selected filters
cliches_df['publish_date'] = pd.to_datetime(cliches_df['publish_date'])
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)
cliches_df = cliches_df[(cliches_df['publish_date'] >= start_date) & (cliches_df['publish_date'] <= end_date)]

if club != "All Clubs":
    cliches_df = cliches_df[cliches_df['club'] == club]

cliches_df = cliches_df.sort_values("publish_date", ascending=False)

st.subheader("Wordcloud of Clichés for the selected filters:")
show_wordcloud(cliches_df)
st.subheader("Video Feed of Clichés for the selected filters:")
show_video_feed(cliches_df)