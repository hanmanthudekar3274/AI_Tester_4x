import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import urllib3
import streamlit as st

import config_store
import ui_styles

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Settings — AI Testcase Generator",
    layout="centered",
    page_icon="⚙️",
)
ui_styles.inject_styles()

# ── Sidebar brand ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"""
        <div class="logo-wrap">
          <div class="logo-glow">{ui_styles.logo_svg(64)}</div>
          <div class="brand-name">AI Testcase Generator</div>
          <div class="brand-sub">AI-Powered Test Generator</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
    st.page_link("app.py", label="💬  Chat", icon=None)

# ── Session state for connection status badges ────────────────────────────────
if "jira_status"   not in st.session_state: st.session_state.jira_status   = "untested"
if "ollama_status" not in st.session_state: st.session_state.ollama_status = "untested"
if "groq_status"   not in st.session_state: st.session_state.groq_status   = "untested"

cfg = config_store.load_config()


def _status_pill(status: str) -> str:
    labels = {"connected": "Connected", "failed": "Failed", "untested": "Not tested"}
    return f'<span class="status-pill {status}">{labels.get(status, status)}</span>'


# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="page-hdr">
      <div class="logo-glow">{ui_styles.logo_svg(38)}</div>
      <div>
        <div class="page-hdr-title">Settings</div>
        <div class="page-hdr-sub">Configure Jira integration &amp; LLM connections</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# JIRA CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    f"""
    <div class="sc">
      <div class="sc-title">
        <div class="sc-name">🔗 Jira Configuration</div>
        {_status_pill(st.session_state.jira_status)}
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("jira_form"):
    jira_url = st.text_input(
        "Jira Base URL",
        value=cfg.get("jira_url", ""),
        placeholder="https://yourorg.atlassian.net",
    )
    jira_email = st.text_input(
        "Jira Email",
        value=cfg.get("jira_email", ""),
        placeholder="you@company.com",
    )
    jira_api_token = st.text_input(
        "Jira API Token",
        value=cfg.get("jira_api_token", ""),
        type="password",
        placeholder="ATATT3x…",
    )

    col1, col2 = st.columns(2)
    with col1:
        save_jira = st.form_submit_button("💾  Save Jira Settings", use_container_width=True)
    with col2:
        test_jira = st.form_submit_button("🔌  Test Connection", use_container_width=True)

if save_jira:
    updated = config_store.load_config()
    updated.update({
        "jira_url":       jira_url.strip().rstrip("/"),
        "jira_email":     jira_email.strip(),
        "jira_api_token": jira_api_token.strip(),
    })
    config_store.save_config(updated)
    st.toast("✅ Jira settings saved", icon="💾")

if test_jira:
    url   = jira_url.strip().rstrip("/")
    email = jira_email.strip()
    token = jira_api_token.strip()
    if not url or not email or not token:
        st.error("Fill in Jira URL, Email, and API Token before testing.")
        st.session_state.jira_status = "failed"
    else:
        with st.spinner("Connecting to Jira…"):
            try:
                r = requests.get(
                    f"{url}/rest/api/3/myself",
                    auth=(email, token),
                    timeout=10,
                    verify=False,
                )
                if r.status_code == 200:
                    data    = r.json()
                    display = data.get("displayName") or data.get("emailAddress", "unknown")
                    st.success(f"Connected — logged in as **{display}**")
                    st.session_state.jira_status = "connected"
                elif r.status_code == 401:
                    st.error("Authentication failed. Check email and API token.")
                    st.session_state.jira_status = "failed"
                elif r.status_code == 404:
                    st.error("URL not found. Check the Jira Base URL.")
                    st.session_state.jira_status = "failed"
                else:
                    st.error(f"Jira returned {r.status_code}: {r.text[:200]}")
                    st.session_state.jira_status = "failed"
            except requests.exceptions.ConnectionError:
                st.error(f"Cannot reach {url}. Check the URL.")
                st.session_state.jira_status = "failed"
            except requests.exceptions.Timeout:
                st.error("Connection timed out.")
                st.session_state.jira_status = "failed"

# ══════════════════════════════════════════════════════════════════════════════
# LLM CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<br>", unsafe_allow_html=True)

col_ollama, col_groq = st.columns(2)

# ── Ollama card ───────────────────────────────────────────────────────────────
with col_ollama:
    st.markdown(
        f"""
        <div class="sc">
          <div class="sc-title">
            <div class="sc-name">🦙 Ollama&nbsp;<span style="font-size:0.72rem;color:#64748b;font-weight:400">(local)</span></div>
            {_status_pill(st.session_state.ollama_status)}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Endpoint: `http://localhost:11434`  \nModel: `llama3.2:latest`")
    with st.form("ollama_form"):
        provider_options  = ["ollama", "groq"]
        current_provider  = cfg.get("llm_provider", "ollama")
        llm_provider = st.selectbox(
            "Default Provider",
            provider_options,
            index=provider_options.index(current_provider)
            if current_provider in provider_options else 0,
            format_func=lambda x: "🦙 Ollama" if x == "ollama" else "☁️ Groq",
        )
        c1, c2 = st.columns(2)
        with c1:
            save_ollama = st.form_submit_button("💾 Save", use_container_width=True)
        with c2:
            test_ollama = st.form_submit_button("🔗 Test", use_container_width=True)

    if save_ollama:
        updated = config_store.load_config()
        updated["llm_provider"] = llm_provider
        config_store.save_config(updated)
        st.toast(f"✅ Default provider set to **{llm_provider}**", icon="💾")

    if test_ollama:
        with st.spinner("Connecting to Ollama…"):
            try:
                r = requests.get("http://localhost:11434/api/tags", timeout=8)
                if r.ok:
                    models = [m["name"] for m in r.json().get("models", [])]
                    if models:
                        st.success(f"Connected — models: **{', '.join(models)}**")
                        st.session_state.ollama_status = "connected"
                    else:
                        st.warning("Ollama running but no models installed.")
                        st.session_state.ollama_status = "connected"
                else:
                    st.error(f"Ollama returned {r.status_code}.")
                    st.session_state.ollama_status = "failed"
            except requests.exceptions.ConnectionError:
                st.error("Cannot reach Ollama at `http://localhost:11434`.")
                st.session_state.ollama_status = "failed"
            except requests.exceptions.Timeout:
                st.error("Ollama connection timed out.")
                st.session_state.ollama_status = "failed"

# ── Groq card ─────────────────────────────────────────────────────────────────
with col_groq:
    st.markdown(
        f"""
        <div class="sc">
          <div class="sc-title">
            <div class="sc-name">☁️ Groq&nbsp;<span style="font-size:0.72rem;color:#64748b;font-weight:400">(cloud)</span></div>
            {_status_pill(st.session_state.groq_status)}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Model: `llama-3.1-8b-instant`  \nRequires a Groq API key")
    with st.form("groq_form"):
        groq_api_key = st.text_input(
            "Groq API Key",
            value=cfg.get("groq_api_key", ""),
            type="password",
            placeholder="gsk_…",
        )
        c1, c2 = st.columns(2)
        with c1:
            save_groq = st.form_submit_button("💾 Save", use_container_width=True)
        with c2:
            test_groq = st.form_submit_button("🔗 Test", use_container_width=True)

    if save_groq:
        updated = config_store.load_config()
        updated["groq_api_key"] = groq_api_key.strip()
        config_store.save_config(updated)
        st.toast("✅ Groq API key saved", icon="💾")

    if test_groq:
        key = groq_api_key.strip()
        if not key:
            st.error("Enter a Groq API key before testing.")
            st.session_state.groq_status = "failed"
        else:
            with st.spinner("Connecting to Groq…"):
                try:
                    import httpx
                    from groq import Groq, APIConnectionError as GroqConnectionError
                    http_client = httpx.Client(verify=False)
                    client      = Groq(api_key=key, http_client=http_client)
                    resp = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": "ping"}],
                        max_tokens=5,
                    )
                    st.success(f"Connected — model: **{resp.model}**")
                    st.session_state.groq_status = "connected"
                except GroqConnectionError:
                    st.error("Cannot reach Groq API. Check your internet connection.")
                    st.session_state.groq_status = "failed"
                except Exception as e:
                    st.error(f"Groq error: {e}")
                    st.session_state.groq_status = "failed"
