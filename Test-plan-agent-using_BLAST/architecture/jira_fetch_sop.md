# SOP — Jira Fetch

> Layer 1 document. `tools/jira_client.py` implements this.
> Golden Rule: if the logic changes, this file changes first.

---

## Goal

Retrieve the complete raw JSON for one Jira Cloud issue, plus its comments, and
hand it downstream unmodified. This tool does no interpretation — flattening and
reshaping belong to the normalizer.

---

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| `issue_key` | Caller, e.g. `QA-123` | Yes |
| `JIRA_BASE_URL` | `.env` | Yes |
| `JIRA_EMAIL` | `.env` | Yes |
| `JIRA_API_TOKEN` | `.env` | Yes |
| `JIRA_VERIFY_SSL` | `.env`, default `true` | No |

---

## Output

```json
{
  "issue": { "...raw Jira issue JSON..." },
  "comments": [ { "...raw comment JSON..." } ],
  "field_map": { "acceptance_criteria": "customfield_10016" },
  "fetched_at": "2026-08-29T12:00:00Z"
}
```

Written to `.tmp/cache/{issue_key}.json`.

---

## Procedure

### 1. Resolve the issue key

- Uppercase and strip the input.
- If it matches `^[A-Z][A-Z0-9]+-\d+$`, use it as-is.
- If it is a bare number and `JIRA_DEFAULT_PROJECT_KEY` is set, compose `{KEY}-{number}`.
- Otherwise raise `JiraClientError` naming the expected format.

### 2. Check the cache

If `.tmp/cache/{issue_key}.json` exists and the caller did not pass
`force_refresh=True`, return it. Re-running a generation must not re-hit the
Jira API. Cache entries carry `fetched_at` so staleness is visible.

### 3. Discover the Acceptance Criteria field

Cached per instance in `.tmp/cache/field_map.json`. On a miss:

```
GET {base_url}/rest/api/3/field
```

Match on the field **`name`** containing `acceptance`, case-insensitive. Never
match on `id` — IDs are always of the form `customfield_NNNNN`, so matching on
`id` can never succeed. That bug exists in `Local_Test_Generator/Src/jira_client.py:73`
and must not be reproduced.

A miss is not fatal. Record `acceptance_criteria: null` and let the normalizer
fall back to parsing criteria out of the description body.

### 4. Fetch the issue

```
GET {base_url}/rest/api/3/issue/{issue_key}?fields={field_list}
```

`field_list` is the thirteen mapped fields from `findings.md` section 4, plus
the discovered acceptance criteria field ID when one was found.

Auth: HTTP Basic, `email:api_token`. Timeout 20 seconds.

### 5. Fetch comments separately

```
GET {base_url}/rest/api/3/issue/{issue_key}/comment?maxResults=50&orderBy=created
```

Comments are fetched in their own call rather than through the `comment` field
expansion, because the embedded form truncates unpredictably. Comments carry
real QA context — rate limits, edge cases agreed in discussion — and feed the
generator directly.

### 6. Write the cache and return

---

## Error Handling

Every branch produces a distinct, actionable message. A generic "connection
failed" is not acceptable.

| Condition | Message |
|-----------|---------|
| 401 | Authentication failed. Check the Jira email and API token in Settings. |
| 403 | Authenticated, but this account cannot view `{key}`. Check project permissions. |
| 404 | Issue `{key}` not found. Check the key and the Jira base URL. |
| 429 | Jira rate limit reached. Retry after the `Retry-After` header. |
| 5xx | Jira returned a server error. Retry shortly. |
| `SSLError` | TLS verification failed. If behind a corporate proxy, see the Verify SSL toggle in Settings. |
| `ConnectionError` | Cannot reach `{base_url}`. Check the URL and network. |
| `Timeout` | Jira did not respond within 20 seconds. |

All raise `JiraClientError`. No exception escapes untyped.

---

## Edge Cases

| Case | Behavior |
|------|----------|
| Issue has no description | Return `null`. The normalizer flags the gap. Not an error here. |
| Issue has no acceptance criteria field | `field_map.acceptance_criteria` is `null`. Normalizer falls back to the description. |
| Issue has 200 comments | Capped at 50, most recent first. Truncation is recorded in the output so the generator knows context was dropped. |
| Issue is an Epic | Fetched identically. Child handling is the generator's concern, not this tool's. |
| Linked issues present | Only the link metadata already in the issue payload is kept. No N+1 fetch in v1 — deferred, and recorded as a limitation. |
| `base_url` has a trailing slash | Stripped before composing the URL. |
| `JIRA_VERIFY_SSL=false` | A warning is logged naming the risk. Never the default. |

---

## Test Connection

Used by the Settings screen, exposed as `test_connection(config) -> dict`.

```
GET {base_url}/rest/api/3/myself
```

Returns `{"ok": bool, "message": str, "display_name": str | None, "ac_field": str | None}`.
On success it also runs step 3 so the user learns the Acceptance Criteria field
was found, which is the single most likely silent failure in this pipeline.

---

## Invariants

1. This tool never calls an LLM.
2. This tool never mutates a Jira issue. Every request is a `GET`. The token needs read scope only.
3. The API token is never logged, never included in an exception message, and never written to `.tmp/`.
4. Raw output is passed through unmodified. Interpretation belongs to the normalizer.
