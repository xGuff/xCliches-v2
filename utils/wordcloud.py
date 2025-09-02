import streamlit as st
import streamlit_wordcloud as wordcloud

# st.set_page_config(layout="wide")

# (optional) trim Streamlit's side padding so the iframe lines up better
# st.markdown("""
# <style>
# .block-container { padding-left: 0.75rem; padding-right: 0.75rem; }
# </style>
# """, unsafe_allow_html=True)

def show_wordcloud(df):
    freq = df['cliche'].value_counts()
    words = [dict(text=c, value=int(n)) for c, n in freq.items()]

    # choose a safe pixel width so it doesn't overflow the content area
    wc_width = "100%"   # if you put this in a column, use ~600–800 instead
    wc_height = "100%"

    wordcloud.visualize(
        words,
        width=wc_width,                 # int pixels (NOT "100%")
        height=wc_height,               # set height explicitly
        padding=0,                      # removes extra gaps around words
        palette="plasma_r",
        enable_tooltip=True,
        tooltip_data_fields={'text': 'Cliché', 'value': 'Count'},
    )
