import streamlit as st
import pandas as pd

def show_video_feed(df):
    st.markdown("---")
    for _, row in df.iterrows():
        st.markdown(f"**{row['club']} ({row['manager']}):** *{row['cliche']}*")
        st.markdown(f"**Published:** {pd.to_datetime(row['publish_date']).date()}")
        st.markdown(f"**Excerpt:** {row['segment_text']}")
        video_id = row['video_id']
        start_time = int(row['start_time']) if pd.notnull(row['start_time']) else 0
        st.markdown(
            f"""
            <iframe width="100%"
            src="https://www.youtube.com/embed/{video_id}?start={start_time}"
            frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowfullscreen></iframe>
            """,
            unsafe_allow_html=True
        )
        st.markdown("---")