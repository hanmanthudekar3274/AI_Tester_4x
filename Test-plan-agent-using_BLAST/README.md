# Test Plan Agent

Generates a structured test plan from a Jira issue key. Built with the
B.L.A.S.T. protocol and the A.N.T. 3-layer architecture.

The agent is a translator, not an author: every test case traces back to
something actually present in the Jira issue. Anything it derives rather than
reads is marked `[INFERRED]`, and anything the issue fails to specify is
reported as a coverage gap instead of being quietly invented.

---

## Quick start

```bash
pip install -r requirements.txt
streamlit run ui/app.py
```

Then open the Settings page, fill in the Jira and Groq cards, and press
**Test Connection** on each before generating anything.

### CLI

```bash
python -m tools.pipeline --issue QA-123
python -m tools.pipeline --issue QA-123 --format docx --out plan.docx
python -m tools.pipeline --issue QA-123 --refresh   # bypass the cache
```

### Tests

```bash
python tests/run_all.py
```

95 assertions across 5 suites. No network access and no API keys required —
the only LLM-calling tool is injected with a fake.

---

## Configuration

Everything lives in a gitignored `.env`. Copy `.env.example` and fill it in, or
use the Settings screen, which writes the same file.

| Key | Purpose |
|-----|---------|
| `JIRA_BASE_URL` | e.g. `https://acme.atlassian.net` |
| `JIRA_EMAIL` | Atlassian account email |
| `JIRA_API_TOKEN` | **Read scope is sufficient.** This app never writes to Jira. |
| `JIRA_DEFAULT_PROJECT_KEY` | Optional. Set `QA` and you can type `123` for `QA-123`. |
| `JIRA_VERIFY_SSL` | Leave `true`. See the security note below. |
| `GROQ_API_KEY` | From console.groq.com/keys |
| `GROQ_MODEL` | Default `openai/gpt-oss-120b` |
| `GROQ_TEMPERATURE` | Default `0.2`, for near-reproducible plans |
| `GROQ_MAX_TOKENS` | Raise if long plans come back truncated |
| `DISPLAY_NAME` | Stamped as plan author. Cosmetic. |
| `DEFAULT_OUTPUT_FORMAT` | `markdown` or `docx` |

**Never commit `.env`.** It is gitignored, and `config_store.py` is the only
module allowed to read or write it.

---

## Architecture

```
issue_key -> fetch -> normalize -> generate -> validate -> format -> download
```

Exactly one stage calls an LLM. Every other stage is deterministic and unit
testable with no network. Stages communicate through JSON files under `.tmp/`,
so any stage can be re-run in isolation against the previous stage's output.

| Layer | Location | Role |
|-------|----------|------|
| 1 — Architecture | `architecture/*.md` | SOPs. The authority on behavior. |
| 2 — Navigation | `tools/pipeline.py` | Routes data between tools. No transformation of its own. |
| 3 — Tools | `tools/*.py` | Atomic, deterministic, testable. |
| 4 — UI | `ui/` | Streamlit. Presentation only. |

`LLM.md` is the project constitution: schemas, behavioral rules, and
architectural invariants. **If code and `LLM.md` disagree, the code is wrong.**

### The Golden Rule

If logic changes, update the SOP in `architecture/` *before* the code. This
applies to prompts too — the generation system prompt lives in
`architecture/test_plan_generation_sop.md` between HTML comment markers and is
loaded from there at runtime. It is never duplicated as a string literal in
Python, and a test asserts that.

---

## How trust is enforced

An LLM is probabilistic; a test plan a QA engineer will act on must not be.
Three mechanisms:

1. **Grounding.** Every test case carries a `traces_to` naming its source. An empty `traces_to` fails validation.
2. **Coverage assertion.** Every acceptance criterion must appear in the traceability matrix with at least one real test case. An uncovered criterion is an *error*, not a warning, and forces a retry. This is the exact failure mode the project exists to prevent.
3. **Bounded retry.** A plan that fails validation is regenerated once with the specific errors fed back. A second failure raises. There is no silent fallback to unstructured text.

Coverage gaps render *above* the test cases in every output format. A plan the
reader must not trust blindly must not look complete at a glance.

---

## Security notes

- The Jira token needs **read scope only**. Every request in `jira_client.py` is a `GET`.
- Secrets are never logged, never written to `.tmp/`, and never included in an exception message.
- `JIRA_VERIFY_SSL=false` disables TLS certificate checking and exposes your API token to anything on the network path. It exists only for corporate proxies that rewrite certificates, it is never the default, and the UI labels it as insecure.

---

## Known limitations (v1)

- Jira **Cloud** only. Server and Data Center use different auth and a different API version.
- Linked issues contribute their metadata only; there is no follow-up fetch of each linked issue's full content.
- Comments are capped at 50, most recent first. Truncation is recorded so the generator knows context was dropped.
- No write-back: no Jira comment, no Confluence page, no Zephyr or Xray push. Deferred to v2.
- Attachments contribute filenames only. Images and specs are not read.
