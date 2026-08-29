# SOP — Normalization

> Layer 1 document. `tools/normalize_issue.py` implements this.

## Goal

Turn the raw Jira payload into the flat input schema in `LLM.md` section 2.
This isolates every downstream stage from ADF nesting, custom field IDs, and
Jira version differences.

## Input

`.tmp/cache/{issue_key}.json` as produced by `tools/jira_client.py`.

## Output

The `LLM.md` section 2 input schema, written to `.tmp/runs/{issue_key}/normalized.json`.

## Procedure

### 1. Flatten ADF to plain text

Jira Cloud API v3 returns rich text as an Atlassian Document Format tree. Walk
it recursively.

| Node type | Handling |
|-----------|----------|
| `text` | Emit `node["text"]` |
| `hardBreak` | Emit a newline |
| `paragraph`, `heading` | Join children, then append a blank line |
| `bulletList`, `orderedList` | Join children with newlines |
| `listItem` | Prefix `- `, join children |
| `codeBlock` | Wrap children in triple backticks |
| `table` | Emit rows as pipe-separated lines |
| `mediaSingle`, `media` | Emit `[attachment: {filename}]` |
| `inlineCard` | Emit the `url` attribute |
| anything else | Recurse into `content`, join with a space |

A plain string input is returned unchanged, so Server-style payloads survive.
`None` returns an empty string.

### 2. Extract acceptance criteria

Ordered fallback. Stop at the first that yields results.

1. The discovered custom field from `field_map.acceptance_criteria`. Flatten it, then split.
2. A heading in the description matching `acceptance criteria`, `acceptance criterion`, or `AC:` case-insensitive. Take the lines that follow until the next heading.
3. Gherkin lines anywhere in the description: lines starting `Given `, `When `, `Then `. Consecutive Given/When/Then lines group into one criterion.
4. Nothing found. Return `[]`. The generator records this as a coverage gap. It is not an error here.

**Splitting rules.** One criterion per bullet, per numbered item, or per blank-line-separated block. Bullet markers `-`, `*`, `•` and leading numbering `1.` / `1)` are stripped. Blank entries and entries shorter than three characters are dropped.

### 3. Map the remaining fields

Direct reads with null-safe access, per the `findings.md` section 4 table.
Every key in the schema is always present. Missing scalars become `null`,
missing lists become `[]`. Keys are never omitted, so downstream code never
needs `.get()` guards.

### 4. Record quality flags

Not part of the LLM payload. Consumed by the chat screen to warn the user
before generation, and by the generator to seed `coverage_gaps`.

```json
{
  "has_description": true,
  "has_acceptance_criteria": false,
  "acceptance_criteria_source": "description_heading",
  "comments_truncated": false,
  "is_epic": false
}
```

## Edge Cases

| Case | Behavior |
|------|----------|
| Description is `null` | `description` is `""`, `has_description` false |
| Description is a plain string, not ADF | Passed through unchanged |
| ADF contains an unknown node type | Recurse into `content` generically. Never crash on an unrecognized type. |
| Acceptance criteria field holds one blob of text | Split per the splitting rules above |
| Comment body is ADF | Flattened with the same walker |
| Subtask has no status | `status` is `null`, entry retained |
| Deeply nested or cyclic ADF | Recursion capped at depth 50; beyond that the subtree is dropped |

## Invariants

1. No LLM call.
2. Pure function of its input. Same payload in, same normalized output.
3. Never raises on malformed content. Degrades to an empty string or list and records a quality flag.
4. Output always contains every key in the `LLM.md` section 2 schema.
