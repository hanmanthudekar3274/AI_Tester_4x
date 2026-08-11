import re
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

import config_store
import jira_client
import llm_client
import ui_styles

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Testcase Generator",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded",
)
ui_styles.inject_styles()

# ── Quick input from welcome-screen chip buttons ───────────────────────────────
quick_input: str | None = st.session_state.pop("quick_input", None)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"""
        <div class="logo-wrap">
          <div class="logo-glow">{ui_styles.logo_svg(76)}</div>
          <div class="brand-name">AI Testcase Generator</div>
          <div class="brand-sub">AI-Powered Test Generator</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown('<div class="provider-label">LLM Provider</div>', unsafe_allow_html=True)

    saved_provider = config_store.get("llm_provider", "ollama")
    provider = st.radio(
        "Select LLM",
        options=["ollama", "groq"],
        index=0 if saved_provider == "ollama" else 1,
        format_func=lambda x: "🦙 Ollama (local)" if x == "ollama" else "☁️ Groq (cloud)",
        key="llm_provider_radio",
        label_visibility="collapsed",
    )

    if provider != saved_provider:
        cfg_update = config_store.load_config()
        cfg_update["llm_provider"] = provider
        config_store.save_config(cfg_update)

    if provider == "ollama":
        st.caption("Model: `llama3.2:latest` · `localhost:11434`")
    else:
        st.caption("Model: `llama-3.1-8b-instant` · Groq cloud API")

    st.divider()
    st.page_link("pages/settings.py", label="⚙️  Settings", icon=None)

# ── Page header ───────────────────────────────────────────────────────────────
provider_label = "🦙 Ollama" if provider == "ollama" else "☁️ Groq"
st.markdown(
    f"""
    <div class="page-hdr">
      <div class="logo-glow">{ui_styles.logo_svg(42)}</div>
      <div>
        <div class="page-hdr-title">AI Testcase Generator</div>
        <div class="page-hdr-sub">
          Active&nbsp;provider:&nbsp;<strong style="color:#a78bfa">{provider_label}</strong>
          &nbsp;&nbsp;·&nbsp;&nbsp;Type a Jira ticket key to generate test cases instantly
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []


# ── Helpers ───────────────────────────────────────────────────────────────────

def _esc(text: str) -> str:
    import html as _html
    return _html.escape(str(text))


def _extract_section(body: str, *names: str) -> str:
    for name in names:
        m = re.search(
            rf"(?:^|\n){re.escape(name)}:\s*(.*?)(?=\n[A-Za-z][^\n]*:|\Z)",
            body, re.DOTALL | re.IGNORECASE,
        )
        if m:
            return m.group(1).strip()
    return ""


def _extract_steps(body: str) -> list[dict]:
    m = re.search(
        r"(?:Steps(?:\s+and\s+Test\s+Data)?|Steps):\s*\n(.*?)(?=\n[A-Za-z][^\n]*:|\Z)",
        body, re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return []
    step_lines = re.findall(r"^\s*\d+\.\s*(.+)$", m.group(1), re.MULTILINE)
    steps = []
    for line in step_lines:
        line = line.strip()
        if re.search(r"\|\s*Test\s*Data\s*:", line, re.IGNORECASE):
            parts = re.split(r"\|\s*Test\s*Data\s*:\s*", line, 1, flags=re.IGNORECASE)
            action = re.sub(r"^Step\s*:\s*", "", parts[0].strip(), flags=re.IGNORECASE)
            data = parts[1].strip() if len(parts) > 1 else ""
        else:
            action = line
            data = ""
        steps.append({"action": action, "data": data})
    return steps


def _parse_test_cases(response: str) -> list[dict]:
    parts = re.split(r"(?=Test Case \d+:)", response.strip())
    parts = [p.strip() for p in parts if p.strip()]
    if not parts or not re.match(r"Test Case \d+:", parts[0]):
        return []
    result = []
    for i, block in enumerate(parts):
        lines = block.split("\n")
        m = re.match(r"Test Case (\d+):\s*(.*)", lines[0])
        body = "\n".join(lines[1:])
        result.append({
            "id": m.group(1) if m else str(i + 1),
            "title": m.group(2).strip() if m else f"Test Case {i + 1}",
            "description": _extract_section(body, "Description", "Summary"),
            "preconditions": _extract_section(body, "Preconditions", "Precondition"),
            "steps": _extract_steps(body),
            "expected_outcome": _extract_section(body, "Expected Outcome", "Expected Result", "Pass Criteria"),
        })
    return result


def _build_table_html(test_cases: list[dict]) -> str:
    rows = ""
    for tc in test_cases:
        steps_html = ""
        for j, step in enumerate(tc["steps"], 1):
            data_html = ""
            if step["data"] and step["data"].strip().lower() not in ("n/a", "none", "-", ""):
                data_html = (
                    f'<div class="step-data">'
                    f'<span class="step-data-lbl">Data:</span> {_esc(step["data"])}'
                    f'</div>'
                )
            steps_html += (
                f'<div class="step-item">'
                f'<span class="step-badge">{j}</span>'
                f'<div class="step-body">'
                f'<div class="step-action">{_esc(step["action"])}</div>'
                f'{data_html}'
                f'</div></div>'
            )

        pre_html = ""
        if tc["preconditions"]:
            pre_html = (
                f'<div class="tc-pre">'
                f'<span class="tc-pre-lbl">Pre:</span> {_esc(tc["preconditions"])}'
                f'</div>'
            )

        rows += (
            f'<tr class="tc-row">'
            f'<td class="td-id"><div class="tc-num">TC-{_esc(tc["id"])}</div></td>'
            f'<td class="td-desc">'
            f'<div class="tc-ttl">{_esc(tc["title"])}</div>'
            f'<div class="tc-sum">{_esc(tc["description"])}</div>'
            f'{pre_html}</td>'
            f'<td class="td-steps">{steps_html or "<span class=\"no-steps\">—</span>"}</td>'
            f'<td class="td-outcome">{_esc(tc["expected_outcome"])}</td>'
            f'</tr>'
        )

    return (
        '<div class="tc-table-wrap">'
        '<table class="tc-table">'
        '<thead><tr>'
        '<th class="th-id">TC ID</th>'
        '<th class="th-desc">Description</th>'
        '<th class="th-steps">Steps &amp; Test Data</th>'
        '<th class="th-outcome">Expected Outcome</th>'
        '</tr></thead>'
        f'<tbody>{rows}</tbody>'
        '</table></div>'
    )


def _render_test_cases(response: str, ticket_key: str, btn_key: str = "dl") -> None:
    test_cases = _parse_test_cases(response)

    if not test_cases:
        st.markdown(response)
        return

    count = len(test_cases)
    st.markdown(
        f'<div class="tc-section">'
        f'<span class="tc-section-title">📋 Generated Test Cases</span>'
        f'<span class="tc-badge">{count} test case{"s" if count != 1 else ""}&nbsp;·&nbsp;{ticket_key}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(_build_table_html(test_cases), unsafe_allow_html=True)
    st.download_button(
        label="📥 Download as Markdown",
        data=response,
        file_name=f"test_cases_{ticket_key}.md",
        mime="text/markdown",
        key=btn_key,
    )


def _render_message(msg: dict, idx: int) -> None:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            _render_test_cases(
                msg["content"],
                msg.get("ticket_key", ""),
                btn_key=f"dl_hist_{idx}",
            )


def _build_prompt(ticket: dict) -> str:
    return f"""You are a QA engineer. Generate structured test cases for the Jira ticket below.

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
- Use EXACTLY these section labels for every test case:

Test Case [N]: [Short title]
Description: [One sentence describing what is being tested]
Preconditions: [What must be true before the test starts]
Steps and Test Data:
  1. Step: [Action the tester performs] | Test Data: [specific input value or N/A]
  2. Step: [Action] | Test Data: [specific value or N/A]
  3. Step: [Action] | Test Data: [specific value or N/A]
Expected Outcome: [Specific measurable result that confirms the test passed]

- Provide concrete Test Data values (e.g. email="admin@test.com", amount=0, query="<script>alert(1)</script>").
- Cover: Happy Path, Negative scenarios, Edge cases, and Input validation.
- Do not explain yourself. Output only the test cases.
"""


# ── Message history ───────────────────────────────────────────────────────────
if not st.session_state.messages:
    # Welcome hero
    st.markdown(
        f"""
        <div class="welcome-hero">
          <div class="logo-glow" style="display:inline-block">
            {ui_styles.logo_svg(78)}
          </div>
          <h2>Welcome to AI Testcase Generator</h2>
          <p>Generate comprehensive test cases from Jira tickets in seconds.<br/>
             Just provide a ticket key — let the AI do the rest.</p>
          <div class="welcome-divider"></div>
          <div class="chip-hint">Try a sample ticket key:</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, _space = st.columns([1, 1, 1, 4])
    with col1:
        if st.button("QA-102", key="chip1"):
            st.session_state.quick_input = "create test cases for QA-102"
            st.rerun()
    with col2:
        if st.button("PROJ-456", key="chip2"):
            st.session_state.quick_input = "create test cases for PROJ-456"
            st.rerun()
    with col3:
        if st.button("BUG-789", key="chip3"):
            st.session_state.quick_input = "create test cases for BUG-789"
            st.rerun()
else:
    for idx, msg in enumerate(st.session_state.messages):
        _render_message(msg, idx)

# ── Chat input ────────────────────────────────────────────────────────────────
user_input = st.chat_input("e.g. create test cases for QA-102")
effective_input: str | None = quick_input or user_input

# ── Processing ────────────────────────────────────────────────────────────────
if effective_input:
    st.session_state.messages.append({"role": "user", "content": effective_input})
    with st.chat_message("user"):
        st.markdown(effective_input)

    # Parse ticket key
    match = re.search(r"\b([A-Z]+-\d+)\b", effective_input)
    if not match:
        reply = (
            "I couldn't find a Jira ticket key in your message. "
            "Try something like: `create test cases for QA-102`"
        )
        st.session_state.messages.append({"role": "assistant", "content": reply, "ticket_key": ""})
        with st.chat_message("assistant"):
            st.info(reply)
        st.stop()

    ticket_key = match.group(1)
    cfg = config_store.load_config()

    missing = [f for f in ("jira_url", "jira_email", "jira_api_token") if not cfg.get(f)]
    if missing:
        reply = (
            f"Jira credentials are not configured ({', '.join(missing)} missing). "
            "Please go to **⚙️ Settings** and fill them in."
        )
        st.session_state.messages.append({"role": "assistant", "content": reply, "ticket_key": ""})
        with st.chat_message("assistant"):
            st.warning(reply)
        st.stop()

    with st.chat_message("assistant"):
        anim = st.empty()

        # ── Stage 1: Fetching Jira ticket ─────────────────────────────────────
        anim.markdown(ui_styles.fetch_anim_html(ticket_key), unsafe_allow_html=True)
        try:
            ticket = jira_client.fetch_ticket(ticket_key, cfg)
        except jira_client.JiraClientError as e:
            anim.empty()
            err = f"Jira error: {e}"
            st.error(err)
            st.session_state.messages.append({"role": "assistant", "content": err, "ticket_key": ""})
            st.stop()

        # ── Stage 2: Generating test cases ────────────────────────────────────
        active_label = "🦙 Ollama" if provider == "ollama" else "☁️ Groq"
        anim.markdown(ui_styles.generate_anim_html(active_label), unsafe_allow_html=True)
        try:
            response = llm_client.generate_test_cases(_build_prompt(ticket), cfg)
        except RuntimeError as e:
            anim.empty()
            err = str(e)
            st.error(err)
            st.session_state.messages.append({"role": "assistant", "content": err, "ticket_key": ""})
            st.stop()

        # ── Stage 3: Render results ───────────────────────────────────────────
        anim.empty()
        _render_test_cases(
            response,
            ticket_key,
            btn_key=f"dl_new_{len(st.session_state.messages)}",
        )

    st.session_state.messages.append(
        {"role": "assistant", "content": response, "ticket_key": ticket_key}
    )
