# LLM.md — Project Constitution

> Test Plan Creator from Jira ID
> Established: 2026-08-29 under B.L.A.S.T. Protocol 0
>
> This file is the authority. If code and this document disagree, this document
> wins and the code is wrong. Any change to schemas, rules, or architecture is
> made here first and in the code second.

---

## 1. Identity and Mission

The system takes a single Jira issue key as input and produces a structured,
executable test plan as output.

It is a translator, not an author. Everything in the generated test plan traces
back to something present in the Jira issue. The system does not invent
requirements, does not assume unstated business logic, and does not pad the plan
with generic boilerplate to look thorough.

**The system will:**
- Fetch and normalize all relevant Jira issue data
- Derive test cases from acceptance criteria, description, and subtasks
- Produce a traceability matrix linking every acceptance criterion to test cases
- Flag gaps where the issue lacks information needed to test properly

**The system will not:**
- Fabricate acceptance criteria that are absent from the issue
- Generate test cases for functionality never mentioned in the issue
- Modify the Jira issue unless the user has explicitly enabled write-back
- Silently proceed when the issue description is empty; it reports the gap

---

## 2. Input Schema

The raw Jira API response is never passed to the LLM. It is first normalized
into this flat, predictable shape. This isolates the rest of the system from
Jira version differences, ADF nesting, and custom field ID variation.

```json
{
  "issue_key": "PROJ-123",
  "url": "https://domain.atlassian.net/browse/PROJ-123",
  "summary": "User can reset password via email link",
  "description": "Plain text, flattened from ADF",
  "issue_type": "Story",
  "priority": "High",
  "status": "In Progress",
  "assignee": "Jane Doe",
  "reporter": "John Smith",
  "story_points": 5,
  "sprint": "Sprint 42",
  "labels": ["authentication", "security"],
  "components": ["Auth Service", "Email Service"],
  "acceptance_criteria": [
    "Given a registered email, when reset is requested, an email is sent within 30 seconds",
    "Reset link expires after 24 hours"
  ],
  "subtasks": [
    { "key": "PROJ-124", "summary": "Build reset token generator", "status": "Done" }
  ],
  "linked_issues": [
    { "key": "PROJ-99", "summary": "Email service rate limiting", "link_type": "blocks" }
  ],
  "comments": [
    { "author": "Jane Doe", "created": "2026-08-20T10:00:00Z", "body": "Rate limit is 3 per hour" }
  ],
  "attachments": [
    { "filename": "reset-flow.png", "mime_type": "image/png", "url": "https://..." }
  ],
  "fetched_at": "2026-08-29T12:00:00Z"
}
```

**Normalization rules**
- `description` is always plain text. ADF trees are flattened before this schema is populated.
- `acceptance_criteria` is always a list of strings, even when Jira stores it as one text blob. Bullet points, numbered lines, and Gherkin blocks are split into separate entries.
- Any field that is absent in Jira appears as `null` for scalars or `[]` for lists. Keys are never omitted.
- `fetched_at` supports cache invalidation.

---

## 3. Output Schema

The LLM returns exactly this shape. Nothing else. No prose wrapper, no markdown
fences, no commentary.

```json
{
  "plan_id": "TP-PROJ-123",
  "source_issue": "PROJ-123",
  "title": "Test Plan: User can reset password via email link",
  "generated_at": "2026-08-29T12:05:00Z",
  "overview": "One paragraph describing what is being tested and why.",
  "scope": {
    "in_scope": ["Password reset request flow", "Reset link expiry handling"],
    "out_of_scope": ["Initial user registration", "OAuth login paths"]
  },
  "assumptions": [
    "[INFERRED] Email delivery is handled by an existing, already-tested service"
  ],
  "test_strategy": "Risk-based. Functional coverage of all acceptance criteria, plus negative and boundary cases around token expiry.",
  "test_environments": [
    { "name": "Staging", "notes": "Requires seeded test accounts with verified emails" }
  ],
  "test_data_requirements": [
    "A registered account with a verified email address",
    "An expired reset token for negative-path testing"
  ],
  "entry_criteria": [
    "PROJ-123 is in Ready for QA status",
    "Staging build contains the reset endpoint"
  ],
  "exit_criteria": [
    "All P0 and P1 test cases pass",
    "No open Critical or Blocker defects"
  ],
  "test_cases": [
    {
      "tc_id": "TC-PROJ-123-001",
      "title": "Reset email is delivered within 30 seconds",
      "type": "Functional",
      "priority": "P0",
      "traces_to": "AC-1",
      "preconditions": "A registered account with a verified email exists",
      "steps": [
        { "step_no": 1, "action": "Navigate to the login page", "test_data": "-" },
        { "step_no": 2, "action": "Click Forgot Password", "test_data": "-" },
        { "step_no": 3, "action": "Enter the registered email and submit", "test_data": "qa.user@example.com" }
      ],
      "expected_result": "A reset email arrives in the inbox within 30 seconds and contains a valid reset link",
      "inferred": false
    }
  ],
  "risks": [
    {
      "risk": "Email service rate limiting may block bulk test runs",
      "severity": "Medium",
      "mitigation": "Throttle test execution to 3 requests per hour per account",
      "source": "PROJ-99 (blocks), and comment by Jane Doe"
    }
  ],
  "traceability_matrix": [
    { "ac_id": "AC-1", "acceptance_criterion": "Email sent within 30 seconds", "test_case_ids": ["TC-PROJ-123-001"] },
    { "ac_id": "AC-2", "acceptance_criterion": "Reset link expires after 24 hours", "test_case_ids": ["TC-PROJ-123-004", "TC-PROJ-123-005"] }
  ],
  "coverage_gaps": [
    "The issue does not specify what the user sees when an unregistered email is submitted. Behavior needs confirmation before this path can be tested."
  ]
}
```

---

## 4. Behavioral Rules

**Grounding**
1. Every test case must trace to something in the input: an acceptance criterion, a description sentence, a subtask, or a comment. The `traces_to` field is mandatory.
2. Content the model derives rather than reads is marked `"inferred": true` and, in prose fields, prefixed with `[INFERRED]`. Inference is allowed; hiding it is not.
3. Missing information becomes an entry in `coverage_gaps`. It is never filled in with a plausible guess.

**Identifiers**
4. Test case IDs follow `TC-{ISSUE_KEY}-{NNN}` with three-digit zero-padded sequence numbers starting at 001.
5. Acceptance criterion IDs follow `AC-{n}`, numbered in the order they appear in the normalized input.
6. Plan IDs follow `TP-{ISSUE_KEY}`.

**Coverage**
7. Every acceptance criterion gets at least one test case. A criterion with zero linked test cases is a generation failure, not an acceptable output.
8. Each acceptance criterion involving a boundary, limit, or time window also gets at least one negative or boundary case.
9. Test case count scales with the issue. A one-line bug fix does not get a forty-case plan.

**Type-specific behavior**
10. `Bug` issues emphasize reproduction steps and regression coverage around the fix.
11. `Story` issues emphasize acceptance criteria coverage and integration points.
12. `Epic` issues produce a plan skeleton plus per-child summaries rather than exhaustive cases.

**Output discipline**
13. The model returns raw JSON matching the output schema. No markdown fences, no preamble, no trailing explanation.
14. Formatting into Markdown, HTML, or Jira wiki markup happens in a deterministic formatter tool, never in the LLM.

---

## 5. Architectural Invariants

The A.N.T. three-layer split from `BLAST.md` applies.

**Layer 1 — `architecture/`**
Markdown SOPs describing what each tool does, its inputs and outputs, and its
edge cases. When behavior changes, the SOP is updated before the code.

Planned SOPs:
- `jira_fetch_sop.md`
- `normalization_sop.md`
- `test_plan_generation_sop.md`
- `output_formatter_sop.md`
- `delivery_sop.md`

**Layer 2 — Navigation**
The reasoning layer routes data between tools in order. It does no data
transformation of its own. Pipeline order is fixed:

```
issue_key -> fetch -> normalize -> generate -> validate -> format -> deliver
```

**Layer 3 — `tools/`**
Deterministic Python scripts, each atomic and independently testable.

| Tool | Responsibility | Calls an LLM? |
|------|---------------|---------------|
| `fetch_jira_issue.py` | Retrieve the raw Jira JSON | No |
| `normalize_issue.py` | Flatten ADF, split acceptance criteria, apply the input schema | No |
| `generate_test_plan.py` | Single LLM call producing the output schema | Yes |
| `validate_plan.py` | Schema validation and coverage assertions | No |
| `format_output.py` | Render JSON into Markdown, HTML, or Jira markup | No |
| `deliver_output.py` | Write to disk, post a Jira comment, or create a Confluence page | No |

**Invariants**
1. Exactly one tool in the pipeline calls an LLM. Every other tool is deterministic and unit-testable without a network connection.
2. Tools communicate through JSON files in `.tmp/`, never through shared in-memory state. Any stage can be re-run in isolation against the output of the previous stage.
3. All secrets live in `.env` and are read only at process start. No credential is ever written to `.tmp/`, to a log, or into a prompt.
4. Fetched Jira responses are cached in `.tmp/cache/{issue_key}.json`. Re-running a generation does not re-hit the Jira API unless the cache is explicitly cleared.
5. Every tool exits non-zero with a readable message on failure. The pipeline halts rather than passing partial data downstream.
6. The custom field ID for acceptance criteria is discovered at runtime and cached per Jira instance. It is never hardcoded.

---

## 6. LLM Provider Rules

**Locked for v1: Groq, model `openai/gpt-oss-120b`.**

1. Providers sit behind one interface, adopted from `Requirement_Analyser_Agent/src/llm/base_llm.py`:

```python
class BaseLLM(ABC):
    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 8192) -> str: ...

    @abstractmethod
    def is_available(self) -> bool: ...
```

   System and user prompts stay separate. They are never concatenated into a
   single string — that pattern, used in `Local_Test_Generator/Src/app.py:77`,
   defeats structured JSON output and is the reason this project is a fresh build.

2. Groq is called through the official `groq` SDK with `response_format={"type": "json_object"}`.
3. Every response is validated against the output schema. A validation failure triggers exactly one retry with the validation error appended as an extra user message. A second failure raises. There is no silent fallback to unstructured text.
4. Temperature defaults to 0.2 and is capped at 1.0 in the UI. Test plans should be close to reproducible.
5. Model ID, temperature, and API key come from `.env`. No hardcoded constants, so a Groq model rename needs no code change.
6. `is_available()` validates the key and the model with a single `models.list()` call, checking that the configured model id is a member of the returned list. `models.retrieve()` must not be used: it URL-encodes the slash in a namespaced id such as `openai/gpt-oss-120b` and returns 404 even when the model is present. See `findings.md` section 11.
7. Token usage and latency are recorded for every call and appended to the metrics section of `progress.md`.
8. Input and output share one tokens-per-minute budget. `max_tokens` is clamped at call time to `TPM_LIMIT - safety_margin - estimated_input`, because a `max_tokens` at or above the TPM limit is rejected with a 413 before the request runs. A prompt too large to leave room for a useful response raises with an actionable message rather than being sent.
9. Input that exceeds the budget is trimmed in a fixed order of least value to a test plan: attachments, then linked issues, then comments, then subtasks, then the description. **Summary and acceptance criteria are never trimmed** -- they are the plan. Every trim is reported to the user and appended to `coverage_gaps`, because silently truncating a ticket means silently reducing test coverage.
10. TLS verification is **on** by default. It may be disabled only through the explicit `JIRA_VERIFY_SSL=false` setting, surfaced in the UI as an insecure option with a warning. It is never disabled by default anywhere in the codebase.

---

## 7. Prompt Contract

**System prompt** establishes the role, the grounding rules from section 4, and
the exact output schema from section 3. It states plainly that the model returns
JSON only.

**User prompt** contains the normalized input JSON from section 2 and nothing
else. No conversational framing, no restating of the rules.

The prompt lives in `architecture/test_plan_generation_sop.md` as the single
source of truth and is loaded from there at runtime. It is not embedded as a
string literal in the Python code.

---

## 8. Configuration Schema

All configuration lives in one gitignored `.env` file at the project root. There
is no `config.json`. There is no second store.

```bash
# --- Jira (Cloud) ---
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=you@company.com
JIRA_API_TOKEN=                      # read scope is sufficient
JIRA_DEFAULT_PROJECT_KEY=QA          # optional, lets "123" resolve to "QA-123"
JIRA_VERIFY_SSL=true                 # set false ONLY for a corporate proxy with a custom CA

# --- Groq ---
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-120b
GROQ_TEMPERATURE=0.2
GROQ_MAX_TOKENS=6000                 # must stay below GROQ_TPM_LIMIT
GROQ_TPM_LIMIT=8000                  # account tokens-per-minute allowance

# --- Preferences (non-secret) ---
DISPLAY_NAME=                        # stamped as plan author, cosmetic only
DEFAULT_OUTPUT_FORMAT=markdown       # markdown | docx
```

**Configuration rules**

1. `.env` is listed in `.gitignore` before any key is ever written to it.
2. `.env.example` is committed and holds every key with empty values. It is the documentation of what the app needs.
3. `tools/config_store.py` is the only module that reads or writes `.env`. It does read-modify-write preserving comments and key order, and it updates `os.environ` in the same process so a Test Connection immediately after a Save uses the new value without a restart.
4. Secret values are never logged, never written to `.tmp/`, and never included in an error message or a prompt.
5. A missing required key is a startup-time failure with a message naming the key and linking to the Settings screen. It is never a silent default.

---

## 9. Screen Contracts

### Screen 1 — Chat (`ui/app.py`)

**Accepts:** a natural-language request that contains a Jira issue key.

**Key resolution order**
1. Regex `\b([A-Z][A-Z0-9]+-\d+)\b` against the input. Match wins.
2. No match, but the input contains a bare number and `JIRA_DEFAULT_PROJECT_KEY` is set: compose `{KEY}-{number}`.
3. Neither: the agent replies asking for a Jira key. It does **not** fall through to a general-purpose QA assistant. Scope is test plan generation only.

**Preflight.** Before any pipeline stage runs, required settings are checked. If
Jira or Groq settings are incomplete, generation is blocked with a message
naming the missing fields and a link to the Settings page. No half-run.

**Stage feedback.** The user sees each pipeline stage as it happens: Fetching,
Normalizing, Generating, Validating, Formatting. A failure names the stage that
failed.

**Rendering.** Coverage gaps and unmet acceptance criteria appear **above** the
test cases, not buried at the bottom. A plan the user must not trust blindly
must not look complete at a glance.

**Delivery.** Download buttons for Markdown and DOCX. The raw plan JSON is also
downloadable for debugging. Nothing is written back to Jira.

### Screen 2 — Settings (`ui/pages/settings.py`)

Three cards. Each is an `st.form` with a Save button and a Test Connection
button side by side, and a status pill reading `untested`, `connected`, or
`failed`, held in `st.session_state`.

| Card | Fields | Test Connection |
|------|--------|----------------|
| Jira | Base URL, Email, API Token (password), Default Project Key, Verify SSL (toggle) | `GET /rest/api/3/myself`, reports `displayName` |
| Groq | API Key (password), Model ID (default `openai/gpt-oss-120b`), Temperature (slider) | `models.list()`, then assert the model id is a member of the returned list |
| Preferences | Display Name, Default Output Format | none |

**Settings rules**
1. Every secret field uses `type="password"`. A stored secret renders as a masked placeholder, never as its real value.
2. Test Connection tests the values currently in the form, not the values last saved. Testing before saving must work.
3. Every failure branch produces a distinct, actionable message. `401` says the token is wrong; `404` says the URL is wrong; an SSL error suggests the Verify SSL toggle. A generic "connection failed" is not acceptable.
4. Saving Jira URL strips whitespace and any trailing slash.
5. Successfully discovering the Acceptance Criteria field ID during a Jira test is reported to the user and cached.

---

## 10. Project Layout

```
Test-plan-agent-using_BLAST/
├── BLAST.md                 # protocol definition
├── LLM.md                   # this file - the constitution
├── task_plan.md             # phases, checklists, locked decisions
├── findings.md              # research, endpoints, reuse notes
├── progress.md              # running work log
├── .env                     # gitignored, real secrets
├── .env.example             # committed, empty values
├── .gitignore
├── requirements.txt
├── architecture/            # Layer 1 - SOPs, written before code
│   ├── jira_fetch_sop.md
│   ├── normalization_sop.md
│   ├── test_plan_generation_sop.md
│   ├── validation_sop.md
│   └── output_formatter_sop.md
├── tools/                   # Layer 3 - deterministic, atomic, testable
│   ├── config_store.py
│   ├── jira_client.py
│   ├── normalize_issue.py
│   ├── llm_client.py
│   ├── generate_test_plan.py
│   ├── validate_plan.py
│   ├── format_markdown.py
│   ├── format_docx.py
│   └── pipeline.py          # Layer 2 - navigation, fixed stage order
├── ui/                      # Layer 4 - Stylize
│   ├── app.py               # Screen 1, chat
│   ├── pages/
│   │   └── settings.py      # Screen 2, settings
│   └── .streamlit/config.toml
└── .tmp/                    # gitignored intermediates
    ├── cache/               # {issue_key}.json, field_map.json
    └── runs/                # per-run stage outputs for debugging
```

---

## 11. Change Log

| Date | Change | Reason |
|------|--------|--------|
| 2026-08-29 | Constitution established | Protocol 0 initialization |
| 2026-08-29 | Added sections 8, 9, 10. Rewrote section 6 for Groq. | Discovery answered: Jira Cloud, `.env` secrets, Groq `openai/gpt-oss-120b`, download-only delivery, test-plan-only chat scope. Provider interface adopted from `Requirement_Analyser_Agent`. TLS verification made on-by-default in reaction to the sibling project's blanket `verify=False`. |
