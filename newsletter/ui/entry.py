import streamlit as st

from newsletter.logger import setup_logger
from newsletter.ui.data import render_data_page
from newsletter.ui.llm_settings import render_llm_settings
from newsletter.ui.newsletter import render_newsletter_page
from newsletter.ui.preferences import render_preferences_page


def render():
    st.set_page_config(
        page_title="AI Newsletter", page_icon=":material/newspaper:", layout="wide"
    )

    if "log_init" not in st.session_state or st.session_state["log_init"] is False:
        setup_logger()
        st.session_state["log_init"] = True

    data_page = st.Page(
        render_data_page, title="Data", icon=":material/draft:", url_path="data"
    )
    preference_page = st.Page(
        render_preferences_page,
        title="Preferences",
        icon=":material/settings_account_box:",
        url_path="preferences",
    )
    newsletters_page = st.Page(
        render_newsletter_page,
        title="Newsletters",
        icon=":material/calendar_today:",
        url_path="newsletters",
        default=True,
    )
    llm_settings_page = st.Page(
        render_llm_settings,
        title="LLM Settings",
        icon=":material/smart_toy:",
        url_path="llm-settings",
    )

    pg = st.navigation(
        {
            "Newsletters": [newsletters_page],
            "Settings": [data_page, preference_page, llm_settings_page],
        }
    )
    pg.run()
