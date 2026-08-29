# SOP — Plan Validation

> Layer 1 document. `tools/validate_plan.py` implements this.

## Goal

Decide whether a generated plan is trustworthy enough to show the user. This is
the gate that makes an LLM's probabilistic output safe to hand to a QA engineer.

Two tiers of check:

- **Structural** — does the JSON match the `LLM.md` section 3 schema? A failure here means the plan cannot be rendered. Hard error.
- **Semantic** — does the plan obey the grounding and coverage rules? A failure here means the plan renders but is not trustworthy.

Both tiers feed the single permitted retry described in the generation SOP.

## Input

Parsed plan dict, plus the normalized issue it was generated from.

## Output

```json
{
  "valid": false,
  "errors": ["structural or coverage failures that must trigger a retry"],
  "warnings": ["quality issues worth surfacing but not worth a retry"],
  "stats": { "test_case_count": 12, "ac_count": 4, "ac_covered": 3, "coverage_pct": 75.0 }
}
```

## Structural Checks

1. Every required top-level key is present: `plan_id`, `source_issue`, `title`, `overview`, `scope`, `assumptions`, `test_strategy`, `test_environments`, `test_data_requirements`, `entry_criteria`, `exit_criteria`, `test_cases`, `risks`, `traceability_matrix`, `coverage_gaps`.
2. `scope` is an object holding `in_scope` and `out_of_scope` arrays.
3. `test_cases` is a non-empty array unless the issue genuinely has no testable content, in which case `coverage_gaps` must be non-empty. A plan that is empty **and** silent is invalid.
4. Every test case has `tc_id`, `title`, `type`, `priority`, `traces_to`, `preconditions`, `steps`, `expected_result`.
5. Every step has `step_no`, `action`, `test_data`.
6. `traceability_matrix` rows have `ac_id`, `acceptance_criterion`, `test_case_ids`.

## Semantic Checks

| # | Rule | Severity |
|---|------|----------|
| 1 | `source_issue` matches the issue actually fetched | error |
| 2 | Every `tc_id` matches `TC-{ISSUE_KEY}-\d{3}` | error |
| 3 | `tc_id` values are unique | error |
| 4 | `tc_id` sequence starts at 001 and has no gaps | warning |
| 5 | Every acceptance criterion appears in the traceability matrix | error |
| 6 | Every matrix row lists at least one test case id | error |
| 7 | Every id in the matrix refers to a test case that exists | error |
| 8 | Every test case `traces_to` is non-empty | error |
| 9 | `priority` is one of P0, P1, P2, P3 | warning |
| 10 | `type` is one of the eight allowed values | warning |
| 11 | Steps are numbered from 1 without gaps | warning |
| 12 | `expected_result` is longer than 10 characters and is not "it works" | warning |
| 13 | Plan has at least one P0 case when acceptance criteria exist | warning |
| 14 | Issue had acceptance criteria but the plan lists none | error |
| 15 | Plan is empty and `coverage_gaps` is also empty | error |

Rule 5 is the one that matters most. An uncovered acceptance criterion is the
exact failure mode this whole project exists to prevent, so it is an error that
forces a retry, never a warning.

## Edge Cases

| Case | Behavior |
|------|----------|
| Issue had zero acceptance criteria | Rules 5 and 14 are skipped. Rule 15 still applies. |
| Issue had no description and no criteria | An empty `test_cases` is acceptable **only** with a populated `coverage_gaps`. |
| Model invents an AC not in the input | Warning, not an error. Recorded so the user can see it was not grounded. |
| Model returns 200 test cases for a one-line bug | Warning at over 50 cases. Not blocked. |
| Duplicate `tc_id` | Error. Breaks traceability. |

## Invariants

1. No LLM call. Pure function of plan plus normalized issue.
2. Never raises. Every problem is reported as a string in `errors` or `warnings`.
3. Error messages name the specific offending id or field, never just "invalid plan".
