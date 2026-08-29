"""Screen 2 - Settings.

Implements the Screen 2 contract in LLM.md section 9. Three cards, each an
st.form with Save and Test Connection side by side and a status pill.

Test Connection tests the values currently in the form, not the values last
saved, so testing before saving works.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools import config_store, jira_client, llm_client  # noqa: E402

st.set_page_config(page_title="Settings - Test Plan Agent", page_icon="⚙️", layout="centered")

config_store.init()
config = config_store.load_config()

for key in ("jira_status", "groq_status"):
    st.session_state.setdefault(key, "untested")
    st.session_state.setdefault(f"{key}_msg", "")

PILL_STYLES = {
    "connected": ("#065f46", "#6ee7b7", "Connected"),
    "failed": ("#7f1d1d", "#fca5a5", "Failed"),
    "untested": ("#374151", "#d1d5db", "Not tested"),
}


def status_pill(status: str) -> str:
    bg, fg, label = PILL_STYLES.get(status, PILL_STYLES["untested"])
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 10px;'
        f'border-radius:999px;font-size:0.78rem;font-weight:600;">{label}</span>'
    )


def show_result(status_key: str) -> None:
    """Render the stored outcome of the last Test Connection for a card."""
    status = st.session_state[status_key]
    message = st.session_state[f"{status_key}_msg"]
    if not message:
        return
    if status == "connected":
        st.success(message)
    else:
        st.error(message)


st.title("Settings")
st.caption("Credentials are stored in a gitignored `.env` file. They are never committed.")
# page_link resolves against the multipage router, which is absent when this
# file is executed standalone (or under AppTest). Degrade to a caption rather
# than taking the whole Settings page down over a navigation link.
try:
    st.page_link("app.py", label="Back to chat", icon="💬")
except Exception:
    st.caption("Run `streamlit run ui/app.py` to open the chat screen.")

missing = config_store.missing_required(config)
if missing:
    st.warning(
        "Test plan generation is blocked until these are set: "
        + ", ".join(missing)
    )
else:
    st.info("All required settings are present.")

st.divider()

# --------------------------------------------------------------------------
# Jira card
# --------------------------------------------------------------------------

head_left, head_right = st.columns([3, 1])
head_left.subheader("Jira Cloud")
head_right.markdown(status_pill(st.session_state.jira_status), unsafe_allow_html=True)

stored_token = config.get("JIRA_API_TOKEN", "")
if stored_token:
    st.caption(f"Stored API token: `{config_store.mask(stored_token)}`")

with st.form("jira_form"):
    jira_url = st.text_input(
        "Jira Base URL",
        value=config.get("JIRA_BASE_URL", ""),
        placeholder="https://your-domain.atlassian.net",
        help="The root URL only. No /browse and no trailing path.",
    )
    jira_email = st.text_input(
        "Jira Email",
        value=config.get("JIRA_EMAIL", ""),
        placeholder="you@company.com",
        help="Your Atlassian account email.",
    )
    jira_token = st.text_input(
        "Jira API Token",
        value=stored_token,
        type="password",
        help=(
            "Create at id.atlassian.com/manage-profile/security/api-tokens. "
            "Read scope is sufficient; this app never writes to Jira."
        ),
    )
    jira_project = st.text_input(
        "Default Project Key (optional)",
        value=config.get("JIRA_DEFAULT_PROJECT_KEY", ""),
        placeholder="QA",
        help="Set this and you can type 123 instead of QA-123.",
    )
    verify_ssl = st.toggle(
        "Verify SSL certificates",
        value=config_store.get_bool("JIRA_VERIFY_SSL", True),
        help=(
            "Leave on. Turning this off disables TLS certificate checking and "
            "exposes your API token to interception. Use only on a corporate "
            "network whose proxy rewrites certificates."
        ),
    )
    if not verify_ssl:
        st.warning(
            "SSL verification is off. Your Jira API token can be intercepted by "
            "anything on the network path. Turn this back on unless a corporate "
            "proxy makes it impossible."
        )

    save_col, test_col = st.columns(2)
    jira_saved = save_col.form_submit_button("Save", use_container_width=True)
    jira_tested = test_col.form_submit_button(
        "Test Connection", use_container_width=True, type="primary"
    )

form_jira = {
    "JIRA_BASE_URL": jira_url.strip().rstrip("/"),
    "JIRA_EMAIL": jira_email.strip(),
    "JIRA_API_TOKEN": jira_token.strip(),
    "JIRA_DEFAULT_PROJECT_KEY": jira_project.strip().upper(),
    "JIRA_VERIFY_SSL": "true" if verify_ssl else "false",
}

if jira_saved:
    config_store.save_config(form_jira)
    st.toast("Jira settings saved.")
    st.rerun()

if jira_tested:
    blanks = [k for k in ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN") if not form_jira[k]]
    if blanks:
        st.session_state.jira_status = "failed"
        st.session_state.jira_status_msg = "Fill in " + ", ".join(blanks) + " first."
    else:
        with st.spinner("Contacting Jira..."):
            result = jira_client.test_connection(form_jira)
        st.session_state.jira_status = "connected" if result["ok"] else "failed"
        st.session_state.jira_status_msg = result["message"]
    st.rerun()

show_result("jira_status")

st.divider()

# --------------------------------------------------------------------------
# Groq card
# --------------------------------------------------------------------------

head_left, head_right = st.columns([3, 1])
head_left.subheader("Groq")
head_right.markdown(status_pill(st.session_state.groq_status), unsafe_allow_html=True)

stored_groq = config.get("GROQ_API_KEY", "")
if stored_groq:
    st.caption(f"Stored API key: `{config_store.mask(stored_groq)}`")

with st.form("groq_form"):
    groq_key = st.text_input(
        "Groq API Key",
        value=stored_groq,
        type="password",
        help="Create at console.groq.com/keys",
    )
    groq_model = st.text_input(
        "Model ID",
        value=config.get("GROQ_MODEL", llm_client.DEFAULT_MODEL),
        help=(
            "Editable so a provider model rename needs no code change. "
            "Test Connection confirms the id actually resolves on your account."
        ),
    )
    groq_temp = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=config_store.get_float("GROQ_TEMPERATURE", 0.2),
        step=0.05,
        help="Low values keep generated plans close to reproducible.",
    )
    groq_max_tokens = st.number_input(
        "Max output tokens",
        min_value=1500,
        max_value=32768,
        value=config_store.get_int("GROQ_MAX_TOKENS", 6000),
        step=500,
        help=(
            "Raise this if long plans come back truncated. It is capped "
            "automatically to whatever the tokens-per-minute budget leaves "
            "after the prompt."
        ),
    )
    groq_tpm = st.number_input(
        "Tokens per minute limit",
        min_value=1000,
        max_value=1000000,
        value=config_store.get_int("GROQ_TPM_LIMIT", 8000),
        step=1000,
        help=(
            "Your Groq account limit. Input and output share this budget, so a "
            "max output above it is rejected with a 413 before the request runs. "
            "The on-demand tier is 8000."
        ),
    )

    save_col, test_col = st.columns(2)
    groq_saved = save_col.form_submit_button("Save", use_container_width=True)
    groq_tested = test_col.form_submit_button(
        "Test Connection", use_container_width=True, type="primary"
    )

form_groq = {
    "GROQ_API_KEY": groq_key.strip(),
    "GROQ_MODEL": groq_model.strip(),
    "GROQ_TEMPERATURE": str(groq_temp),
    "GROQ_MAX_TOKENS": str(int(groq_max_tokens)),
    "GROQ_TPM_LIMIT": str(int(groq_tpm)),
}

if groq_saved:
    config_store.save_config(form_groq)
    st.toast("Groq settings saved.")
    st.rerun()

if groq_tested:
    if not form_groq["GROQ_API_KEY"]:
        st.session_state.groq_status = "failed"
        st.session_state.groq_status_msg = "Enter a Groq API key first."
    elif not form_groq["GROQ_MODEL"]:
        st.session_state.groq_status = "failed"
        st.session_state.groq_status_msg = "Enter a model id first."
    else:
        with st.spinner("Contacting Groq..."):
            result = llm_client.test_connection(form_groq)
        st.session_state.groq_status = "connected" if result["ok"] else "failed"
        st.session_state.groq_status_msg = result["message"]
    st.rerun()

show_result("groq_status")

st.divider()

# --------------------------------------------------------------------------
# Preferences card
# --------------------------------------------------------------------------

st.subheader("Preferences")

with st.form("prefs_form"):
    display_name = st.text_input(
        "Display Name",
        value=config.get("DISPLAY_NAME", ""),
        help="Stamped as the author on generated plans. Cosmetic only.",
    )
    formats = ["markdown", "docx"]
    current_format = config.get("DEFAULT_OUTPUT_FORMAT", "markdown")
    output_format = st.selectbox(
        "Default Output Format",
        options=formats,
        index=formats.index(current_format) if current_format in formats else 0,
    )
    if st.form_submit_button("Save", use_container_width=True):
        config_store.save_config(
            {"DISPLAY_NAME": display_name.strip(), "DEFAULT_OUTPUT_FORMAT": output_format}
        )
        st.toast("Preferences saved.")
        st.rerun()

st.divider()

# --------------------------------------------------------------------------
# Maintenance
# --------------------------------------------------------------------------

with st.expander("Cache"):
    st.caption(
        "Fetched Jira issues are cached so re-running a generation does not "
        "hit the Jira API again. Clear the cache to pick up issue edits."
    )
    if st.button("Clear Jira cache"):
        removed = jira_client.clear_cache()
        st.success(f"Removed {removed} cached issue file(s).")
