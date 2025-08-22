import streamlit as st
from pathlib import Path
from utils.data_io import load_data_bundle, ensure_data
from utils.gw import current_gw, last_n_gw_range


st.set_page_config(
page_title="xGuff — Clichés Dashboard",
page_icon="🗣️",
layout="wide",
initial_sidebar_state="expanded",
)


# --- Sidebar
st.sidebar.title("xGuff — Clichés")
DATA_DIR = Path(st.session_state.get("data_dir", "data"))
st.sidebar.text_input("Data folder", value=str(DATA_DIR), key="data_dir")


with st.sidebar.expander("Filters", expanded=True):
    st.session_state.setdefault("min_pressers", 2)
    st.number_input("Min pressers per manager", 0, 20, key="min_pressers")


with st.sidebar.expander("Gameweeks", expanded=True):
    gw_now = current_gw(DATA_DIR)
    gw_min, gw_max = last_n_gw_range(DATA_DIR, n=38)
    st.session_state.setdefault("gw_range", (gw_min, gw_max))
    st.slider("GW Range", min_value=1, max_value=max(gw_max, 4), value=st.session_state["gw_range"], key="gw_range")
    st.toggle("Show last‑4 GW rolling view", value=True, key="rolling4")


# --- Data
ensure_data(Path(st.session_state["data_dir"]))
frag = load_data_bundle(Path(st.session_state["data_dir"]))


# --- Home content
st.title("🗣️ xGuff — Clichés Dashboard")
st.caption("Season‑to‑date cliché usage in manager press conferences. Replace placeholder data with your pipeline outputs.")


col1, col2, col3 = st.columns(3)
col1.metric("Managers", frag.stats["n_managers"])
col2.metric("Videos", frag.stats["n_videos"])
col3.metric("Clichés counted", frag.stats["n_cliches"])


st.divider()


st.subheader("Season leaderboard — clichés per 10k words")
from utils.plots import leaderboard_bar
fig = leaderboard_bar(frag, min_pressers=st.session_state["min_pressers"], gw_range=st.session_state["gw_range"])
st.plotly_chart(fig, use_container_width=True)


st.subheader("Trend by gameweek (rolling 4)")
from utils.plots import trend_lines
fig2 = trend_lines(frag, rolling4=st.session_state["rolling4"], gw_range=st.session_state["gw_range"])
st.plotly_chart(fig2, use_container_width=True)


st.info("Use the sidebar to set your data folder and filters. Add pages in the `pages/` folder.")