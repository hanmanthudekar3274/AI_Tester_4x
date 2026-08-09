# Local Test Case Generator — Implementation Plan

> **Status:** Awaiting `env.md` credentials before build starts.  
> Based on: `finetuned_prompt.md` | Templates: `Templates/test_creater.md`

---

## 1. Final File Structure

```
Local_Testcase_Generator/
├── Src/
│   ├── app.py                  # Screen 1 — Chat UI (entry point)
│   ├── config_store.py         # Read/write persisted settings (JSON)
│   ├── jira_client.py          # Jira REST API — fetch ticket details
│   ├── llm_client.py           # Ollama (primary) + Groq (fallback) calls
│   ├── pages/
│   │   └── settings.py         # Screen 2 — Settings UI
│   ├── requirements.txt
│   ├── .gitignore              # excludes config.json (credentials)
│   ├── finetuned_prompt.md     # (existing)
│   └── plan.md                 # (this file)
├── Templates/
│   ├── test_creater.md         # (existing — reference template)
│   └── testcase_template.md    # (existing — format skeleton)
```

---

## 2. Screen Designs

### Screen 1 — Chat (`app.py`)
| Element | Detail |
|---|---|
| Title bar | "AI Test Case Generator" |
| Chat history | `st.session_state.messages` rendered as chat bubbles |
| Input box | `st.chat_input` — natural language, e.g. `create test cases for QA-102` |
| Send action | Triggers the end-to-end pipeline (parse → fetch → generate → render) |
| Sidebar link | Navigation button to Settings page |

### Screen 2 — Settings (`pages/settings.py`)
| Field | Stored Key |
|---|---|
| Jira Base URL | `jira_url` |
| Jira Email | `jira_email` |
| Jira API Token | `jira_api_token` (masked input) |
| LLM Provider | `llm_provider` (`ollama` / `groq`) |
| Groq API Key | `groq_api_key` (masked input) |

All fields persist to `config.json` (excluded from git) via `config_store.py`.

---

## 3. Data Flow

```
User types: "create test cases for QA-102"
        │
        ▼
app.py  ── regex parse ──► ticket_key = "QA-102"
        │
        ▼
jira_client.py
  GET /rest/api/3/issue/QA-102
  Extracts: summary, description, acceptance_criteria
        │
        ▼
Load Templates/test_creater.md  (template structure)
Merge ticket fields into prompt
        │
        ▼
llm_client.py
  ├─ Try Ollama  http://localhost:11434  model=gemma3:1b
  │    └─ if unavailable / provider=groq ──► Groq API
  └─ Return generated test cases (markdown string)
        │
        ▼
app.py  renders response as chat bubble
```

---

## 4. Module Responsibilities

### `config_store.py`
- `load_config() → dict` — reads `config.json`; returns empty dict if missing
- `save_config(data: dict)` — writes to `config.json`
- `get(key, default=None)` — convenience getter
- Config file location: same directory as `app.py`; added to `.gitignore`

### `jira_client.py`
- `fetch_ticket(ticket_key: str, config: dict) → dict`
  - Calls `GET {jira_url}/rest/api/3/issue/{ticket_key}`
  - Auth: HTTP Basic with `jira_email:jira_api_token`
  - Returns: `{summary, description, acceptance_criteria, priority, issue_type}`
  - Raises `JiraClientError` on auth failure, 404, or network error

### `llm_client.py`
- `generate_test_cases(prompt: str, config: dict) → str`
  - Step 1: if `config["llm_provider"] == "ollama"`, try Ollama first
    - `POST http://localhost:11434/api/generate` with `model=gemma3:1b`
    - On `ConnectionError` or timeout → auto-fallback to Groq, surface warning in chat
  - Step 2 (fallback): call Groq API (`groq` SDK) with `llama3-8b-8192` or equivalent
  - Returns raw markdown string of generated test cases

### `app.py`
- Streamlit entry point; multipage via `pages/` folder
- Session state: `messages` list (role + content)
- Regex to parse Jira key: `r'\b[A-Z]+-\d+\b'`
- Builds the merged prompt:
  ```
  {template content}
  
  --- Jira Ticket: {key} ---
  Summary: {summary}
  Description: {description}
  Acceptance Criteria: {acceptance_criteria}
  ```
- Renders LLM response with `st.chat_message("assistant")`

### `pages/settings.py`
- Loads current config with `config_store.load_config()`
- Form with all fields pre-filled from config
- On Save: calls `config_store.save_config()`; shows success toast

---

## 5. Prompt Construction

The merged prompt sent to the LLM combines:
1. The system persona from `test_creater.md` (Steps 1–5 instructions)
2. The ticket data fetched from Jira
3. Instruction to output in the `TC-001` format from the template

---

## 6. `requirements.txt` (planned)

```
streamlit>=1.35.0
requests>=2.31.0
groq>=0.9.0
```

No further dependencies. Ollama is called via raw `requests` (no SDK needed).

---

## 7. `.gitignore` additions

```
config.json
__pycache__/
*.pyc
.env
env.md
```

---

## 8. Build Sequence (step-by-step, one module at a time)

| Step | Module | Deliverable |
|------|--------|-------------|
| 1 | `config_store.py` | Credential persistence layer |
| 2 | `pages/settings.py` | Settings UI wired to config store |
| 3 | `jira_client.py` | Jira REST fetch + error handling |
| 4 | `llm_client.py` | Ollama call + Groq fallback |
| 5 | `app.py` | Chat UI + full end-to-end pipeline |
| 6 | `requirements.txt` + `.gitignore` | Packaging |

---

## 9. Credentials Needed (from `env.md`)

Before Step 3 (jira_client) can be tested, the following are required:

| Credential | Purpose |
|---|---|
| `JIRA_URL` | Base URL, e.g. `https://yourorg.atlassian.net` |
| `JIRA_EMAIL` | Atlassian account email |
| `JIRA_API_TOKEN` | Atlassian API token |
| `GROQ_API_KEY` | Groq fallback (optional until Ollama confirmed working) |

These will be entered via the Settings screen at runtime — never hardcoded.

---

## 10. Out of Scope

- No authentication/login for the Streamlit app itself (internal tool)
- No database — JSON file config is sufficient
- No Docker or deployment config
- No automated tests (manual QA flow only)
