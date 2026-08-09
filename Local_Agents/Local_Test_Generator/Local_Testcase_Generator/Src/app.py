import re
from pathlib import Path

import streamlit as st

import config_store
import jira_client
import llm_client

TEMPLATE_PATH = Path(__file__).parent.parent / "Templates" / "test_creater.md"

st.set_page_config(page_title="AI Test Case Generator", layout="wide")

# ── Sidebar — LLM provider selector ─────────────────────────────────────────
with st.sidebar:
    st.title("AI Test Case Generator")
    st.divider()

    st.subheader("LLM Provider")
    saved_provider = config_store.get("llm_provider", "ollama")
    provider = st.radio(
        "Select LLM",
        options=["ollama", "groq"],
        index=0 if saved_provider == "ollama" else 1,
        format_func=lambda x: "🦙 Ollama (local)" if x == "ollama" else "🤖 Groq (cloud)",
        key="llm_provider_radio",
    )

    if provider != saved_provider:
        cfg_update = config_store.load_config()
        cfg_update["llm_provider"] = provider
        config_store.save_config(cfg_update)

    if provider == "ollama":
        st.caption("Model: `llama3.2:latest`\nEndpoint: `localhost:11434`")
    else:
        st.caption("Model: `llama-3.1-8b-instant`\nvia Groq cloud API")

    st.divider()
    st.page_link("pages/settings.py", label="Settings", icon="⚙️")

# ── Main chat area ────────────────────────────────────────────────────────────
st.title("AI Test Case Generator")
st.caption(
    f"Active LLM: **{'🦙 Ollama' if provider == 'ollama' else '🤖 Groq'}**  ·  "
    "Type `create test cases for QA-102` and press Enter."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask me to generate test cases for a Jira ticket...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    match = re.search(r'\b([A-Z]+-\d+)\b', user_input)

    if not match:
        reply = (
            "I couldn't find a Jira ticket key in your message. "
            "Try something like: `create test cases for QA-102`"
        )
        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)
        st.stop()

    ticket_key = match.group(1)
    cfg = config_store.load_config()

    missing = [f for f in ("jira_url", "jira_email", "jira_api_token") if not cfg.get(f)]
    if missing:
        reply = (
            f"Jira credentials are not configured ({', '.join(missing)} missing). "
            "Please go to **Settings** and fill them in."
        )
        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.warning(reply)
        st.stop()

    with st.chat_message("assistant"):
        with st.spinner(f"Fetching {ticket_key} from Jira…"):
            try:
                ticket = jira_client.fetch_ticket(ticket_key, cfg)
            except jira_client.JiraClientError as e:
                err = f"Jira error: {e}"
                st.error(err)
                st.session_state.messages.append({"role": "assistant", "content": err})
                st.stop()

        merged_prompt = f"""You are a QA engineer. Generate plain text test cases for the Jira ticket below.

JIRA TICKET: {ticket['key']}
Summary: {ticket['summary']}
Type: {ticket['issue_type']} | Priority: {ticket['priority']}

Description:
{ticket['description'] or '(none provided)'}

Acceptance Criteria:
{ticket['acceptance_criteria'] or '(none provided)'}

---
OUTPUT RULES:
- Write each test case in plain text, no markdown, no code blocks, no bullet symbols.
- Number each test case: Test Case 1, Test Case 2, etc.
- Each test case must have exactly these sections:

Test Case [N]: [Short title]
Summary: [One sentence describing what is being tested]
Preconditions: [What must be true before the test starts]
Steps:
  1. [Action]
  2. [Action]
  3. [Action]
Expected Result: [What should happen]
Pass Criteria: [Specific measurable condition that confirms success]

- Cover: Happy Path, Negative scenarios, Edge cases, and Input validation.
- Do not explain yourself. Output only the test cases.
"""

        active_provider = "🦙 Ollama" if provider == "ollama" else "🤖 Groq"
        with st.spinner(f"Generating test cases via {active_provider}…"):
            try:
                response = llm_client.generate_test_cases(merged_prompt, cfg)
            except RuntimeError as e:
                err = str(e)
                st.error(err)
                st.session_state.messages.append({"role": "assistant", "content": err})
                st.stop()

        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
