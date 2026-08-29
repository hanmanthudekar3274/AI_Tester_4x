# Findings — Jira API Research

> Last updated: 2026-08-29 | Protocol 0 — Research Phase

---

## 1. Jira REST API — Issue Fetch

### Endpoint

```
GET /rest/api/3/issue/{issueIdOrKey}
```

Full URL (Jira Cloud):
```
https://{domain}.atlassian.net/rest/api/3/issue/{ISSUE_KEY}
```

### Authentication

**Jira Cloud — API Token (recommended)**
- Generate at: https://id.atlassian.com/manage-profile/security/api-tokens
- Auth method: HTTP Basic Auth — `email:api_token` encoded as Base64

**Jira Server / Data Center**
- Personal Access Token (PAT): `Authorization: Bearer {PAT}`
- Or Basic Auth with username:password (legacy, not recommended)

---

## 2. curl Examples

### Fetch Issue (Cloud)
```bash
curl -u "your-email@domain.com:YOUR_API_TOKEN" \
  -H "Accept: application/json" \
  "https://your-domain.atlassian.net/rest/api/3/issue/PROJECT-123"
```

### Fetch Issue with Specific Fields Only
```bash
curl -u "your-email@domain.com:YOUR_API_TOKEN" \
  -H "Accept: application/json" \
  "https://your-domain.atlassian.net/rest/api/3/issue/PROJECT-123?fields=summary,description,issuetype,priority,status,assignee,reporter,labels,components,subtasks,issuelinks,comment,attachment,customfield_10016"
```

### Fetch Issue (Server/DC with PAT)
```bash
curl -H "Authorization: Bearer YOUR_PAT" \
  -H "Accept: application/json" \
  "https://jira.your-company.com/rest/api/2/issue/PROJECT-123"
```

### Fetch Epic Children
```bash
curl -u "email:token" \
  -H "Accept: application/json" \
  "https://your-domain.atlassian.net/rest/api/3/search?jql=parent=PROJECT-123&fields=summary,description,issuetype"
```

### Fetch Linked Issues
```bash
# issuelinks field in the issue response contains linked issue keys
# then fetch each linked issue separately
curl -u "email:token" \
  -H "Accept: application/json" \
  "https://your-domain.atlassian.net/rest/api/3/issue/PROJECT-456?fields=summary,issuetype"
```

---

## 3. Python Request Example

```python
import requests
from requests.auth import HTTPBasicAuth
import json

def fetch_jira_issue(issue_key: str, domain: str, email: str, api_token: str) -> dict:
    url = f"https://{domain}.atlassian.net/rest/api/3/issue/{issue_key}"
    params = {
        "fields": "summary,description,issuetype,priority,status,assignee,"
                  "reporter,labels,components,subtasks,issuelinks,comment,"
                  "attachment,customfield_10016,customfield_10014"
    }
    response = requests.get(
        url,
        auth=HTTPBasicAuth(email, api_token),
        headers={"Accept": "application/json"},
        params=params
    )
    response.raise_for_status()
    return response.json()
```

---

## 4. Key Fields for Test Plan Generation

| Jira Field | API Field Name | Used For |
|------------|---------------|----------|
| Summary | `fields.summary` | Test plan title / scope |
| Description | `fields.description` | Feature context, requirements |
| Issue Type | `fields.issuetype.name` | Determines test depth (Story vs Bug vs Epic) |
| Priority | `fields.priority.name` | Risk-based testing emphasis |
| Acceptance Criteria | `fields.customfield_10016` (varies) | Direct test conditions → test cases |
| Labels | `fields.labels` | Tags for test categories |
| Components | `fields.components[].name` | Scope boundaries |
| Subtasks | `fields.subtasks[]` | Sub-features needing individual test cases |
| Linked Issues | `fields.issuelinks[]` | Dependencies, blocks, duplicates |
| Comments | `fields.comment.comments[]` | Dev notes, QA feedback, constraints |
| Attachments | `fields.attachment[]` | Wireframes, spec docs |
| Status | `fields.status.name` | Current state (affects test focus) |
| Story Points | `fields.customfield_10016` | Complexity signal |
| Sprint | `fields.customfield_10020` | Context / deadline |

---

## 5. Jira Description Format — ADF vs Plain Text

Jira Cloud API v3 returns description as **Atlassian Document Format (ADF)** — a nested JSON structure, not plain text.

```json
{
  "description": {
    "type": "doc",
    "version": 1,
    "content": [
      {
        "type": "paragraph",
        "content": [
          { "type": "text", "text": "User should be able to log in..." }
        ]
      }
    ]
  }
}
```

**Solution:** Write an ADF-to-plain-text parser, or use `jira2text` library, or use API v2 (returns plain Markdown-like text).

API v2 endpoint (returns simpler text):
```
GET /rest/api/2/issue/{issueIdOrKey}
```

---

## 6. Custom Field Discovery

Acceptance Criteria field name varies by Jira configuration. To discover it:

```bash
curl -u "email:token" \
  -H "Accept: application/json" \
  "https://your-domain.atlassian.net/rest/api/3/field" | \
  python3 -c "import sys,json; fields=json.load(sys.stdin); [print(f['id'], f['name']) for f in fields if 'criteria' in f['name'].lower() or 'acceptance' in f['name'].lower()]"
```

---

## 7. Rate Limits

- Jira Cloud: ~10 requests/second per token (burst), soft limit
- Server/DC: No enforced rate limit but respect server load
- Mitigation: Cache fetched issues in `.tmp/` folder, retry with exponential backoff

---

## 8. Constraints Found

- ADF parsing needed for Jira Cloud API v3 descriptions
- Acceptance Criteria custom field ID varies per Jira instance — must discover dynamically
- Linked issues require N+1 fetches (one per linked issue key)
- Attachments: only metadata returned, binary fetch needs separate call
- Comments may contain crucial QA context — must include in LLM prompt
- API v2 vs v3: v2 gives plain text description but v3 is the current supported version

---

## 9. Relevant GitHub Repos Found

- `pycontribs/jira` — Python Jira client library (wraps REST API, handles auth + pagination)
  - `pip install jira`
  - Handles both Cloud and Server auth transparently
- `atlassian-api/atlassian-python-api` — broader Atlassian SDK
- `ankitects/anki` style ADF parsers for extracting plain text from ADF JSON

**Recommended:** Use `jira` library for fetching, write custom ADF extractor for descriptions.

---

## 10. Open Questions — Resolved 2026-08-29

| Question | Answer |
|----------|--------|
| Jira Cloud or Server/DC? | **Cloud** (`*.atlassian.net`). Basic auth, REST API v3, ADF flattener required. |
| Confluence fetching needed? | **No** in v1. Jira is the only source of truth. |
| Write-back to Jira or Zephyr? | **No.** Delivery is Markdown and DOCX download only. Jira token needs read scope only. |
| Epics handled differently? | **Yes** — rule 12 in `LLM.md`: Epics get a skeleton plus per-child summaries, not exhaustive cases. |
| Acceptance Criteria field ID? | **Still unknown.** Not askable — it is instance-specific. Resolved at runtime, see section 12. |

Remaining unknown, to be resolved during Phase 2 Link against the live instance:
- [ ] Acceptance Criteria custom field ID on the target Jira instance
- [ ] Whether the corporate network requires a custom CA bundle for `*.atlassian.net`

---

## 11. Test Connection Endpoints

### Jira — validate URL, email, and token in one call

```bash
curl -u "your-email@domain.com:YOUR_API_TOKEN" \
  -H "Accept: application/json" \
  "https://your-domain.atlassian.net/rest/api/3/myself"
```

Response codes and what they mean for the status pill:

| Code | Meaning | Pill |
|------|---------|------|
| 200 | Valid. Response contains `displayName` and `emailAddress`, shown as confirmation. | connected |
| 401 | Email or API token wrong | failed |
| 403 | Credentials valid but the account lacks permission | failed |
| 404 | Base URL wrong, or a trailing path was included | failed |
| ConnectionError | Host unreachable, DNS, or proxy blocking | failed |
| SSLError | Corporate proxy with a custom CA intercepting TLS | failed, prompt the Verify SSL toggle |

### Groq — validate the key and the model in one call

```bash
curl -H "Authorization: Bearer $GROQ_API_KEY"   "https://api.groq.com/openai/v1/models"
```

Python:

```python
from groq import Groq

client = Groq(api_key=key)
available = [m.id for m in client.models.list().data]
ok = "openai/gpt-oss-120b" in available
```

**Do not use `client.models.retrieve(model_id)` to validate the model.**
It places the id into the URL path, so a namespaced id such as
`openai/gpt-oss-120b` is sent as `openai%2Fgpt-oss-120b` and the API returns:

```
404 - The model `openai%2Fgpt-oss-120b` does not exist or you do not have access to it.
```

That happens even when the model **is** present on the account. Verified on
2026-08-29 against a live key: `models.list()` returned 14 models including
`openai/gpt-oss-120b`, `openai/gpt-oss-20b`, and
`openai/gpt-oss-safeguard-20b`, while `models.retrieve("openai/gpt-oss-120b")`
raised `NotFoundError`. Membership in `models.list()` is the correct check.

Model `openai/gpt-oss-120b` is **confirmed available** on the target account.

---

## 12. Acceptance Criteria Field Discovery

The field ID differs per Jira instance and must never be hardcoded.

```bash
curl -u "email:token" \
  -H "Accept: application/json" \
  "https://your-domain.atlassian.net/rest/api/3/field"
```

Returns a list of objects shaped `{"id": "customfield_10016", "name": "Acceptance Criteria", ...}`.

**Match on `name`, not `id`.** The sibling project matches the substring
`"acceptance"` against the field key, which is always of the form
`customfield_NNNNN` and therefore never matches. That fallback is dead code
there and must not be copied.

```python
def discover_ac_field(fields: list[dict]) -> str | None:
    for f in fields:
        if "acceptance" in f.get("name", "").lower():
            return f["id"]
    return None
```

Result is cached in `.tmp/cache/field_map.json` so the discovery call runs once
per instance rather than once per issue.

---

## 13. Reusable Code in Sibling Projects

Two existing projects in this repo solve overlapping problems. Logic is worth
borrowing; the implementations are not worth copying verbatim.

### `Local_Agents/Local_Test_Generator/Local_Testcase_Generator/Src/`

| File | What is reusable | What must not be carried over |
|------|-----------------|------------------------------|
| `jira_client.py` | `_extract_adf_text()` recursive ADF walker (line 13). Correct approach, handles nested content and per-node-type separators. | `verify=False` on every request (line 38). Acceptance Criteria fallback matching on field key instead of field name (line 73) — dead code. Only six fields fetched; we need thirteen. |
| `pages/settings.py` | The whole card pattern: `st.form` + Save and Test Connection as two `st.form_submit_button`s in a 2-column layout, plus `_status_pill()` (line 46) driven by session state. Jira test hits `/rest/api/3/myself` (line 124), Groq test does a 5-token completion (line 268). | Saves to plaintext `config.json`. Ollama endpoint and Groq model hardcoded as captions rather than editable. |
| `llm_client.py` | Lazy `groq` import with an actionable ImportError message (line 48). | Single concatenated prompt string with no system role (app.py line 77). This blocks structured JSON output and is the main reason for a fresh build. No `temperature`, no `max_tokens`. |
| `config_store.py` | The read-merge-write idiom. | Plaintext secrets, non-atomic writes, re-reads the file on every `get()`. |
| `requirements.txt` | — | Lists only `streamlit` and `requests`. `groq` and `httpx` are imported but undeclared, so a clean install crashes at runtime. |

### `Requirement_Analyser_Agent/src/`

Cleaner abstractions, closer to what `LLM.md` requires:

- `llm/base_llm.py:4` — `BaseLLM(ABC)` with `complete(system_prompt, user_prompt, max_tokens)` and `is_available()`. **Separate system and user prompts**, which is what structured JSON output needs. Adopt this interface.
- `llm/groq_llm.py:20` — proper system plus user message roles with `temperature=0.2`. Adopt.
- `llm/llm_router.py:51` — `from_env()` reading `GROQ_API_KEY`, `GROQ_MODEL`, and friends. Adopt the pattern, narrowed to Groq for v1.
- `connectors/jira_connector.py` — `_fetch_comments()` hitting `/rest/api/3/issue/{key}/comment` (line 66) and `_adf_to_text()` (line 77). Both needed here.
- `requirements.txt` — correctly declares `groq>=0.9.0`, `python-docx>=1.1.0`, `python-dotenv>=1.0.0`. Use as the baseline.

### Security note recorded during research

`Local_Test_Generator/Src/config.json` and `Src/env.md` currently hold live Jira
and Groq credentials in plaintext. Both are gitignored, so nothing has leaked to
version control, but this is the direct motivation for the `.env` decision here
and for keeping `.env` out of the Settings screen's plaintext dump path.

---

## 14. DOCX Generation

`python-docx` is already proven in `Requirement_Analyser_Agent/src/output/docx_generator.py`.

```python
from docx import Document

doc = Document()
doc.add_heading(plan["title"], level=0)
doc.add_paragraph(plan["overview"])
table = doc.add_table(rows=1, cols=5)
table.style = "Light Grid Accent 1"
```

Test cases render as a table with columns: TC ID, Title, Priority, Steps,
Expected Result. The traceability matrix renders as a second table.

---

## 15. Groq Rate Limits and the 413

Confirmed live on 2026-08-29 by reading the response headers on the target account:

```
x-ratelimit-limit-requests   = 1000
x-ratelimit-limit-tokens     = 8000     <- tokens per minute
x-ratelimit-remaining-tokens = 7918
x-ratelimit-reset-tokens     = 615ms
```

**Input and output share the 8000 TPM budget.** A `max_tokens` at or above the
limit is therefore rejected before the request runs:

```
413 - Request too large for model openai/gpt-oss-120b ... on tokens per minute (TPM): Limit 8000
```

The original default of `GROQ_MAX_TOKENS=8192` exceeded the entire per-minute
allowance on its own, so every generation failed regardless of ticket size.

### Measured prompt footprint

| Component | Tokens |
|-----------|--------|
| System prompt | ~880 |
| Output schema hint | ~350 |
| **Fixed overhead** | **1228** (measured, not estimated) |
| Remaining for issue data + response | 6772 |

A real generation for a two-criterion story used 3268 total tokens, well inside
the budget.

### Reading your own limits

```bash
curl -s -D - -o /dev/null -X POST https://api.groq.com/openai/v1/chat/completions   -H "Authorization: Bearer $GROQ_API_KEY"   -H "Content-Type: application/json"   -d '{"model":"openai/gpt-oss-120b","messages":[{"role":"user","content":"hi"}],"max_tokens":1}'   | grep -i ratelimit
```

Set `GROQ_TPM_LIMIT` in `.env` to whatever `x-ratelimit-limit-tokens` reports
for your tier. The clamp and the input trimming both scale off that number.

