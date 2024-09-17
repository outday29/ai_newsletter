from pathlib import Path

import streamlit as st

from newsletter.news.news import Newsletter, get_newsletters
from newsletter.scraper.reddit import (
    Preference,
    load_reddit_preferences,
    save_reddit_preferences,
)
from newsletter.settings import DataSource, settings
from newsletter.ui.utils import add_spacing


def configure_preferences(platform: DataSource):
    match platform:
        case "Reddit":
            configure_reddit_preferences()
        case _:
            pass


@st.dialog(title="Reddit preferences", width="large")
def configure_reddit_preferences():
    existing_preferences = load_reddit_preferences()

    def set_upvotes(key: str, preference: Preference):
        preference.post_filter.upvotes = st.session_state[key]
        save_reddit_preferences(existing_preferences)

    def set_upvote_ratio(key: str, preference: Preference):
        preference.post_filter.upvote_ratio = st.session_state[key]
        save_reddit_preferences(existing_preferences)

    def set_recency(key: str, preference: Preference):
        preference.post_filter.recency = st.session_state[key]
        save_reddit_preferences(existing_preferences)

    button_cols = st.columns(5, gap="small")
    st.write("Subreddit to scrape")
    for idx, preference in enumerate(existing_preferences):
        if idx % 5 == 0:
            button_cols = st.columns(5, gap="small")

        with button_cols[idx % 5].popover(
            preference.subreddit_name, use_container_width=True
        ):
            upvotes_key = f"upvotes_{preference.subreddit_name}"
            st.number_input(
                label="Minimum upvotes",
                value=preference.post_filter.upvotes,
                min_value=0,
                key=upvotes_key,
                step=20,
                kwargs={
                    "key": upvotes_key,
                    "preference": preference,
                },
                on_change=set_upvotes,
            )
            upvote_ratio_key = f"upvote_ratio_{preference.subreddit_name}"
            st.number_input(
                label="Minimum upvote ratio",
                value=preference.post_filter.upvote_ratio,
                min_value=0.0,
                max_value=1.0,
                step=0.1,
                key=upvote_ratio_key,
                kwargs={
                    "key": upvote_ratio_key,
                    "preference": preference,
                },
                on_change=set_upvote_ratio,
            )
            recency_key = f"recency_{preference.subreddit_name}"
            st.number_input(
                label="Recency (days)",
                value=preference.post_filter.recency,
                min_value=1,
                max_value=7,
                step=1,
                key=recency_key,
                kwargs={
                    "key": recency_key,
                    "preference": preference,
                },
                on_change=set_recency,
            )

    add_spacing(100)
    _, col = st.columns(spec=[0.7, 0.3], gap="small")
    with col.popover(label="Add new subreddit", use_container_width=True):
        new_subreddit_name = st.text_input(
            label="Subreddit name",
            value="",
        )


def toggle_empty_newsletter(newsletter_path: list[Path], toggle_status: bool):
    for i in newsletter_path:
        newsletter = Newsletter.from_path(i)
        if len(newsletter.news) == 0:
            st.session_state[f"checkbox_{i.stem}"] = toggle_status


def toggle_all_newsletter(newsletter_path: list[Path], toggle_status: bool):
    for i in newsletter_path:
        st.session_state[f"checkbox_{i.stem}"] = toggle_status


def clear_data(newsletter_path: list[Path]):
    deleted_count = 0
    for i in newsletter_path:
        if st.session_state[f"checkbox_{i.stem}"]:
            i.unlink()
            deleted_count += 1

    if deleted_count == 0:
        st.toast("No newsletter selected", icon=":material/warning:")

    else:
        st.toast("Successfully deleted", icon=":material/check:")


def render_data_page():
    st.write("# Data")
    add_spacing(20)

    st.write("### Configure data source")

    supported_data_source = settings.get_supported_data_source()

    button_cols = st.columns(6, gap="small")
    for idx, (data_source, supported) in enumerate(supported_data_source.items()):
        button_cols[idx].button(
            label=data_source,
            args=[data_source],
            disabled=not supported,
            on_click=configure_preferences,
            type="secondary",
            use_container_width=True,
        )

    add_spacing(20)

    newsletters = get_newsletters()

    st.write("### Clear data")
    col1, col2, _ = st.columns(
        spec=[0.3, 0.2, 0.5], gap="small", vertical_alignment="bottom"
    )
    col1.toggle(
        label="Select empty",
        value=False,
        key="toggle_empty",
        on_change=toggle_empty_newsletter,
        kwargs={
            "newsletter_path": newsletters,
            "toggle_status": (
                not st.session_state["toggle_empty"]
                if "toggle_empty" in st.session_state
                else True
            ),
        },
    )
    col2.toggle(
        label="Select all",
        value=False,
        key="toggle_all",
        on_change=toggle_all_newsletter,
        kwargs={
            "newsletter_path": newsletters,
            "toggle_status": (
                not st.session_state["toggle_all"]
                if "toggle_all" in st.session_state
                else True
            ),
        },
    )

    with st.container(height=500):
        st.write("<h4>Saved newsletters</h4>", unsafe_allow_html=True)
        for newsletter in newsletters:
            st.checkbox(
                label=newsletter.stem,
                key=f"checkbox_{newsletter.stem}",
            )

    add_spacing(20)
    _, col3 = st.columns(spec=[0.85, 0.15], vertical_alignment="bottom")

    col3.button(
        label="Clear data",
        type="primary",
        use_container_width=True,
        on_click=clear_data,
        kwargs={"newsletter_path": newsletters},
    )
