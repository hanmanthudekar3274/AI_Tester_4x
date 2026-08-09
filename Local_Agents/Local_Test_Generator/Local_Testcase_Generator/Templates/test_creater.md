# Test Case Creator from JIRA Story

## Purpose
Fetch a JIRA story and automatically generate structured functional test cases covering happy paths, edge cases, and negative scenarios.

---

## Instructions for Claude

### Step 1 — Get the JIRA Story Key

If the user hasn't provided a story key (e.g., `PROJ-123`), ask:
> "Please provide the JIRA story key (e.g., PROJ-123)."

---

### Step 2 — Fetch the Story

Use the Atlassian Rovo MCP connector to fetch the issue:

```
Tool: getJiraIssue
Args: { "issueIdOrKey": "<STORY_KEY>" }
```

Extract and note the following fields:
- **Summary** — the story title
- **Description** — full acceptance criteria / story body
- **Story Type** — Story, Bug, Task, Sub-task
- **Labels / Components** — for context
- **Acceptance Criteria** — if present as a structured field or within description
- **Priority**

If the Atlassian connector is not connected, ask the user to paste the story details directly.

---

### Step 3 — Analyze the Story

Before writing test cases, reason through:

1. **What is the feature/functionality being built?**
2. **What are the explicit acceptance criteria?**
3. **What are the implicit requirements** (e.g., authentication, permissions, data validation)?
4. **What are the boundaries / edge cases** (empty inputs, max lengths, invalid formats)?
5. **What are the negative scenarios** (unauthorized access, wrong data types, missing required fields)?

---

### Step 4 — Generate Test Cases

Produce test cases in the following format. Aim for comprehensive coverage:

---

#### Test Case Template

```
TC-001: <Short descriptive title>

Type:       [Functional | Negative | Edge Case | Integration | UI/UX]
Priority:   [High | Medium | Low]
Related:    <JIRA Story Key>

Preconditions:
- <Any setup required before executing this test>

Steps:
1. <Action step 1>
2. <Action step 2>
3. <Action step 3>

Expected Result:
- <What should happen after the steps>

Pass Criteria:
- <Specific, measurable condition that confirms success>
```

---

### Step 5 — Coverage Checklist

After generating test cases, verify coverage across these categories:

| Category              | Covered? |
|-----------------------|----------|
| Happy Path            | ✅ / ❌  |
| Input Validation      | ✅ / ❌  |
| Edge Cases            | ✅ / ❌  |
| Negative / Error Path | ✅ / ❌  |
| Authorization / Roles | ✅ / ❌  |
| UI Feedback / Errors  | ✅ / ❌  |
| Data Persistence      | ✅ / ❌  |
| Performance / Limits  | ✅ / ❌  |

---

### Step 6 — Output Options

Ask the user how they want the output:

1. **Markdown** — display in chat (default)
2. **Word Document (.docx)** — use the `docx` skill to produce a formatted file
3. **Excel Spreadsheet (.xlsx)** — use the `xlsx` skill, one row per test case
4. **Paste back to JIRA** — use `addCommentToJiraIssue` to post test cases as a comment on the story

---

## Example Output

Given a story: *"As a user, I can reset my password via email."*

---

**TC-001: Successful password reset with valid email**
- Type: Functional | Priority: High
- Preconditions: User exists in the system with email `test@example.com`
- Steps:
  1. Navigate to the Login page
  2. Click "Forgot Password"
  3. Enter `test@example.com` and submit
  4. Open email and click the reset link
  5. Enter a new valid password and confirm
- Expected Result: Password is updated; user can log in with the new password
- Pass Criteria: Login succeeds with new password; old password is rejected

---

**TC-002: Reset attempt with unregistered email**
- Type: Negative | Priority: High
- Preconditions: None
- Steps:
  1. Navigate to "Forgot Password"
  2. Enter `unknown@example.com` and submit
- Expected Result: A generic message is shown (no information leakage)
- Pass Criteria: Message reads "If this email exists, you'll receive a reset link"

---

**TC-003: Reset link expires after 24 hours**
- Type: Edge Case | Priority: Medium
- Preconditions: Valid reset email has been sent
- Steps:
  1. Wait 24+ hours (or manually expire the token)
  2. Click the reset link
- Expected Result: Link is invalid; user sees an expiry message
- Pass Criteria: Token is rejected; user is prompted to request a new link

---

## Notes

- If the story lacks acceptance criteria, flag it and generate test cases based on reasonable assumptions — then list those assumptions explicitly.
- For bug stories, always include a regression test case that confirms the bug is fixed.
- For API stories, generate test cases for each HTTP method/endpoint, including auth headers, response codes, and payload validation.