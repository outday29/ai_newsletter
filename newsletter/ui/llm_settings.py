import streamlit as st

from newsletter.settings import settings
from newsletter.ui.utils import add_spacing


def render_llm_settings():
    st.write("# LLM settings")
    st.write("## Supported platform")
    add_spacing(10)
    supported_platform = settings.get_supported_platform()
    for platform, value in supported_platform.items():
        st.checkbox(
            label=platform,
            value=value,
            disabled=True,
        )
