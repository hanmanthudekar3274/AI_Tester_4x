"""Screen 1 - Chat.

Implements the Screen 1 contract in LLM.md section 9. Scope is test plan
generation only: input must contain a Jira key. There is deliberately no
general-purpose QA chat fallback.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools import config_store, format_docx, pipeline  # noqa: E402

st.set_page_config(page_title="Test Plan Agent", page_icon="🧪", layout="wide")

config_store.init()

ISSUE_KEY_RE = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b", re.IGNORECASE)
BARE_NUMBER_RE = re.compile(r"\b(\d{1,6})\b")

st.session_state.setdefault("history", [])


def extract_issue_key(text: str, config: dict[str, str]) -> tuple[str | None, str | None]:
    """Return (issue_key, error). Resolution order per the Screen 1 contract."""
    match = ISSUE_KEY_RE.search(text or "")
    if match:
        return match.group(1).upper(), None

    default_key = str(config.get("JIRA_DEFAULT_PROJECT_KEY", "")).strip().upper()
    number = BARE_NUMBER_RE.search(text or "")
    if number and default_key:
        return f"{default_key}-{number.group(1)}", None

    if number and not default_key:
        return None, (
            f"I found the number {number.group(1)} but no project key. "
            "Type the full key like QA-123, or set a Default Project Key in Settings."
        )

    return None, (
        "I need a Jira issue key to work from. Try: "
        "*Create a test plan for QA-123*."
    )


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------

with st.sidebar:
    st.title("🧪 Test Plan Agent")
    st.caption("Generates a test plan from a Jira issue. Grounded in the issue, never invented.")
    try:
        st.page_link("pages/settings.py", label="Settings", icon="⚙️")
    except Exception:
        st.caption("Settings page: ui/pages/settings.py")

    config = config_store.load_config()
    missing = config_store.missing_required(config)
    if missing:
        st.error("Not configured yet. Missing: " + ", ".join(missing))
    else:
        st.success("Ready")
        st.caption(f"Model: `{config.get('GROQ_MODEL', '')}`")
        default_key = config.get("JIRA_DEFAULT_PROJECT_KEY", "")
        if default_key:
            st.caption(f"Default project: `{default_key}`")

    if st.session_state.history and st.button("Clear conversation"):
        st.session_state.history = []
        st.rerun()


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def render_result(result: dict, key_suffix: str) -> None:
    validation = result["validation"]
    stats = validation.get("stats", {})
    plan = result["plan"]

    columns = st.columns(4)
    columns[0].metric("Test cases", stats.get("test_case_count", 0))
    columns[1].metric("Criteria covered", f"{stats.get('ac_covered', 0)}/{stats.get('ac_count', 0)}")
    columns[2].metric("Coverage", f"{stats.get('coverage_pct', 0)}%")
    columns[3].metric("Inferred", stats.get("inferred_count", 0))

    # Gaps first, above the plan body. A plan the user must not trust blindly
    # must not look complete at a glance.
    gaps = plan.get("coverage_gaps") or []
    if gaps:
        with st.container(border=True):
            st.warning(
                "**Coverage gaps.** The issue did not carry enough detail to test "
                "these points. They need a decision before the plan is complete."
            )
            for gap in gaps:
                st.markdown(f"- {gap}")

    warnings = validation.get("warnings") or []
    if warnings:
        with st.expander(f"Quality warnings ({len(warnings)})"):
            for warning in warnings:
                st.markdown(f"- {warning}")

    download_columns = st.columns(3)
    download_columns[0].download_button(
        "Download Markdown",
        data=result["markdown"],
        file_name=f"{result['issue_key']}-test-plan.md",
        mime="text/markdown",
        key=f"md_{key_suffix}",
        use_container_width=True,
    )
    try:
        docx_bytes = format_docx.render(plan, validation, model=result.get("model"))
        download_columns[1].download_button(
            "Download DOCX",
            data=docx_bytes,
            file_name=f"{result['issue_key']}-test-plan.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"docx_{key_suffix}",
            use_container_width=True,
        )
    except RuntimeError as exc:
        download_columns[1].caption(str(exc))

    download_columns[2].download_button(
        "Download JSON",
        data=json.dumps(plan, indent=2, ensure_ascii=False),
        file_name=f"{result['issue_key']}-test-plan.json",
        mime="application/json",
        key=f"json_{key_suffix}",
        use_container_width=True,
    )

    st.divider()
    st.markdown(result["markdown"])

    usage = result.get("usage") or []
    total_tokens = sum(u.get("total_tokens") or 0 for u in usage)
    latency = sum(u.get("latency_seconds") or 0 for u in usage)
    st.caption(
        f"Model {result.get('model')} · {result.get('attempts')} attempt(s) · "
        f"{total_tokens} tokens · {latency:.1f}s"
    )


# --------------------------------------------------------------------------
# History replay
# --------------------------------------------------------------------------

st.title("Test Plan Agent")

if not st.session_state.history:
    st.info(
        "Ask for a test plan by Jira issue key. For example: "
        "**Create a test plan for QA-123**"
    )

for index, entry in enumerate(st.session_state.history):
    with st.chat_message(entry["role"]):
        if entry.get("text"):
            st.markdown(entry["text"])
        if entry.get("result"):
            render_result(entry["result"], key_suffix=str(index))


# --------------------------------------------------------------------------
# Input
# --------------------------------------------------------------------------

prompt = st.chat_input("e.g. Create a test plan for QA-123")

if prompt:
    st.session_state.history.append({"role": "user", "text": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        config = config_store.load_config()

        missing = config_store.missing_required(config)
        if missing:
            message = (
                "I cannot generate a plan yet. These settings are missing: **"
                + ", ".join(missing)
                + "**. Open the Settings page to add them."
            )
            st.error(message)
            try:
                st.page_link("pages/settings.py", label="Go to Settings", icon="⚙️")
            except Exception:
                pass
            st.session_state.history.append({"role": "assistant", "text": message})
        else:
            issue_key, error = extract_issue_key(prompt, config)
            if error:
                st.markdown(error)
                st.session_state.history.append({"role": "assistant", "text": error})
            else:
                status = st.status(f"Working on {issue_key}", expanded=True)

                def on_stage(stage: str, message: str) -> None:
                    status.write(f"**{stage}** — {message}")

                try:
                    result = pipeline.run(issue_key, config, on_stage=on_stage)
                    status.update(label=f"Plan ready for {issue_key}", state="complete")
                    render_result(result, key_suffix=str(len(st.session_state.history)))
                    st.session_state.history.append({
                        "role": "assistant",
                        "text": f"Test plan for **{result['issue_key']}**:",
                        "result": result,
                    })
                except pipeline.PipelineError as exc:
                    status.update(label=f"Failed at the {exc.stage} stage", state="error")
                    st.error(exc.detail)
                    if exc.stage in ("fetch", "preflight"):
                        try:
                            st.page_link("pages/settings.py", label="Check Settings", icon="⚙️")
                        except Exception:
                            pass
                    st.session_state.history.append({
                        "role": "assistant",
                        "text": f"**Failed at the {exc.stage} stage.** {exc.detail}",
                    })
