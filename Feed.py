import streamlit as st
import pandas as pd
from utils.wordcloud import show_wordcloud
from utils.video_feed import show_video_feed
from utils.sidebar import sidebar_filters  # <-- Import your sidebar filter function
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(layout="centered", page_title="Expected Clichés")
st.title("Expected Clichés")

st.markdown(
    """
    Welcome to the Expected Clichés dashboard, brought to you by <a href="https://xguff.substack.com" style="color: #da7842;">xGuff.substack.com</a><br>
    
    Inspired by the likes of <a href="https://x.com/bryansgunn?lang=en-GB" style="color: #da7842;">Bryan's Gunn</a> and the <a href="https://open.spotify.com/show/6U4LfcF1ymFwxRDEsUq3Gd" style="color: #da7842;">Football Clichés Podcast</a>, I'm on a mission to develop the definitive database of football managers (and occasionally journalists) saying classic football phrases.<br>

    You can find me writing about this data and more on my <a href="https://xguff.substack.com" style="color: #da7842;">Substack</a>.

    Please explore my *world-leading* data through the video feed below, and the various charting options on the left sidebar.
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

st.subheader("Wordcloud of clichés found for the selected filters:")
st.write("Click on a cliché to filter the video feed below.")
show_wordcloud(cliches_df)

# Button to reset wordcloud selection
if st.button("Reset selection"):
    streamlit_js_eval(js_expressions="parent.window.location.reload()")


# Filter by selected cliche from wordcloud
wordcloud = st.session_state.get('wordcloud', None)
selected_cliche = None
if wordcloud and wordcloud.get("clicked"):
    selected_cliche = wordcloud["clicked"]["text"]

if selected_cliche:
    st.info(f"Filtering video feed by cliché: '{selected_cliche}'")
    filtered_df = cliches_df[cliches_df['cliche'] == selected_cliche]
else:
    filtered_df = cliches_df

st.subheader("Video feed of clichés for the selected filters:")
show_video_feed(filtered_df)