import streamlit as st
from pathlib import Path
from utils.data_io import load_data_bundle
from utils.plots import trend_lines


st.set_page_config(page_title="Trends — xGuff")
DATA_DIR = Path(st.session_state.get("data_dir", "data"))
frag = load_data_bundle(DATA_DIR)


st.title("Trends by gameweek")
st.caption("Rolling 4‑GW cliché rates by manager.")
fig = trend_lines(frag, rolling4=True, gw_range=st.session_state.get("gw_range", (1, 38)))
st.plotly_chart(fig, use_container_width=True)