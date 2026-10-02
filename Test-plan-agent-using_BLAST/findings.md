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

## 10. Open Questions

- [ ] Is domain internal Jira or external client Jira?
- [ ] What is the custom field ID for Acceptance Criteria on the target instance?
- [ ] Are Confluence pages linked to Jira issues and should they be fetched too?
- [ ] Should the tool handle Epics differently from Stories/Bugs/Tasks?
