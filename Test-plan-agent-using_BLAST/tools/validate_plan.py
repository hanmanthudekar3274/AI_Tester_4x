"""Validate a generated test plan.

Implements architecture/validation_sop.md.

Pure function of (plan, normalized_issue). Never raises: every problem is
reported as a string. Errors trigger the single permitted generation retry;
warnings are surfaced to the user but do not block.
"""

from __future__ import annotations

import re
from typing import Any

REQUIRED_TOP_LEVEL = (
    "plan_id", "source_issue", "title", "overview", "scope", "assumptions",
    "test_strategy", "test_environments", "test_data_requirements",
    "entry_criteria", "exit_criteria", "test_cases", "risks",
    "traceability_matrix", "coverage_gaps",
)

REQUIRED_CASE_KEYS = (
    "tc_id", "title", "type", "priority", "traces_to", "preconditions",
    "steps", "expected_result",
)

ALLOWED_PRIORITIES = {"P0", "P1", "P2", "P3"}
ALLOWED_TYPES = {
    "Functional", "Negative", "Boundary", "Integration",
    "Regression", "Usability", "Performance", "Security",
}

WEAK_EXPECTED = {"it works", "works", "success", "ok", "pass", "as expected", "no error"}
MAX_REASONABLE_CASES = 50


def validate(plan: Any, normalized: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    issue = normalized.get("issue", {})
    issue_key = issue.get("issue_key", "UNKNOWN")
    criteria = issue.get("acceptance_criteria") or []

    if not isinstance(plan, dict):
        return {
            "valid": False,
            "errors": [f"Plan must be a JSON object, got {type(plan).__name__}."],
            "warnings": [],
            "stats": {},
        }

    _check_structure(plan, errors)
    cases = plan.get("test_cases") if isinstance(plan.get("test_cases"), list) else []
    matrix = plan.get("traceability_matrix") if isinstance(plan.get("traceability_matrix"), list) else []
    gaps = plan.get("coverage_gaps") if isinstance(plan.get("coverage_gaps"), list) else []

    _check_cases(cases, issue_key, errors, warnings)
    covered = _check_coverage(matrix, cases, criteria, errors, warnings)
    _check_emptiness(cases, gaps, criteria, errors, warnings)

    if plan.get("source_issue") and plan["source_issue"] != issue_key:
        errors.append(
            f"source_issue is '{plan['source_issue']}' but the fetched issue was '{issue_key}'."
        )

    if criteria and cases and not any(
        str(c.get("priority", "")).upper() == "P0" for c in cases if isinstance(c, dict)
    ):
        warnings.append(
            "No P0 test case exists even though the issue has acceptance criteria. "
            "Core paths should be P0."
        )

    if len(cases) > MAX_REASONABLE_CASES:
        warnings.append(
            f"{len(cases)} test cases generated. Verify the plan is proportional to the issue."
        )

    ac_count = len(criteria)
    stats = {
        "test_case_count": len(cases),
        "ac_count": ac_count,
        "ac_covered": len(covered),
        "coverage_pct": round(100.0 * len(covered) / ac_count, 1) if ac_count else 100.0,
        "gap_count": len(gaps),
        "inferred_count": sum(
            1 for c in cases if isinstance(c, dict) and c.get("inferred") is True
        ),
    }

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
    }


# --------------------------------------------------------------------------
# Structural
# --------------------------------------------------------------------------

def _check_structure(plan: dict[str, Any], errors: list[str]) -> None:
    for key in REQUIRED_TOP_LEVEL:
        if key not in plan:
            errors.append(f"Missing required top-level key '{key}'.")

    scope = plan.get("scope")
    if scope is not None:
        if not isinstance(scope, dict):
            errors.append("'scope' must be an object with 'in_scope' and 'out_of_scope'.")
        else:
            for sub in ("in_scope", "out_of_scope"):
                if sub not in scope:
                    errors.append(f"'scope' is missing '{sub}'.")
                elif not isinstance(scope[sub], list):
                    errors.append(f"'scope.{sub}' must be an array.")

    for key in ("test_cases", "traceability_matrix", "coverage_gaps", "assumptions", "risks"):
        if key in plan and not isinstance(plan[key], list):
            errors.append(f"'{key}' must be an array, got {type(plan[key]).__name__}.")


# --------------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------------

def _check_cases(
    cases: list[Any], issue_key: str, errors: list[str], warnings: list[str]
) -> None:
    id_pattern = re.compile(rf"^TC-{re.escape(issue_key)}-\d{{3}}$")
    seen: set[str] = set()
    sequence: list[int] = []

    for index, case in enumerate(cases):
        label = f"test_cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{label} must be an object.")
            continue

        for key in REQUIRED_CASE_KEYS:
            if key not in case:
                errors.append(f"{label} is missing '{key}'.")

        tc_id = str(case.get("tc_id", "")).strip()
        label = tc_id or label

        if tc_id:
            if not id_pattern.match(tc_id):
                errors.append(
                    f"{label} does not match the required format TC-{issue_key}-NNN."
                )
            else:
                sequence.append(int(tc_id.rsplit("-", 1)[1]))
            if tc_id in seen:
                errors.append(f"Duplicate test case id '{tc_id}'. Ids must be unique.")
            seen.add(tc_id)

        if not str(case.get("traces_to", "")).strip():
            errors.append(
                f"{label} has an empty 'traces_to'. Every case must trace to "
                "an acceptance criterion, the description, a subtask, or a comment."
            )

        priority = str(case.get("priority", "")).upper()
        if priority and priority not in ALLOWED_PRIORITIES:
            warnings.append(f"{label} has priority '{priority}'. Expected one of P0-P3.")

        case_type = str(case.get("type", ""))
        if case_type and case_type not in ALLOWED_TYPES:
            warnings.append(
                f"{label} has type '{case_type}'. Expected one of: "
                + ", ".join(sorted(ALLOWED_TYPES))
            )

        expected = str(case.get("expected_result", "")).strip()
        if expected and (len(expected) <= 10 or expected.lower().rstrip(".") in WEAK_EXPECTED):
            warnings.append(
                f"{label} has a vague expected_result: '{expected}'. "
                "It should state one observable outcome."
            )

        _check_steps(case.get("steps"), label, errors, warnings)

    if sequence:
        expected_sequence = list(range(1, len(sequence) + 1))
        if sorted(sequence) != expected_sequence:
            warnings.append(
                "Test case ids are not a gapless sequence starting at 001. "
                f"Found: {sorted(sequence)}"
            )


def _check_steps(steps: Any, label: str, errors: list[str], warnings: list[str]) -> None:
    if steps is None:
        return
    if not isinstance(steps, list):
        errors.append(f"{label} 'steps' must be an array.")
        return
    if not steps:
        warnings.append(f"{label} has no steps.")
        return

    numbers: list[int] = []
    for position, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            errors.append(f"{label} step {position} must be an object.")
            continue
        for key in ("step_no", "action", "test_data"):
            if key not in step:
                errors.append(f"{label} step {position} is missing '{key}'.")
        try:
            numbers.append(int(step.get("step_no", position)))
        except (TypeError, ValueError):
            warnings.append(f"{label} step {position} has a non-numeric step_no.")

    if numbers and numbers != list(range(1, len(numbers) + 1)):
        warnings.append(f"{label} steps are not numbered 1..n without gaps.")


# --------------------------------------------------------------------------
# Coverage
# --------------------------------------------------------------------------

def _check_coverage(
    matrix: list[Any],
    cases: list[Any],
    criteria: list[str],
    errors: list[str],
    warnings: list[str],
) -> set[str]:
    """Return the set of AC ids that are genuinely covered."""
    known_ids = {
        str(c.get("tc_id")) for c in cases if isinstance(c, dict) and c.get("tc_id")
    }
    expected_acs = {f"AC-{i}" for i in range(1, len(criteria) + 1)}
    covered: set[str] = set()

    for index, row in enumerate(matrix):
        if not isinstance(row, dict):
            errors.append(f"traceability_matrix[{index}] must be an object.")
            continue

        ac_id = str(row.get("ac_id", "")).strip()
        if not ac_id:
            errors.append(f"traceability_matrix[{index}] is missing 'ac_id'.")
            continue

        case_ids = row.get("test_case_ids")
        if not isinstance(case_ids, list) or not case_ids:
            errors.append(
                f"Acceptance criterion {ac_id} has no test cases in the "
                "traceability matrix. Every criterion must be covered."
            )
            continue

        unknown = [cid for cid in case_ids if str(cid) not in known_ids]
        if unknown:
            errors.append(
                f"traceability_matrix row {ac_id} references test case id(s) "
                f"{unknown} that do not exist in test_cases."
            )

        if expected_acs and ac_id not in expected_acs:
            warnings.append(
                f"traceability_matrix references {ac_id}, which is not one of the "
                f"{len(criteria)} acceptance criteria found in the issue."
            )

        if any(str(cid) in known_ids for cid in case_ids):
            covered.add(ac_id)

    if criteria:
        uncovered = sorted(expected_acs - covered, key=lambda a: int(a.split("-")[1]))
        for ac_id in uncovered:
            position = int(ac_id.split("-")[1]) - 1
            text = criteria[position] if position < len(criteria) else ""
            preview = (text[:80] + "...") if len(text) > 80 else text
            errors.append(
                f"Acceptance criterion {ac_id} is not covered by any test case: \"{preview}\""
            )

    return covered


# --------------------------------------------------------------------------
# Emptiness
# --------------------------------------------------------------------------

def _check_emptiness(
    cases: list[Any],
    gaps: list[Any],
    criteria: list[str],
    errors: list[str],
    warnings: list[str],
) -> None:
    if cases:
        return
    if gaps:
        warnings.append(
            "The plan contains no test cases. The issue did not carry enough "
            "detail to test. See the coverage gaps."
        )
        return
    errors.append(
        "The plan has no test cases and no coverage gaps. An empty plan must "
        "explain what information was missing."
    )


def format_errors(result: dict[str, Any]) -> str:
    """Render errors for the retry prompt."""
    return "\n".join(f"- {e}" for e in result.get("errors", []))
