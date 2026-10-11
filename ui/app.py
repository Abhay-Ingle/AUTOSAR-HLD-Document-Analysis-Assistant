import os

import streamlit as st

st.set_page_config(page_title="AUTOSAR HLD Assistant", page_icon="A")
st.title("AUTOSAR HLD Document Analysis Assistant")
st.info(
    "Phase 1 foundation is running. PDF ingestion, cited Q&A, review queues, "
    "and analysis arrive in later phases."
)
st.code(f"Backend: {os.getenv('API_BASE_URL', 'http://localhost:8000')}")
