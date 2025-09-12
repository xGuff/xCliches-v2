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
        font_scale=1,
        palette="plasma_r",
        layout="rectangular",
        enable_tooltip=True,
        tooltip_data_fields={'text': 'Cliché', 'value': 'Count'},
    )