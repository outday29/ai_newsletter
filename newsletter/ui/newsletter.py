import datetime

import streamlit as st
from loguru import logger

from newsletter.llm.fireworks_ai import FireworksAI
from newsletter.llm.openai import OpenAILLM
from newsletter.llm.together_llm import Model, TogetherLLM
from newsletter.news.news import News, Newsletter, get_newsletters
from newsletter.news.summarize import Summarizer
from newsletter.scraper.post import PostList
from newsletter.scraper.reddit import load_reddit_preferences, reddit_scraper
from newsletter.settings import LLMPlatform, settings
from newsletter.ui.utils import (
    add_spacing,
    get_model_alias_formatter,
    get_supported_model,
)

generation_status = False


def generate_default_newsletter_name() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")


def create_task(
    platform: LLMPlatform,
    name: str,
    filter_model: list[Model],
    summary_model: list[Model],
):
    st.session_state["generation_task"] = {
        "platform": platform,
        "name": name,
        "filter_model": filter_model,
        "summary_model": summary_model,
    }


def render_generate_newsletter():
    with st.status("Generating newsletter...") as status:
        try:
            task = st.session_state["generation_task"]
            platform: LLMPlatform = task["platform"]
            name = task["name"]
            filter_models = task["filter_model"]
            summary_models = task["summary_model"]

            preferences = load_reddit_preferences()
            st.write("Scraping data...")
            res = reddit_scraper.scrape_with_preferences(preferences=preferences)

            all_post_list = []
            for subreddit_name, post_list in res.items():
                filepath = settings.storage.raw_data_folder / f"{subreddit_name}.json"
                post_list.save(filepath)
                all_post_list.append(post_list)

            st.write("Scraping completed.")
            st.write("Summarizing data...")
            match platform:
                case "Fireworks AI":
                    summarizer = Summarizer(llm=FireworksAI())

                case "Together AI":
                    summarizer = Summarizer(llm=TogetherLLM())

                case "OpenAI":
                    summarizer = Summarizer(llm=OpenAILLM())

            aggregated_post_list = PostList.from_post_lists(
                source="aggregated",
                post_lists=all_post_list,
            )
            summary = summarizer.summarize_post_list(
                post_list=aggregated_post_list,
                summary_model=summary_models,
                filter_model=filter_models,
                newsletter_name=name,
            )
            summary.save()

            st.write("Summarizing completed.")

        except Exception as e:
            logger.exception(e)
            st.write("Failed, see logs for details")
            status.update(
                label="Generation failed",
                state="error",
            )

        else:
            status.update(
                label="Generation completed",
                state="complete",
            )

        finally:
            st.session_state["generation_task"] = {}


@st.dialog("Generate newsletter")
def select_scrape_settings():
    default_newsletter_name = generate_default_newsletter_name()

    newsletter_name = st.text_input(
        label="Newsletter name",
        help="Must be unique",
        value=(
            default_newsletter_name
            if "newsletter_name" not in st.session_state
            else st.session_state["newsletter_name"]
        ),
        key="newsletter_name",
    )
    supported_platform_dict = settings.get_supported_platform()
    supported_platform = filter(
        lambda x: supported_platform_dict[x], supported_platform_dict
    )
    selected_platform = st.selectbox(
        label="Platform",
        options=supported_platform,
        index=None,
        key="platform",
    )

    if selected_platform is not None:
        models_list = get_supported_model(platform=selected_platform)
        format_func = get_model_alias_formatter(platform=selected_platform)
        summary_model = st.multiselect(
            label="Model for summarization",
            options=models_list,
            default=None,
            key="summary_model",
            format_func=format_func,
            help="Model priority is ordered from left to right. Subsequent model will be used if the previous one is not available.",
        )
        filter_model = st.multiselect(
            label="Model for filtering",
            options=models_list,
            default=None,
            key="filter_model",
            format_func=format_func,
            help="Model priority is ordered from left to right. Subsequent model will be used if the previous one is not available.",
        )

        add_spacing(20)

        if st.button(
            label="Generate",
            type="primary",
            disabled=summary_model is None and filter_model is None,
        ):
            create_task(
                platform=selected_platform,
                name=newsletter_name,
                filter_model=filter_model,
                summary_model=summary_model,
            )
            st.rerun()

    else:
        add_spacing(20)
        st.button(label="Generate", type="primary", disabled=True)


def render_scrape_button():
    st.button(
        "New",
        type="primary",
        on_click=select_scrape_settings,
        disabled=generation_status,
    )


def render_newsletter(newsletter: Newsletter):
    def render_news(news: News):
        st.write(f"### {news.title}")
        st.write("\n")
        st.write(f"{news.description}")
        st.write("##### Source:")
        for source in news.sources:
            link = f"https://reddit.com{source}"
            st.page_link(page=link, label=link)

    st.caption("Created at: " + newsletter.created_at.strftime("%Y-%m-%d %H:%M:%S"))

    if len(newsletter.news) == 0:
        st.write("<div style='height: 20px'></div>", unsafe_allow_html=True)
        st.write("No important news.")

    for news in newsletter.news:
        render_news(news)
        st.write("---")


def render_newsletter_page():
    global generation_status
    if "generation_task" in st.session_state and (
        len(st.session_state["generation_task"].keys()) != 0 and not generation_status
    ):
        generation_status = True
        render_generate_newsletter()
        generation_status = False

    newsletters = get_newsletters()

    col1, col2 = st.columns(
        spec=[0.85, 0.15], gap="medium", vertical_alignment="bottom"
    )

    with col1:
        # A dropdown to select the date of the newsletter
        selected_newsletter_path = st.selectbox(
            "Select newsletter",
            options=newsletters,
            index=None,
            format_func=lambda x: x.name,
        )

    with col2:
        render_scrape_button()

    if selected_newsletter_path is not None:
        selected_newsletter = Newsletter.from_path(selected_newsletter_path)
        render_newsletter(selected_newsletter)
