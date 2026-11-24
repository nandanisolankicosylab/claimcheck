"""Presentation for the deployed ClaimCheck app."""
from pathlib import Path

import streamlit as st


ASSET_DIR = Path(__file__).parent


def apply():
    css = (ASSET_DIR / "theme.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
