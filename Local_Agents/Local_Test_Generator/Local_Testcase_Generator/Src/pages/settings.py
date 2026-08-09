import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import urllib3
import streamlit as st
import config_store

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Settings — AI Test Case Generator", layout="centered")
st.title("Settings")

cfg = config_store.load_config()

# ── Jira Configuration ──────────────────────────────────────────────────────
st.subheader("Jira Configuration")

with st.form("jira_form"):
    jira_url = st.text_input("Jira Base URL", value=cfg.get("jira_url", ""),
                             placeholder="https://yourorg.atlassian.net")
    jira_email = st.text_input("Jira Email", value=cfg.get("jira_email", ""))
    jira_api_token = st.text_input("Jira API Token", value=cfg.get("jira_api_token", ""),
                                   type="password")
    jira_col1, jira_col2 = st.columns(2)
    with jira_col1:
        save_jira = st.form_submit_button("💾 Save Jira Settings", use_container_width=True)
    with jira_col2:
        test_jira = st.form_submit_button("🔌 Test Jira Connection", use_container_width=True)

if save_jira:
    updated = config_store.load_config()
    updated.update({
        "jira_url": jira_url.strip().rstrip("/"),
        "jira_email": jira_email.strip(),
        "jira_api_token": jira_api_token.strip(),
    })
    config_store.save_config(updated)
    st.success("Jira settings saved.")

if test_jira:
    url = jira_url.strip().rstrip("/")
    email = jira_email.strip()
    token = jira_api_token.strip()
    if not url or not email or not token:
        st.error("Fill in Jira URL, Email, and API Token before testing.")
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
                    data = r.json()
                    display = data.get("displayName") or data.get("emailAddress", "unknown")
                    st.success(f"✅ Jira connected — logged in as **{display}**")
                elif r.status_code == 401:
                    st.error("❌ Authentication failed. Check email and API token.")
                elif r.status_code == 404:
                    st.error("❌ URL not found. Check the Jira Base URL.")
                else:
                    st.error(f"❌ Jira returned {r.status_code}: {r.text[:200]}")
            except requests.exceptions.ConnectionError:
                st.error(f"❌ Cannot reach {url}. Check the URL.")
            except requests.exceptions.Timeout:
                st.error("❌ Connection timed out.")

st.divider()

# ── LLM Configuration ────────────────────────────────────────────────────────
st.subheader("LLM Configuration")

# ── Ollama ───────────────────────────────────────────────────────────────────
with st.form("ollama_form"):
    st.markdown("**Ollama (local)**")
    provider_options = ["ollama", "groq"]
    current_provider = cfg.get("llm_provider", "ollama")
    llm_provider = st.selectbox("Default LLM Provider", provider_options,
                                index=provider_options.index(current_provider)
                                if current_provider in provider_options else 0)
    st.caption(f"Ollama endpoint: `http://localhost:11434` · Model: `llama3.2:latest`")

    save_ollama = st.form_submit_button("💾 Save Provider", use_container_width=False)
    test_ollama = st.form_submit_button("🦙 Test Ollama Connection", use_container_width=False)

if save_ollama:
    updated = config_store.load_config()
    updated["llm_provider"] = llm_provider
    config_store.save_config(updated)
    st.success(f"Default provider set to **{llm_provider}**.")

if test_ollama:
    with st.spinner("Connecting to Ollama…"):
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=8)
            if r.ok:
                models = [m["name"] for m in r.json().get("models", [])]
                if models:
                    st.success(f"✅ Ollama connected — available models: **{', '.join(models)}**")
                else:
                    st.warning("⚠️ Ollama is running but no models are installed.")
            else:
                st.error(f"❌ Ollama returned {r.status_code}.")
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot reach Ollama at http://localhost:11434. Is it running?")
        except requests.exceptions.Timeout:
            st.error("❌ Ollama connection timed out.")

st.divider()

# ── Groq ─────────────────────────────────────────────────────────────────────
with st.form("groq_form"):
    st.markdown("**Groq (cloud fallback)**")
    groq_api_key = st.text_input("Groq API Key", value=cfg.get("groq_api_key", ""),
                                 type="password", placeholder="gsk_…")
    groq_col1, groq_col2 = st.columns(2)
    with groq_col1:
        save_groq = st.form_submit_button("💾 Save Groq Key", use_container_width=True)
    with groq_col2:
        test_groq = st.form_submit_button("🤖 Test Groq Connection", use_container_width=True)

if save_groq:
    updated = config_store.load_config()
    updated["groq_api_key"] = groq_api_key.strip()
    config_store.save_config(updated)
    st.success("Groq API key saved.")

if test_groq:
    key = groq_api_key.strip()
    if not key:
        st.error("Enter a Groq API Key before testing.")
    else:
        with st.spinner("Connecting to Groq…"):
            try:
                import httpx
                from groq import Groq, APIConnectionError as GroqConnectionError
                http_client = httpx.Client(verify=False)
                client = Groq(api_key=key, http_client=http_client)
                resp = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": "ping"}],
                    max_tokens=5,
                )
                st.success(f"✅ Groq connected — model: **{resp.model}**")
            except GroqConnectionError:
                st.error("❌ Cannot reach Groq API. Check your internet connection.")
            except Exception as e:
                st.error(f"❌ Groq error: {e}")
