"""
Analyzer Agent — Streamlit 3-step wizard.

Usage:
    cd Requirement_Analyser_Agent/src
    streamlit run app.py
"""

import os
import sys

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Ensure local packages are importable
sys.path.insert(0, os.path.dirname(__file__))

from agents.analyzer_agent import AnalyzerAgent
from connectors.jira_connector import JiraConnector
from connectors.confluence_connector import ConfluenceConnector
from connectors.slack_connector import SlackConnector
from connectors.text_connector import TextConnector
from llm.llm_router import LLMRouter
from output.docx_generator import DocxGenerator

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Analyzer Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
DEFAULTS = {
    "context_blocks": [],
    "analysis_result": None,
    "router": None,
}
for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ---------------------------------------------------------------------------
# Sidebar — LLM & credentials
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🧠 Analyzer Agent")
    st.caption("AI-powered QA test plan generator")
    st.divider()

    # --- LLM Backend ---
    st.subheader("LLM Backend")
    ollama_on = st.toggle("Ollama (local)", value=os.getenv("LLM_OLLAMA_ENABLED", "false").lower() == "true")
    groq_on = st.toggle("Groq (cloud)", value=os.getenv("LLM_GROQ_ENABLED", "false").lower() == "true")

    ollama_url = st.text_input("Ollama URL", value=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"), disabled=not ollama_on)
    ollama_model = st.text_input("Ollama model", value=os.getenv("OLLAMA_MODEL", "llama3.2"), disabled=not ollama_on)
    groq_key = st.text_input("Groq API key", value=os.getenv("GROQ_API_KEY", ""), type="password", disabled=not groq_on)
    groq_model = st.selectbox(
        "Groq model",
        ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"],
        disabled=not groq_on,
    )

    if st.button("Connect LLM", use_container_width=True):
        router = LLMRouter(
            ollama_enabled=ollama_on,
            groq_enabled=groq_on,
            ollama_base_url=ollama_url,
            ollama_model=ollama_model,
            groq_api_key=groq_key,
            groq_model=groq_model,
        )
        st.session_state.router = router
        if router.warning:
            st.warning(router.warning)
        if router.active_backend == "None":
            st.error("No LLM configured — enable at least one backend.")
        else:
            st.success(f"Active backend: **{router.active_backend}**")

    st.divider()

    # --- Jira Credentials ---
    with st.expander("Jira credentials", expanded=True):
        jira_url = st.text_input("Jira base URL", value=os.getenv("JIRA_BASE_URL", ""), placeholder="https://company.atlassian.net")
        jira_email = st.text_input("Jira email", value=os.getenv("JIRA_EMAIL", ""))
        jira_token = st.text_input("Jira API token", value=os.getenv("JIRA_API_TOKEN", ""), type="password")

    # --- Confluence Credentials ---
    with st.expander("Confluence credentials"):
        conf_url = st.text_input("Confluence base URL", value=os.getenv("CONFLUENCE_BASE_URL", ""), placeholder="https://company.atlassian.net/wiki")
        conf_email = st.text_input("Confluence email", value=os.getenv("CONFLUENCE_EMAIL", jira_email))
        conf_token = st.text_input("Confluence API token", value=os.getenv("CONFLUENCE_API_TOKEN", jira_token), type="password")

    # --- Slack Credentials ---
    with st.expander("Slack credentials"):
        slack_token = st.text_input("Slack bot token", value=os.getenv("SLACK_BOT_TOKEN", ""), type="password", placeholder="xoxb-...")

# ---------------------------------------------------------------------------
# Main area — 3-tab wizard
# ---------------------------------------------------------------------------

st.title("Requirement Analyzer Agent")
st.caption("Enter a Jira story ID and the agent will produce a full IEEE 829 test plan.")

tab1, tab2, tab3 = st.tabs(["1 · Collect Data", "2 · Configure & Run", "3 · Test Plan"])

# ===========================================================================
# TAB 1 — Collect Data
# ===========================================================================
with tab1:
    st.header("Collect Data")
    st.write("Fetch requirements from Jira, Confluence, Slack, or paste text/upload a file.")

    col_left, col_right = st.columns(2)

    # --- Jira ---
    with col_left:
        st.subheader("Jira")
        jira_key = st.text_input(
            "Jira issue key",
            placeholder="e.g. AAA-50",
            help='The agent will fetch the issue, acceptance criteria, and all comments.',
        )
        if st.button("Fetch Jira story", use_container_width=True):
            if not all([jira_url, jira_email, jira_token, jira_key]):
                st.error("Fill in Jira credentials (sidebar) and an issue key.")
            else:
                with st.spinner(f"Fetching {jira_key}…"):
                    try:
                        connector = JiraConnector(jira_url, jira_email, jira_token)
                        block = connector.fetch(jira_key.strip().upper())
                        st.session_state.context_blocks = [
                            b for b in st.session_state.context_blocks
                            if not b.startswith("=== JIRA ISSUE")
                        ]
                        st.session_state.context_blocks.append(block)
                        st.success(f"Fetched {jira_key}")
                        with st.expander("Preview"):
                            st.text(block[:1500] + ("…" if len(block) > 1500 else ""))
                    except Exception as exc:
                        st.error(f"Jira error: {exc}")

    # --- Confluence ---
    with col_right:
        st.subheader("Confluence (optional)")
        conf_page_id = st.text_input("Confluence page ID", placeholder="e.g. 123456789")
        conf_query = st.text_input("Or search query", placeholder="e.g. login feature spec")
        conf_space = st.text_input("Space key (for search)", placeholder="e.g. PROD")

        if st.button("Fetch Confluence", use_container_width=True):
            if not all([conf_url, conf_email, conf_token]):
                st.error("Fill in Confluence credentials in the sidebar.")
            else:
                with st.spinner("Fetching Confluence…"):
                    try:
                        connector = ConfluenceConnector(conf_url, conf_email, conf_token)
                        if conf_page_id.strip():
                            block = connector.fetch_by_id(conf_page_id.strip())
                        elif conf_query.strip():
                            block = connector.search(conf_query.strip(), space_key=conf_space.strip())
                        else:
                            st.warning("Enter a page ID or search query.")
                            block = ""
                        if block:
                            st.session_state.context_blocks.append(block)
                            st.success("Confluence content added.")
                            with st.expander("Preview"):
                                st.text(block[:1500] + ("…" if len(block) > 1500 else ""))
                    except Exception as exc:
                        st.error(f"Confluence error: {exc}")

    st.divider()
    col_slack, col_file = st.columns(2)

    # --- Slack ---
    with col_slack:
        st.subheader("Slack (optional)")
        slack_channel = st.text_input("Channel ID", placeholder="e.g. C0123ABCDEF")
        slack_limit = st.slider("Messages to fetch", 10, 200, 50)
        if st.button("Fetch Slack channel", use_container_width=True):
            if not slack_token:
                st.error("Enter a Slack bot token in the sidebar.")
            elif not slack_channel.strip():
                st.error("Enter a channel ID.")
            else:
                with st.spinner("Fetching Slack…"):
                    try:
                        connector = SlackConnector(slack_token)
                        block = connector.fetch_channel(slack_channel.strip(), limit=slack_limit)
                        st.session_state.context_blocks.append(block)
                        st.success("Slack messages added.")
                        with st.expander("Preview"):
                            st.text(block[:1500] + ("…" if len(block) > 1500 else ""))
                    except Exception as exc:
                        st.error(f"Slack error: {exc}")

    # --- File / Paste ---
    with col_file:
        st.subheader("File / Text (optional)")
        uploaded = st.file_uploader(
            "Upload a file",
            type=["txt", "md", "pdf", "docx"],
            help="Spec sheet, meeting notes, PRD, etc.",
        )
        if uploaded and st.button("Add file", use_container_width=True):
            connector = TextConnector()
            block = connector.from_file(uploaded.read(), uploaded.name)
            st.session_state.context_blocks.append(block)
            st.success(f"Added: {uploaded.name}")

        pasted = st.text_area("Or paste text here", height=120, placeholder="Paste requirements, notes, or any context…")
        if pasted and st.button("Add pasted text", use_container_width=True):
            connector = TextConnector()
            block = connector.from_paste(pasted)
            st.session_state.context_blocks.append(block)
            st.success("Pasted text added.")

    st.divider()
    # Context summary
    n = len(st.session_state.context_blocks)
    if n:
        st.success(f"**{n} context block(s) collected.** Ready for Step 2.")
        if st.button("Clear all context", type="secondary"):
            st.session_state.context_blocks = []
            st.rerun()
    else:
        st.info("No context collected yet. Fetch at least one Jira story to continue.")

# ===========================================================================
# TAB 2 — Configure & Run
# ===========================================================================
with tab2:
    st.header("Configure & Run")

    col_a, col_b = st.columns(2)
    with col_a:
        feature_name = st.text_input("Feature name", placeholder="e.g. User Login")
        product = st.text_input("Product", placeholder="e.g. MyApp Web")
        release = st.text_input("Release / Sprint", placeholder="e.g. v2.4 / Sprint 42")
    with col_b:
        team_size = st.text_input("QA team size", placeholder="e.g. 3")
        timeline = st.text_input("Testing timeline", placeholder="e.g. 5 business days")

    st.divider()
    st.subheader("Readiness Checklist")
    checks = {
        "At least one Jira story fetched": any(b.startswith("=== JIRA") for b in st.session_state.context_blocks),
        "LLM backend connected": st.session_state.router is not None
            and st.session_state.router.active_backend != "None",
        "Feature name provided": bool(feature_name.strip()),
    }
    all_ready = all(checks.values())
    for label, ok in checks.items():
        icon = "✅" if ok else "❌"
        st.write(f"{icon} {label}")

    st.divider()
    run_disabled = not all_ready
    if run_disabled:
        st.warning("Complete the checklist above before running.")

    if st.button("Run Analysis", type="primary", use_container_width=True, disabled=run_disabled):
        status_box = st.empty()
        progress = st.progress(0, text="Starting…")

        steps_done = [0]

        def on_step(msg: str):
            step_map = {
                "Fusing": 25,
                "Extracting": 50,
                "Analysing": 75,
                "Generating": 90,
                "Done": 100,
            }
            pct = next((v for k, v in step_map.items() if k.lower() in msg.lower()), steps_done[0])
            steps_done[0] = pct
            progress.progress(pct, text=msg)
            status_box.info(msg)

        agent = AnalyzerAgent(st.session_state.router)
        result = agent.run(
            context_blocks=st.session_state.context_blocks,
            feature_name=feature_name,
            product=product,
            release=release,
            team_size=team_size,
            timeline=timeline,
            on_step=on_step,
        )
        st.session_state.analysis_result = result
        progress.empty()
        status_box.empty()

        if result.error:
            st.error(f"Pipeline error: {result.error}")
        else:
            st.success("Analysis complete! Switch to the **Test Plan** tab.")

# ===========================================================================
# TAB 3 — Test Plan
# ===========================================================================
with tab3:
    st.header("Test Plan")

    result = st.session_state.analysis_result

    if result is None:
        st.info("Run the analysis in Step 2 first.")
    elif result.error:
        st.error(f"Analysis failed: {result.error}")
    else:
        # --- Metrics dashboard ---
        reqs = result.requirements_json
        disc = result.discussion_json
        fr_count = len(reqs.get("functional", []))
        nfr_count = len(reqs.get("non_functional", []))
        flag_count = len(reqs.get("flagged_items", []))
        oq_count = len(disc.get("open_questions", []))
        risk_count = len(disc.get("risks", []))

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Functional Reqs", fr_count)
        m2.metric("Non-Functional Reqs", nfr_count)
        m3.metric("Flagged Items", flag_count, delta=f"-{flag_count} need attention" if flag_count else None, delta_color="inverse")
        m4.metric("Open Questions", oq_count)
        m5.metric("Risks", risk_count)

        st.divider()

        # --- Extracted requirements ---
        with st.expander("Extracted Requirements (JSON)", expanded=False):
            st.json(reqs)

        # --- Discussion signals ---
        with st.expander("Discussion Signals (JSON)", expanded=False):
            st.json(disc)

        st.divider()

        # --- Full test plan ---
        st.subheader("Full Test Plan")
        st.markdown(result.test_plan_markdown)

        st.divider()

        # --- Downloads ---
        st.subheader("Download")
        dl_col1, dl_col2 = st.columns(2)

        with dl_col1:
            st.download_button(
                label="Download as Markdown",
                data=result.test_plan_markdown.encode("utf-8"),
                file_name=f"test_plan_{feature_name or 'output'}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with dl_col2:
            try:
                gen = DocxGenerator()
                docx_bytes = gen.generate(result.test_plan_markdown, title=f"Test Plan — {feature_name or 'Output'}")
                st.download_button(
                    label="Download as Word (.docx)",
                    data=docx_bytes,
                    file_name=f"test_plan_{feature_name or 'output'}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            except Exception as exc:
                st.error(f"Word export failed: {exc}")
