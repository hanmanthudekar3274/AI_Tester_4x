# Analyzer Agent — Application Design Plan

**Version:** 1.0  
**Author:** Hanmant Hudekar  
**Date:** 2026-08-12

---

## 1. Overview

The Analyzer Agent is an AI-powered QA agent that reads user provided JIRA id  requirements and discussions from requirments comments, analyzes them using a local or cloud LLM, and produces a structured, IEEE 829-aligned test plan.

---

## 1a. User Interaction Pattern

The agent is driven by natural-language requests. A user simply tells the agent which Jira story to analyze:

> **Example:** "Analyze jira story AAA-50"

The agent then:
1. Fetches the Jira story (AAA-50) — title, description, acceptance criteria, comments
2. Pulls linked Confluence pages and Slack threads (if configured)
3. Runs the 4-step pipeline (Fuse → Extract → Analyze → Generate)
4. Returns a complete, IEEE 829-aligned test plan to the user

---

## 2. Goals

- Reduce test planning time by 60–70% through AI-assisted analysis
- Eliminate missed requirements by fusing data from Jira, Confluence, Slack, and file uploads into a single context
- Produce consistent, reviewable test plans in both Markdown and Word formats
- Work offline (via Ollama) or at cloud speed (via Groq) — user's choice

---

## 3. Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        ANALYZER AGENT                                │
│                                                                      │
│  ┌─────────────┐   ┌─────────────┐   ┌──────────────┐   ┌────────┐ │
│  │  DATA LAYER │   │  LLM LAYER  │   │  AGENT CORE  │   │  UI    │ │
│  │             │   │             │   │              │   │        │ │
│  │ Jira        │   │ OllamaLLM   │   │ AnalyzerAgent│   │Streamlit│ │
│  │ Confluence  │──▶│    OR       │──▶│  Pipeline:   │──▶│        │ │
│  │ Slack       │   │ GroqLLM     │   │  1. Fuse     │   │ Step 1 │ │
│  │ File/Text   │   │             │   │  2. Extract  │   │ Step 2 │ │
│  └─────────────┘   │ LLMRouter   │   │  3. Analyze  │   │ Step 3 │ │
│                    │ (toggle)    │   │  4. Generate │   │        │ │
│                    └─────────────┘   └──────────────┘   └────────┘ │
│                                              │                      │
│                                    ┌─────────▼─────────┐           │
│                                    │   OUTPUT LAYER    │           │
│                                    │  Markdown (UI)    │           │
│                                    │  Word (.docx)     │           │
│                                    └───────────────────┘           │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. Technology Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| UI | Streamlit (Python) | Fast to build, no frontend knowledge needed, easy to deploy internally |
| AI — Local | Ollama | Free, offline, privacy-safe; ideal for sensitive internal docs |
| AI — Cloud | Groq API | Fast inference, large context window, free tier available |
| Jira / Confluence | Atlassian REST API v3 | Official API, supports ADF parsing |
| Slack | Slack Web API | Bot token, reads channels and threads |
| Word export | python-docx | Full formatting control, no Office dependency |
| PDF parsing | pypdf | Lightweight, no binary dependencies |
| Language | Python 3.11+ | All libraries available, Streamlit-native |

---

## 5. Project Structure

```
analyzer-agent/
│
├── Analyzer.md              ← Agent capability spec (RICE POT prompts)
├── plan.md                  ← This file — application design plan
├── app.py                   ← Streamlit UI (3-step wizard)
├── requirements.txt         ← Python dependencies
├── .env.example             ← Environment variable template
│
├── llm/                     ← LLM abstraction layer
│   ├── base_llm.py          ← Abstract interface
│   ├── ollama_llm.py        ← Ollama REST client
│   ├── groq_llm.py          ← Groq SDK client
│   └── llm_router.py        ← Toggle logic (ONE model at a time)
│
├── connectors/              ← Data source connectors
│   ├── jira_connector.py    ← Jira REST API (issues, comments, epics, sprints)
│   ├── confluence_connector.py ← Confluence pages + inline comments
│   ├── slack_connector.py   ← Channel messages + thread replies
│   └── text_connector.py    ← File upload (.txt/.md/.pdf/.docx) + paste
│
├── agents/
│   └── analyzer_agent.py    ← 4-step pipeline (Fuse → Extract → Analyze → Generate)
│
├── prompts/
│   └── test_plan_prompts.py ← RICE POT-structured system + task prompts
│
└── output/
    └── docx_generator.py    ← Markdown → Word document converter
```

---

## 6. Core Pipeline — Step by Step

### Step 1: COLLECT (UI Layer)
User connects sources via the Streamlit sidebar (credentials) and Step 1 tab (what to fetch). Each connector fetches data and converts it to a plain-text block. All blocks are stored in Streamlit session state.

### Step 2: FUSE (Agent Core)
All text blocks are merged into a single `unified_context` string. Token budget is managed (max ~12,000 tokens per LLM call) to stay within model limits.

### Step 3: EXTRACT REQUIREMENTS (LLM Call 1)
The requirements extraction prompt (RICE POT) is sent to the active LLM. Output: structured JSON with functional, non-functional, and flagged requirements.

### Step 4: ANALYZE DISCUSSIONS (LLM Call 2)
The discussion analysis prompt is sent to the active LLM. Output: JSON with decisions, open questions, risks, and assumptions.

### Step 5: GENERATE TEST PLAN (LLM Call 3)
The test plan prompt is sent with the structured outputs from Steps 3 and 4. Output: complete Markdown test plan with 12 sections.

### Step 6: RENDER & EXPORT
The test plan is rendered in the Streamlit UI with metrics dashboard. User downloads as Markdown or Word (.docx).

---

## 7. LLM Router — Toggle Logic

```
User enables Ollama only  →  Uses Ollama
User enables Groq only    →  Uses Groq
User enables both         →  Groq wins, warning shown in UI
User enables neither      →  Error shown, pipeline blocked
```

The router is hot-reloadable — changing the toggle in the sidebar instantly reconfigures the active backend without restarting the app.

**Why two models?**
- **Ollama**: No internet, no API costs, private data stays local. Slower.
- **Groq**: Cloud speed, larger context, handles long Confluence pages better. Requires API key.

---

## 8. RICE POT Prompts — Summary

Three prompts drive the agent (full text in `Analyzer.md` and `prompts/test_plan_prompts.py`):

| Prompt | Purpose | Output |
|--------|---------|--------|
| Requirements Extraction | Parse raw context → testable requirements | JSON |
| Discussion Analysis | Parse discussions → decisions, risks, questions | JSON |
| Test Plan Generation | Combine analysis → full IEEE 829 test plan | Markdown |

Each prompt follows RICE POT: Role → Instructions → Context → Examples → Parameters → Output format → Task.

---

## 9. UI — 3-Step Wizard

| Tab | Purpose |
|-----|---------|
| Step 1: Collect Data | Fetch from Jira / Confluence / Slack / file. Shows collected blocks with preview. |
| Step 2: Configure & Run | Set feature name, product, release, team size, timeline. Readiness checklist. Run button. |
| Step 3: Test Plan | Metrics dashboard, extracted requirements, discussion signals, full plan, download buttons. |

---

## 10. Setup Instructions

### Prerequisites
```bash
pip install streamlit requests groq python-docx pypdf pypdf2 python-dotenv
# For Ollama: install from https://ollama.com then run: ollama pull llama3.2
```

### Run the app
```bash
cd analyzer-agent
streamlit run app.py
```

### Environment variables (copy from .env.example)
```
LLM_OLLAMA_ENABLED=true
OLLAMA_MODEL=llama3.2
LLM_GROQ_ENABLED=false
GROQ_API_KEY=your_key
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=you@company.com
JIRA_API_TOKEN=your_token
CONFLUENCE_BASE_URL=https://yourcompany.atlassian.net/wiki
SLACK_BOT_TOKEN=xoxb-...
```

---

## 11. Future Enhancements

| Enhancement | Priority | Notes |
|-------------|----------|-------|
| Write test plan back to Confluence | High | Auto-create a Confluence page from the output |
| Jira ticket creation from flagged requirements | High | Auto-file clarification tickets |
| TestRail / Xray export (JSON) | Medium | Downstream test case import |
| Streaming LLM output | Medium | Show test plan being written in real-time |
| Multi-language test plans | Low | i18n support for non-English teams |
| Vector memory (RAG) | Low | Remember previous test plans for consistency |

---

## 12. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Ollama too slow for large context | Medium | Medium | Fallback to Groq, or summarize input before sending |
| Jira API token expires | Low | High | Clear error message + guide to regenerate token |
| LLM hallucinates requirements | Medium | High | Agent only extracts — never infers; prompt includes explicit rule |
| Confluence HTML parsing incomplete | Medium | Medium | Strip + fallback to raw text; user can always paste |
| Slack bot not in channel | Medium | Medium | Friendly error with fix instructions |