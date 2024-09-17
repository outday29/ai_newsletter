import streamlit as st

from newsletter.settings import settings


def reset_interest_edit(original_prompt: str):
    st.session_state["interest_edit"] = original_prompt


def save_interest_prompt(new_prompt: str):
    settings.storage.save_user_interest_prompt(new_prompt)
    st.toast("Successfully saved prompt", icon=":material/check:")


def render_preferences_page():
    st.write("## Edit preferences")
    original_prompt = settings.storage.get_user_interest_prompt()
    if original_prompt is None:
        st.write("No prompt found")
        st.toast("Interest.txt does not exist", icon=":material/error:")

    else:
        st.text_area(
            label="Interest prompt",
            key="interest_edit",
            value=original_prompt,
            max_chars=5000,
            height=450,
        )

        _, col2, col3 = st.columns(
            spec=[0.78, 0.12, 0.1], gap="small", vertical_alignment="bottom"
        )

        col2.button(
            "Reset",
            type="secondary",
            key="reset_interest",
            on_click=reset_interest_edit,
            use_container_width=True,
            kwargs={"original_prompt": original_prompt},
        )

        col3.button(
            "Save",
            type="primary",
            key="save_interest",
            on_click=save_interest_prompt,
            use_container_width=True,
            kwargs={"new_prompt": st.session_state["interest_edit"]},
        )
