# SOP — Output Formatting

> Layer 1 document. `tools/format_markdown.py` and `tools/format_docx.py` implement this.

## Goal

Render a validated plan JSON into a document a QA engineer can read and hand to
a team. Deterministic. The LLM never produces presentation output.

## Section Order

Fixed, because a reader scanning many plans should find the same thing in the
same place every time.

1. Title and metadata (issue key, link, generated timestamp, author, model)
2. **Coverage summary** — case count, criteria covered, coverage percentage
3. **Coverage gaps** — when non-empty
4. Overview
5. Scope, in and out
6. Assumptions, with `[INFERRED]` markers preserved
7. Test strategy
8. Environments and test data requirements
9. Entry and exit criteria
10. Test cases
11. Risks
12. Traceability matrix

Gaps sit at position 3, above the test cases, deliberately. A plan the reader
must not trust blindly must not look complete at a glance. Burying the gaps at
the bottom would do exactly that.

## Test Case Rendering

Markdown renders each case as a heading plus a step table:

```
### TC-QA-1-001 — Reset email is delivered within 30 seconds
**Type:** Functional  **Priority:** P0  **Traces to:** AC-1

**Preconditions:** A registered account with a verified email exists

| # | Action | Test Data |
|---|--------|-----------|
| 1 | Navigate to the login page | - |

**Expected Result:** A reset email arrives within 30 seconds
```

An inferred case is prefixed `[INFERRED]` in its heading.

DOCX renders the same content: heading 3 per case, a metadata line, a
three-column step table styled `Table Grid`, then the expected result.

## Escaping

Markdown: pipe characters inside table cells are escaped as `\|`, and newlines
inside cells become `<br>`. An unescaped pipe silently breaks the table, which
is the most likely way a generated plan renders wrong.

DOCX: `python-docx` handles escaping. Newlines are written as separate runs.

## Edge Cases

| Case | Behavior |
|------|----------|
| A section is empty | The heading is omitted entirely rather than shown empty |
| `coverage_gaps` is empty | The section is omitted. Absence means no known gaps |
| A test case has no steps | Renders with a "No steps provided" note rather than an empty table |
| A field is `None` | Renders as an em dash |
| Text contains a pipe | Escaped |
| Plan has 200 cases | All rendered. Truncation would hide test coverage |

## Invariants

1. No LLM call. Pure function of the plan dict.
2. Never raises on a missing key. Every access is null-safe, because the
   formatter must still render a plan that only passed validation with warnings.
3. Markdown and DOCX render the same content in the same order. They must not
   drift.
