import streamlit as st

from newsletter.llm.fireworks_ai import (
    get_model_list as get_fireworks_model_list,
)
from newsletter.llm.fireworks_ai import (
    model_format_func as fireworks_format_func,
)
from newsletter.llm.openai import (
    get_model_list as get_openai_model_list,
)
from newsletter.llm.openai import (
    model_format_func as openai_format_func,
)
from newsletter.llm.together_llm import (
    get_model_list as get_together_model_list,
)
from newsletter.llm.together_llm import (
    model_format_func as together_format_func,
)
from newsletter.settings import LLMPlatform


def add_spacing(spacing: int):
    st.write(f"<div style='height: {spacing}px'></div>", unsafe_allow_html=True)


def get_supported_model(platform: LLMPlatform) -> list[str]:
    match platform:
        case "Fireworks AI":
            return get_fireworks_model_list()

        case "Together AI":
            return get_together_model_list()

        case "OpenAI":
            return get_openai_model_list()


def get_model_alias_formatter(platform: LLMPlatform) -> callable:
    match platform:
        case "Fireworks AI":
            return fireworks_format_func

        case "Together AI":
            return together_format_func

        case "OpenAI":
            return openai_format_func
