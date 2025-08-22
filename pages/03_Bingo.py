import streamlit as st
from pathlib import Path
from utils.data_io import load_data_bundle


st.set_page_config(page_title="Bingo — xGuff")
DATA_DIR = Path(st.session_state.get("data_dir", "data"))
frag = load_data_bundle(DATA_DIR)


st.title("Cliché Bingo (placeholder)")
st.write("This page will generate bingo cards per club/manager from the lexicon + counts.")
st.dataframe(frag.cliche_counts.head(20))