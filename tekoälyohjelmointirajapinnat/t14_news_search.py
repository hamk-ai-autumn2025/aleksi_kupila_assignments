import streamlit as st
from utils.xai_utils import get_api_key, news_summarizer

st.title("AI-powered news summarizer")

col1, col2 = st.columns([0.7,0.3])

with col1:
    prompt = st.text_input("Topic or keyword","",500)
with col2:
    time_range = st.selectbox("Time period",["Today", "Past week", "Past month", "Past year", "Past 5 years"])

if st.button("Search results"):
    if not prompt:
        st.warning("No prompt entered!")
        pass
    client = get_api_key()
    if not client:
        st.warning("Fetching API key failed!")
        pass
    with st.spinner("Generating summaries..."):
        st.write_stream(news_summarizer(client, prompt, time_range))
