import streamlit as st
from pathlib import Path
from utils.data_io import load_data_bundle
from utils.plots import leaderboard_bar


st.set_page_config(page_title="Season So Far — xGuff")
DATA_DIR = Path(st.session_state.get("data_dir", "data"))
frag = load_data_bundle(DATA_DIR)


st.title("Season so far")
st.caption("Leaderboard and summaries for the selected GW range.")
fig = leaderboard_bar(frag, min_pressers=st.session_state.get("min_pressers", 2), gw_range=st.session_state.get("gw_range", (1, 38)))
st.plotly_chart(fig, use_container_width=True)