import streamlit as st
import streamlit_wordcloud as wordcloud

def show_wordcloud(df):
    freq = df['cliche'].value_counts()
    words = [dict(text=c, value=int(n)) for c, n in freq.items()]

    # choose a safe pixel width so it doesn't overflow the content area
    wc_width = "100%"   # if you put this in a column, use ~600–800 instead
    wc_height = 600  # Increase height to fit more words; adjust as needed

    st.session_state['wordcloud'] = wordcloud.visualize(
        words,
        # width=wc_width,                 # int pixels (NOT "100%")
        # height=wc_height,               # set height explicitly
        # font_min=20,
        # font_max=100,
        # padding=5,
        palette="plasma_r",
        layout="rectangular",
        enable_tooltip=True,
        tooltip_data_fields={'text': 'Cliché', 'value': 'Count'},
    )