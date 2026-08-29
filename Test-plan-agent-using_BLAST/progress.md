# Progress Log — Test Plan Creator from Jira ID

> Session started: 2026-08-29
> Protocol: B.L.A.S.T. — currently in Protocol 0 (Initialization)

Log every meaningful unit of work here: what was attempted, what happened, what
broke, and what the next step is. Entries are append-only and newest-last.

---

## 2026-08-29

### Entry 001 — Project memory initialization

| Field | Value |
|-------|-------|
| Time | Session start |
| Phase | Protocol 0 |
| Action | Read `BLAST.md`, confirmed Protocol 0 requirements. Inspected project directory. |
| Result | Directory contained only `BLAST.md`. No prior state to recover. |
| Errors | None |
| Next | Create the four project memory files |

### Entry 002 — Created `task_plan.md`

| Field | Value |
|-------|-------|
| Phase | Protocol 0 |
| Action | Wrote phase checklist covering Protocol 0 through Phase 5 (Trigger), a prioritized goals table, and the five mandatory Discovery Questions. |
| Result | File created. Protocol 0 checklist items 1–4 marked complete. |
| Errors | None |
| Next | Research the Jira REST API before writing any fetch code |

### Entry 003 — Jira REST API research

| Field | Value |
|-------|-------|
| Phase | Protocol 0 / Phase 1 Research |
| Action | Researched Jira Cloud and Server/DC issue-fetch endpoints, authentication methods, field mapping, and rate limits. Recorded curl and Python examples in `findings.md`. |
| Result | Confirmed `GET /rest/api/3/issue/{issueIdOrKey}` as the primary endpoint. Identified thirteen issue fields relevant to test plan generation. |
| Errors | None — research only, no live API calls made (no credentials supplied yet). |
| Next | Resolve two known blockers before the Link phase |

### Entry 004 — Constraints discovered during research

| Field | Value |
|-------|-------|
| Phase | Protocol 0 |
| Finding 1 | Jira Cloud API v3 returns issue descriptions in Atlassian Document Format (ADF), a nested JSON tree rather than plain text. A flattening step is required before the text reaches the LLM. |
| Finding 2 | The Acceptance Criteria field is a custom field whose ID differs per Jira instance. It must be discovered at runtime via `GET /rest/api/3/field` rather than hardcoded. |
| Finding 3 | Linked issues are returned as keys only, so enriching them requires one additional request per link. This needs caching to stay within rate limits. |
| Impact | All three constraints are now reflected in the tool design recorded in `LLM.md`. |
| Next | Write the project constitution |

### Entry 005 — Created `findings.md`

| Field | Value |
|-------|-------|
| Phase | Protocol 0 |
| Action | Documented endpoints, three curl variants (Cloud basic auth, field-filtered, Server PAT), a Python `requests` example, the Jira field mapping table, the ADF problem, custom field discovery, rate limits, and candidate GitHub libraries. |
| Result | File created. Recommended `pycontribs/jira` for fetching plus a custom ADF extractor. |
| Errors | None |
| Next | Create `progress.md` and `LLM.md` |

### Entry 006 — Created `progress.md` and `LLM.md`

| Field | Value |
|-------|-------|
| Phase | Protocol 0 |
| Action | Wrote this log and the project constitution containing the input and output JSON schemas, behavioral rules, and architectural invariants. |
| Result | All four Protocol 0 memory files now exist. The Data Schema gate is satisfied. |
| Errors | None |
| Next | Answer the five Discovery Questions in `task_plan.md`, then request Blueprint approval. Code in `tools/` remains blocked until then. |

### Entry 007 — Security incident: credentials exposed

| Field | Value |
|-------|-------|
| Phase | Protocol 0 |
| Event | A live Groq API key was pasted directly into the chat session and is now recorded in the session transcript. |
| Action | Refused to write the key into any project file. Advised immediate revocation and regeneration at https://console.groq.com/keys. |
| Secondary finding | Code exploration of the sibling project found `Local_Test_Generator/Src/config.json` holding a live Jira API token plus a live Groq key in plaintext, and `Src/env.md` holding a second, different Groq key. Both files are gitignored so nothing reached version control, but both are readable by any process running as the current user. |
| Impact on design | Directly motivated the decision to store secrets in a gitignored `.env` rather than a UI-managed plaintext JSON file, and the rule that secrets are never logged or written to `.tmp/`. |
| Status | Awaiting user confirmation that the exposed keys have been rotated. |

### Entry 008 — Sibling codebase exploration

| Field | Value |
|-------|-------|
| Phase | Phase 1 Research |
| Action | Explored `Local_Agents/Local_Test_Generator/.../Src/` and `Requirement_Analyser_Agent/src/` for reusable components. |
| Result | Roughly 70 percent of the required plumbing already exists somewhere in this repo: an ADF flattener, a Jira Cloud Basic auth client, a Groq SDK adapter, and a settings page with a working three-card Save plus Test Connection pattern. |
| Defects found in the sibling, not to be carried over | `verify=False` on every Jira request. Acceptance Criteria fallback matches the substring `"acceptance"` against the field **key** (always `customfield_NNNNN`), so the fallback is dead code and never fires. System and user prompts concatenated into one string with no system role, which blocks structured JSON output. `groq` and `httpx` imported but absent from `requirements.txt`, so a clean install crashes at runtime. Only six Jira fields fetched where thirteen are needed. |
| Cleaner patterns found in Requirement_Analyser_Agent | `BaseLLM` abstract interface with separate `system_prompt` and `user_prompt` arguments. `from_env()` config loading. A comment-fetching Jira connector. A working `python-docx` generator. |
| Decision | Fresh build, borrowing logic and rewriting implementations. Adopt the `BaseLLM` interface. |
| Errors | None |
| Next | Put the open questions to the user |

### Entry 009 — Discovery questions answered

| Field | Value |
|-------|-------|
| Phase | Phase 1 Blueprint |
| Action | Asked eight questions across two rounds rather than assuming. First round returned three of four answers; the delivery question came back blank and was re-asked in round two. |
| Answers | Jira Cloud. Settings fields limited to Jira URL, email, API token, plus a cosmetic display name and a default project key — no password field, since Jira Cloud has no password auth. Delivery is Markdown and DOCX download only, so the Jira token needs read scope only. Secrets in a gitignored `.env` loaded by `python-dotenv`. Groq model `openai/gpt-oss-120b`. Chat screen scoped to test plan generation only, with no general Q&A fallback. Fresh build on the BLAST 3-layer structure. |
| Result | Every Protocol 0 gate is now satisfied. The halt on writing code in `tools/` is lifted. |
| Errors | None |
| Next | Record the decisions across all four memory files |

### Entry 010 — Memory files updated with the locked blueprint

| Field | Value |
|-------|-------|
| Phase | Phase 1 to Phase 2 boundary |
| Action | Rewrote `task_plan.md` with a locked-decisions table, both screen specifications, a revised five-phase checklist, a fourteen-row goals table, and a risk register. Extended `findings.md` with test connection endpoints and response-code handling, the acceptance criteria discovery procedure, a sibling-code reuse table, and DOCX notes. Extended `LLM.md` with the configuration schema, screen contracts, project layout, and a Groq-specific rewrite of the provider rules. |
| Result | All four memory files are consistent with the locked decisions. `LLM.md` now carries the input schema, output schema, configuration schema, and screen contracts. |
| Errors | A bash heredoc write of `LLM.md` failed with `unexpected EOF while looking for matching '` — the shell mis-parsed an apostrophe inside the quoted heredoc body. Worked around by using the file-write tool directly. Noted so the same approach is not retried for large Markdown bodies. |
| Next | Phase 2 Link: scaffold directories, write `.gitignore` and `.env.example` first, then verify both connections against live credentials |

### Entry 011 — Phase 2 Link: scaffold and configuration

| Field | Value |
|-------|-------|
| Phase | Phase 2 Link |
| Action | Created `architecture/`, `tools/`, `ui/pages/`, `.tmp/cache/`, `.tmp/runs/`. Wrote `.gitignore`, `.env.example`, `requirements.txt`, and `tools/config_store.py`. |
| Result | `.env` and `.tmp/` confirmed ignored by git; `.env.example` confirmed tracked. All seven dependencies already present in the Python 3.14.6 environment, so no install step was needed. |
| Defect found and fixed | The first `.env.example` shipped placeholder values (`https://your-domain.atlassian.net`, `you@company.com`). Since `config_store` seeds a new `.env` from the example, those placeholders were written as real values and `missing_required()` reported the config as complete. A run would then have started against a bogus URL. Rewrote the example with empty values and moved the samples into comments. Verified `missing_required()` now returns all four keys on a fresh `.env`. |
| Errors | None outstanding |
| Next | Build the fetch tool, SOP first |

### Entry 012 — Jira client

| Field | Value |
|-------|-------|
| Phase | Phase 3 Architect |
| Action | Wrote `architecture/jira_fetch_sop.md`, then `tools/jira_client.py`. |
| Result | Read-only client with per-status-code error branches, issue plus comment fetch, response caching, and a `test_connection()` for the Settings screen. Key resolution handles `QA-123`, `qa-123`, and a bare `123` against the default project key. |
| Deliberate divergence from the sibling project | Acceptance Criteria discovery matches on the field **name**, not the field id. The sibling matches `"acceptance"` against the id, which is always `customfield_NNNNN`, so its fallback can never fire. TLS verification defaults to on rather than being globally disabled. |
| Tests | Key resolution and rejection paths verified. |

### Entry 013 — Normalizer

| Field | Value |
|-------|-------|
| Phase | Phase 3 Architect |
| Action | Wrote `architecture/normalization_sop.md`, then `tools/normalize_issue.py`. Built a 27-assertion suite covering ADF flattening, criteria extraction, and degenerate payloads. |
| Result | 27 of 27 pass. |
| Errors | One real failure during development: Gherkin criteria came out as 5 entries instead of 2. Cause was that `_doc_to_text` separates ADF blocks with blank lines, and the grouping loop treated any non-Gherkin line, including a blank one, as a group terminator. Fixed by skipping blank lines rather than flushing the group. |
| Notes | Recursion is capped at depth 50, verified against a 200-deep nested document with no `RecursionError`. |

### Entry 014 — Validator

| Field | Value |
|-------|-------|
| Phase | Phase 3 Architect |
| Action | Wrote `architecture/validation_sop.md`, then `tools/validate_plan.py`. Built a 19-assertion suite. |
| Result | 19 of 19 pass. |
| Key behavior | An uncovered acceptance criterion is an **error**, not a warning, so it forces the retry. That is the exact failure mode this project exists to prevent. Confirmed the validator never raises, including on `None`, a list, a string, and an integer. |

### Entry 015 — Generator and the retry loop

| Field | Value |
|-------|-------|
| Phase | Phase 3 Architect |
| Action | Wrote `architecture/test_plan_generation_sop.md` holding the system prompt between HTML comment markers, then `tools/generate_test_plan.py` which loads the prompt from that file at runtime. Tested with a fake LLM so no API calls were spent. |
| Result | 15 of 15 pass. Verified: valid on attempt one makes exactly one call; an invalid plan triggers exactly one retry with the validation errors fed back verbatim; two failures raise rather than looping; a prose reply recovers through the retry; a fenced JSON reply is tolerated. |
| Invariant confirmed by test | The system prompt text does not appear anywhere in the Python source, so the BLAST Golden Rule holds for prompts as well as logic. |

### Entry 016 — Formatters

| Field | Value |
|-------|-------|
| Phase | Phase 3 Architect |
| Action | Wrote `architecture/output_formatter_sop.md`, then `tools/format_markdown.py` and `tools/format_docx.py`. |
| Result | 14 of 14 pass. Verified pipe escaping inside table cells, newline to `<br>` conversion, gaps rendering above the test cases, inferred markers, empty-step handling, and that every generated Markdown table has a consistent column count. |
| Errors | One real defect caught: a plan whose `scope` was a string rather than an object crashed both formatters with `AttributeError: 'str' object has no attribute 'get'`, violating the never-raises invariant. Fixed with an `isinstance` guard in both files. |

### Entry 017 — Pipeline and both screens

| Field | Value |
|-------|-------|
| Phase | Phase 3 and Phase 4 |
| Action | Wrote `tools/pipeline.py` as the Layer 2 navigator plus a CLI, then `ui/app.py` (chat) and `ui/pages/settings.py` (settings), and `ui/.streamlit/config.toml`. |
| Result | Streamlit boots; both routes return HTTP 200. Under `AppTest`, both screens render without exceptions. Confirmed all six required settings fields exist, both secret fields are password-masked, there are two Test Connection buttons and three Save buttons, and clicking Test Connection with blank fields warns rather than crashing. The chat screen blocks generation and names the missing settings instead of half-running. |
| Errors | `st.page_link` raised `KeyError: 'url_pathname'` when a page is executed outside the multipage router. Wrapped every `page_link` call in a guard that degrades to a caption, so a navigation link can no longer take a whole screen down. |
| Note on a false alarm | The test initially reported both secret fields as unmasked. The assertion was wrong, not the code: `AppTest` exposes `.type` as the element name, while the real widget type lives in `proto.type`, where `1` means password. Corrected the assertion; both fields are genuinely masked. |

### Entry 018 — Test suite committed

| Field | Value |
|-------|-------|
| Phase | Phase 3 |
| Action | Moved all five suites into `tests/` with a `tests/run_all.py` runner. |
| Result | 95 assertions across 5 suites, all passing. The whole suite runs with no network access and no API keys, because the only LLM-calling tool is injected with a fake in tests. |
| Next | Live verification against real credentials, which is blocked on the user |

---

## Test Results

| Date | Suite | Assertions | Result |
|------|-------|-----------|--------|
| 2026-08-29 | `test_normalize` | 27 | Pass |
| 2026-08-29 | `test_validate` | 19 | Pass |
| 2026-08-29 | `test_generate` | 15 | Pass |
| 2026-08-29 | `test_e2e` (formatters) | 14 | Pass |
| 2026-08-29 | `test_ui` (both screens) | 20 | Pass |
| 2026-08-29 | **Total** | **95** | **All pass** |

Not yet tested, because it requires live credentials:
- A real Jira fetch against a real issue
- A real Groq call, including whether `openai/gpt-oss-120b` resolves
- Plan quality on a real ticket

### Entry 019 — Live Groq verification, and a bug in my own validator

| Field | Value |
|-------|-------|
| Phase | Phase 2 Link |
| Event | The user entered real credentials and the Groq Test Connection reported: "Key is valid, but model 'openai/gpt-oss-120b' did not resolve." The user pushed back, stating the model is valid for their key. |
| Investigation | Listed the models available to the live key. `models.list()` returned 14 models including `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, and `openai/gpt-oss-safeguard-20b`. Calling `models.retrieve("openai/gpt-oss-120b")` on the same client raised `NotFoundError: 404 - The model 'openai%2Fgpt-oss-120b' does not exist or you do not have access to it.` |
| Root cause | Mine, not the user's. `models.retrieve()` places the model id into the URL path, so the slash in a namespaced id is percent-encoded to `%2F` and the request 404s even when the model is present on the account. The two-step check recorded in `findings.md` section 11 was wrong. |
| Fix | `GroqLLM.is_available()` now validates the key and the model with a single `models.list()` call and asserts membership in the returned list. On a miss it names the available models rather than saying only that the id failed. Corrected `findings.md` section 11 and `LLM.md` section 6 rule 6 and section 9, per the Golden Rule that docs change before code is considered settled. |
| Verified | Correct model returns "Connected. Model 'openai/gpt-oss-120b' is available." A bogus model id is rejected and lists real alternatives. A bad key still reports an authentication failure. |
| Outcome | **`openai/gpt-oss-120b` is confirmed available on the target account.** Risk 2 in `task_plan.md` is closed. |

### Entry 020 — Configuration precedence corrected for hand-edited .env

| Field | Value |
|-------|-------|
| Phase | Phase 2 Link |
| Trigger | The user chose to enter credentials by editing `.env` directly rather than through the Settings screen. |
| Problem | `load_config()` applied `os.environ` last. Once a value had been saved through Settings it also lived in `os.environ`, so a later hand edit to `.env` would be read and then silently overridden by the stale in-process value. |
| Fix | Reversed the precedence: `.env` now wins for any key it defines with a non-empty value, while keys absent from `.env` still fall through to `os.environ`, which preserves CI and container deployments that set real environment variables and ship no `.env`. |
| Verified | A hand edit to `.env` now wins over a stale `os.environ` value, and the environment-variable fallback still works for a key left blank in `.env`. |

### Entry 021 — Groq 413, and a default that could never have worked

| Field | Value |
|-------|-------|
| Phase | Phase 2 Link |
| Event | First real generation attempt failed with `413 - Request too large for model openai/gpt-oss-120b ... on tokens per minute (TPM): Limit 8000`. |
| Investigation | Read the live rate-limit headers: `x-ratelimit-limit-tokens = 8000`. Input and output share that one budget. |
| Root cause | Mine. The shipped default was `GROQ_MAX_TOKENS=8192`, which exceeds the entire per-minute allowance on its own, so the reservation alone triggered a 413 before any input was counted. Every generation would have failed regardless of ticket size. The user had also hand-set 10000, which made it worse. |
| Measured | Fixed prompt overhead is 1228 tokens (system prompt plus schema hint), leaving 6772 for issue data and the response. |
| Fix, three parts | 1. `max_tokens` is now clamped at call time to `TPM_LIMIT - margin - estimated_input`, so it can never exceed what is actually available. 2. Oversized input is trimmed in a fixed order — attachments, linked issues, comments, subtasks, then description — while summary and acceptance criteria are never touched, and every trim is reported and appended to `coverage_gaps`. 3. A 413 now maps to a message naming the budget and the setting to change. Defaults lowered to `GROQ_MAX_TOKENS=6000`, and `GROQ_TPM_LIMIT=8000` added as a configurable so a higher Groq tier scales the whole mechanism. |
| Verified live | A real end-to-end generation succeeded: 4 test cases, 100 percent criteria coverage, 3268 tokens, one attempt, no validation warnings, first case correctly tracing to AC-1. |
| Tests | Added `tests/test_budget.py`, 15 assertions, no network needed. Confirms clamping, refusal of an impossible prompt, trim ordering, and that acceptance criteria and summary survive trimming. |
| Note | The trimming reports are deliberately surfaced as coverage gaps rather than logged. Dropping 55 comments can drop real test context, and hiding that would defeat the point of the tool. |

---

## Blockers

| # | Blocker | Owner | Status |
|---|---------|-------|--------|
| 1 | Groq key pasted into chat must be revoked and regenerated | User | **Open — action required** |
| 2 | Plaintext live credentials in `Local_Test_Generator/Src/config.json` and `env.md` should be rotated | User | Open |
| 3 | Jira base URL, account email, and API token not yet supplied | User | Open |
| 4 | Acceptance Criteria custom field ID unknown for the target instance | Resolved at runtime once credentials exist | Deferred to Phase 2 |
| 5 | Model ID `openai/gpt-oss-120b` unverified against the live Groq account | Verified by the Test Connection button in Phase 2 | Deferred to Phase 2 |
| 6 | Unknown whether the corporate network needs a custom CA bundle for `*.atlassian.net` | Detected by the Jira Test Connection SSL error branch | Deferred to Phase 2 |
| ~~7~~ | ~~LLM provider not chosen~~ | — | Closed: Groq |
| ~~8~~ | ~~Delivery target undecided~~ | — | Closed: Markdown and DOCX download |


---

## Metrics to track once running

- Jira issues processed
- Average end-to-end generation time per issue
- LLM tokens consumed per test plan
- Schema validation failure rate (how often the model returns malformed JSON)
- Test cases generated per issue
- Acceptance criteria coverage percentage from the traceability matrix
