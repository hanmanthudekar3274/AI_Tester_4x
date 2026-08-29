import re
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

import config_store
import jira_client
import llm_client

TEMPLATES_DIR = Path(__file__).parent.parent / "Templates"

st.set_page_config(
    page_title="AI Test Case Generator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ AI Test Case Generator")
    st.divider()
    st.page_link("pages/settings.py", label="⚙️  Settings")

# ── Page header ───────────────────────────────────────────────────────────────
st.title("AI Test Case Generator")

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Chat history ──────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Chat input ────────────────────────────────────────────────────────────────
user_input = st.chat_input("e.g. create test cases for QA-102")

# ── Processing ────────────────────────────────────────────────────────────────
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    cfg = config_store.load_config()
    match = re.search(r"\b([A-Z]+-\d+)\b", user_input)

    with st.chat_message("assistant"):
        response = ""
        try:
            if match:
                ticket_key = match.group(1)

                with st.spinner(f"Fetching Jira ticket {ticket_key}…"):
                    ticket = jira_client.fetch_ticket(ticket_key, cfg)

                system_prompt = (TEMPLATES_DIR / "test_creater.md").read_text(encoding="utf-8")
                user_prompt = (
                    f"---\n"
                    f"Jira Ticket: {ticket_key}\n"
                    f"Summary: {ticket['summary']}\n"
                    f"Description: {ticket['description'] or '(none)'}\n"
                    f"Acceptance Criteria: {ticket['acceptance_criteria'] or '(none)'}\n"
                    f"Priority: {ticket['priority']}\n"
                    f"Issue Type: {ticket['issue_type']}\n"
                    f"---\n"
                    f"Generate a complete set of test cases using the TC-001 format."
                )

                provider = cfg.get("llm_provider", "ollama")
                with st.spinner(f"Generating test cases with {provider}…"):
                    response = llm_client.generate_test_cases(
                        system_prompt + "\n\n" + user_prompt, cfg
                    )

            else:
                system_prompt = "You are a QA engineer. Help with testing questions."
                user_prompt = user_input

                provider = cfg.get("llm_provider", "ollama")
                with st.spinner(f"Thinking with {provider}…"):
                    response = llm_client.generate_test_cases(
                        system_prompt + "\n\n" + user_prompt, cfg
                    )

            st.markdown(response)

        except jira_client.JiraClientError as e:
            response = f"Jira error: {e}"
            st.error(response)
        except RuntimeError as e:
            response = f"LLM error: {e}"
            st.error(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
