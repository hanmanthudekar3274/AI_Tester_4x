# Task Plan — Test Plan Creator from Jira ID

> BLAST Protocol 0 — Project Memory Initialized: 2026-08-29
> Discovery answered: 2026-08-29. Blueprint locked.

---

## North Star

A user types "Create a test plan for QA-123" into a chat screen. The agent
fetches that Jira issue, generates a structured test plan grounded entirely in
the issue content, and offers it as a Markdown or DOCX download. No manual
research, no fabricated requirements.

---

## Locked Decisions (from Discovery)

| Decision | Answer | Consequence |
|----------|--------|-------------|
| Jira deployment | Jira Cloud (`*.atlassian.net`) | Basic auth with email + API token. REST API v3. ADF flattener required. |
| Auth fields | Jira URL, Jira email, Jira API token, Groq API key | No password field. Jira Cloud has no password auth. |
| Display name | Cosmetic only | Stamped as author on generated plans. Not used for auth. |
| Default project key | Yes | Lets the user type `123` and have it resolve to `QA-123`. |
| Delivery | Download from UI: Markdown + DOCX | Jira token needs **read scope only**. No write-back, no Confluence, no Zephyr in v1. |
| Secrets storage | `.env`, gitignored, loaded via `python-dotenv` | Settings screen reads and writes `.env`. No plaintext `config.json` holding tokens. |
| LLM provider | Groq | Single provider in v1. Adapter interface still used so Ollama can be added later. |
| Model | `openai/gpt-oss-120b` | Test Connection button confirms the ID resolves against the user key. |
| Chat scope | Test plan generation only | Input must contain a Jira key. No key, the agent asks for one. No general chit-chat fallback. |
| Codebase | Fresh build under `Test-plan-agent-using_BLAST/`, BLAST 3-layer | Logic borrowed from `Local_Test_Generator` but rewritten to satisfy the `LLM.md` invariants. |

---

## Screens

### Screen 1 — Chat (`ui/app.py`)
- `st.chat_input` accepting a natural request containing a Jira key
- Jira key extracted by regex; bare numbers resolved against the default project key
- Progress indicators per pipeline stage: Fetch, Normalize, Generate, Validate
- Rendered test plan with a coverage summary and any coverage gaps surfaced up front
- Download buttons: Markdown, DOCX
- Blocks with a clear message when settings are incomplete, linking to Settings

### Screen 2 — Settings (`ui/pages/settings.py`)
Two cards, each a form with Save and Test Connection buttons and a status pill.

**Jira card**
| Field | Type | Notes |
|-------|------|-------|
| Jira Base URL | text | trailing slash stripped on save |
| Jira Email | text | Atlassian account email |
| Jira API Token | password | read scope is sufficient |
| Default Project Key | text | optional, e.g. `QA` |
| Verify SSL | toggle | default on; off only for corporate proxy with custom CA |

Test Connection: `GET {base_url}/rest/api/3/myself`, reports `displayName`.

**Groq card**
| Field | Type | Notes |
|-------|------|-------|
| Groq API Key | password | |
| Model ID | text | default `openai/gpt-oss-120b` |
| Temperature | slider | 0.0 to 1.0, default 0.2 |

Test Connection: list models to validate the key, then a small completion to
validate the model ID resolves.

**Preferences card**
| Field | Type | Notes |
|-------|------|-------|
| Display Name | text | stamped as plan author |
| Default Output Format | select | Markdown or DOCX |

---

## Phase Checklist

### Protocol 0 — Initialization
- [x] Create `task_plan.md`
- [x] Create `findings.md`
- [x] Create `progress.md`
- [x] Create `LLM.md` (Project Constitution)
- [x] Answer the five Discovery Questions
- [x] Define the Data Schema in `LLM.md`
- [x] Blueprint approved — Protocol 0 halt lifted

### Phase 1 — Blueprint
- [x] Output test plan schema defined in `LLM.md` section 3
- [x] Delivery format decided: Markdown and DOCX download
- [x] LLM provider and model decided: Groq `openai/gpt-oss-120b`
- [x] Jira auth method decided: Cloud Basic auth, email + API token
- [x] Jira field to test plan section mapping recorded in `findings.md`
- [x] Researched reusable code in `Local_Test_Generator` and `Requirement_Analyser_Agent`
- [x] Settings schema locked in `LLM.md` section 9

### Phase 2 — Link
- [x] Scaffold project directories: `architecture/`, `tools/`, `ui/`, `.tmp/`
- [x] Write `.env.example` and `.gitignore`
- [x] Write `requirements.txt` with `groq`, `httpx`, `python-dotenv`, `python-docx` included
- [x] Build `tools/config_store.py` — read and write `.env`, update `os.environ` in process
- [ ] Verify the Jira token against `/rest/api/3/myself`
- [ ] Discover the Acceptance Criteria custom field ID on the live instance
- [ ] Verify the Groq key and that `openai/gpt-oss-120b` resolves
- [ ] Fetch one real issue and save the raw JSON to `.tmp/` for schema confirmation

### Phase 3 — Architect
SOPs first, then the tool each one describes.

- [x] `architecture/jira_fetch_sop.md` then `tools/jira_client.py`
- [x] `architecture/normalization_sop.md` then `tools/normalize_issue.py`
- [x] `architecture/test_plan_generation_sop.md` (contains the system prompt) then `tools/generate_test_plan.py`
- [x] `architecture/validation_sop.md` then `tools/validate_plan.py`
- [x] `architecture/output_formatter_sop.md` then `tools/format_markdown.py` and `tools/format_docx.py`
- [x] `tools/llm_client.py` — Groq adapter behind the `BaseLLM`-style interface
- [x] `tools/pipeline.py` — Layer 2 navigation, wires the stages in fixed order

### Phase 4 — Stylize
- [x] Build `ui/app.py` chat screen
- [x] Build `ui/pages/settings.py` with the three cards above
- [x] Per-stage progress indicators
- [x] Coverage gaps surfaced prominently, not buried at the bottom
- [x] Download buttons for Markdown and DOCX
- [x] `.streamlit/config.toml` theme

### Phase 5 — Trigger
- [x] `streamlit run ui/app.py` as the primary entry point
- [x] CLI: `python -m tools.pipeline --issue QA-123 --format markdown`
- [ ] Deferred to v2: Jira comment write-back, Confluence publishing, Zephyr push, batch sprint mode

---

## Goals

| # | Goal | Priority | Done |
|---|------|----------|------|
| 1 | Fetch a Jira Cloud issue by key with Basic auth | P0 | [x] |
| 2 | Flatten ADF description to plain text | P0 | [x] |
| 3 | Discover the Acceptance Criteria custom field at runtime | P0 | [x] |
| 4 | Generate a test plan matching the `LLM.md` output schema | P0 | [x] |
| 5 | Validate the plan against the schema and assert AC coverage | P0 | [x] |
| 6 | Render Markdown output | P0 | [x] |
| 7 | Chat screen accepting a Jira key | P0 | [x] |
| 8 | Settings screen with working Test Connection for Jira and Groq | P0 | [x] |
| 9 | Secrets in `.env`, never in a committed file | P0 | [x] |
| 10 | Render DOCX output | P1 | [x] |
| 11 | Default project key resolution for bare numbers | P1 | [x] |
| 12 | Jira response caching in `.tmp/cache/` | P1 | [x] |
| 13 | CLI entry point | P2 | [x] |
| 14 | Second LLM provider behind the same adapter | P3 | [ ] |

---

## Known Risks

| # | Risk | Mitigation |
|---|------|-----------|
| 1 | Acceptance Criteria custom field ID is unknown until we hit the live instance | Discover at runtime via `/rest/api/3/field` matching on field **name**, cache the result |
| 2 | `openai/gpt-oss-120b` model ID string is unverified against the live Groq account | Test Connection button validates it before any generation runs |
| 3 | Sibling project disables TLS verification globally | Verify SSL is on by default here, with an explicit opt-out toggle labeled insecure |
| 4 | Model may return prose instead of JSON | Schema validation with one corrective retry, then hard failure. No silent fallback |
| 5 | Issues with an empty description produce a hollow plan | Normalizer flags the gap; generator reports it in `coverage_gaps` rather than inventing content |
