"""Render a validated plan as Markdown.

Implements architecture/output_formatter_sop.md. Pure function of the plan
dict. Null-safe everywhere: a plan that passed validation with warnings must
still render.
"""

from __future__ import annotations

from typing import Any

DASH = "—"


def _cell(value: Any) -> str:
    """Escape a value for use inside a Markdown table cell.

    An unescaped pipe silently breaks the table, which is the single most
    likely way a generated plan renders wrong.
    """
    if value is None or value == "":
        return DASH
    return str(value).replace("|", r"\|").replace("\n", "<br>").strip()


def _text(value: Any) -> str:
    if value is None or value == "":
        return DASH
    return str(value).strip()


def _bullets(items: Any) -> str:
    if not isinstance(items, list) or not items:
        return ""
    lines = []
    for item in items:
        if isinstance(item, dict):
            name = item.get("name") or item.get("risk") or ""
            notes = item.get("notes") or item.get("mitigation") or ""
            lines.append(f"- **{_text(name)}** {notes}".rstrip())
        else:
            lines.append(f"- {_text(item)}")
    return "\n".join(lines)


def _section(title: str, body: str) -> str:
    """Emit a section, or nothing when the body is empty.

    Empty headings are omitted rather than shown, per the SOP.
    """
    body = (body or "").strip()
    return f"## {title}\n\n{body}\n\n" if body else ""


def render(plan: dict[str, Any], validation: dict[str, Any] | None = None,
           model: str | None = None) -> str:
    plan = plan or {}
    validation = validation or {}
    stats = validation.get("stats", {})
    out: list[str] = []

    issue_key = _text(plan.get("source_issue"))
    out.append(f"# {_text(plan.get('title')) }\n")

    meta = [f"**Issue:** {issue_key}"]
    if plan.get("url"):
        meta.append(f"**Link:** {plan['url']}")
    if plan.get("author"):
        meta.append(f"**Author:** {plan['author']}")
    if plan.get("generated_at"):
        meta.append(f"**Generated:** {plan['generated_at']}")
    if model:
        meta.append(f"**Model:** {model}")
    out.append("  \n".join(meta) + "\n")

    # 2. Coverage summary
    if stats:
        out.append(
            "## Coverage Summary\n\n"
            f"| Metric | Value |\n|---|---|\n"
            f"| Test cases | {stats.get('test_case_count', 0)} |\n"
            f"| Acceptance criteria | {stats.get('ac_count', 0)} |\n"
            f"| Criteria covered | {stats.get('ac_covered', 0)} |\n"
            f"| Coverage | {stats.get('coverage_pct', 0)}% |\n"
            f"| Inferred cases | {stats.get('inferred_count', 0)} |\n\n"
        )

    # 3. Gaps and warnings sit above the test cases on purpose.
    gaps = plan.get("coverage_gaps") or []
    if gaps:
        out.append(
            "## ⚠️ Coverage Gaps\n\n"
            "The issue did not contain enough information to test these points. "
            "They need a decision before this plan is complete.\n\n"
            + _bullets(gaps) + "\n\n"
        )

    warnings = validation.get("warnings") or []
    if warnings:
        out.append("## Quality Warnings\n\n" + _bullets(warnings) + "\n\n")

    out.append(_section("Overview", _text(plan.get("overview"))))

    scope = plan.get("scope")
    if not isinstance(scope, dict):
        scope = {}
    scope_body = ""
    if scope.get("in_scope"):
        scope_body += "**In scope**\n\n" + _bullets(scope["in_scope"]) + "\n\n"
    if scope.get("out_of_scope"):
        scope_body += "**Out of scope**\n\n" + _bullets(scope["out_of_scope"])
    out.append(_section("Scope", scope_body))

    out.append(_section("Assumptions", _bullets(plan.get("assumptions"))))
    out.append(_section("Test Strategy", _text(plan.get("test_strategy"))
                        if plan.get("test_strategy") else ""))
    out.append(_section("Test Environments", _bullets(plan.get("test_environments"))))
    out.append(_section("Test Data Requirements", _bullets(plan.get("test_data_requirements"))))
    out.append(_section("Entry Criteria", _bullets(plan.get("entry_criteria"))))
    out.append(_section("Exit Criteria", _bullets(plan.get("exit_criteria"))))

    out.append(_render_cases(plan.get("test_cases")))
    out.append(_render_risks(plan.get("risks")))
    out.append(_render_matrix(plan.get("traceability_matrix")))

    return "".join(part for part in out if part).rstrip() + "\n"


def _render_cases(cases: Any) -> str:
    if not isinstance(cases, list) or not cases:
        return ""
    out = ["## Test Cases\n\n"]

    for case in cases:
        if not isinstance(case, dict):
            continue
        marker = "[INFERRED] " if case.get("inferred") else ""
        out.append(f"### {_text(case.get('tc_id'))} {DASH} {marker}{_text(case.get('title'))}\n\n")
        out.append(
            f"**Type:** {_text(case.get('type'))} &nbsp;&nbsp; "
            f"**Priority:** {_text(case.get('priority'))} &nbsp;&nbsp; "
            f"**Traces to:** {_text(case.get('traces_to'))}\n\n"
        )
        if case.get("preconditions"):
            out.append(f"**Preconditions:** {_text(case['preconditions'])}\n\n")

        steps = case.get("steps")
        if isinstance(steps, list) and steps:
            out.append("| # | Action | Test Data |\n|---|--------|-----------|\n")
            for index, step in enumerate(steps, start=1):
                if not isinstance(step, dict):
                    continue
                out.append(
                    f"| {_cell(step.get('step_no', index))} "
                    f"| {_cell(step.get('action'))} "
                    f"| {_cell(step.get('test_data'))} |\n"
                )
            out.append("\n")
        else:
            out.append("_No steps provided._\n\n")

        out.append(f"**Expected Result:** {_text(case.get('expected_result'))}\n\n")

    return "".join(out)


def _render_risks(risks: Any) -> str:
    if not isinstance(risks, list) or not risks:
        return ""
    out = ["## Risks\n\n| Risk | Severity | Mitigation | Source |\n|---|---|---|---|\n"]
    for risk in risks:
        if not isinstance(risk, dict):
            out.append(f"| {_cell(risk)} | {DASH} | {DASH} | {DASH} |\n")
            continue
        out.append(
            f"| {_cell(risk.get('risk'))} | {_cell(risk.get('severity'))} "
            f"| {_cell(risk.get('mitigation'))} | {_cell(risk.get('source'))} |\n"
        )
    return "".join(out) + "\n"


def _render_matrix(matrix: Any) -> str:
    if not isinstance(matrix, list) or not matrix:
        return ""
    out = ["## Traceability Matrix\n\n| AC | Acceptance Criterion | Test Cases |\n|---|---|---|\n"]
    for row in matrix:
        if not isinstance(row, dict):
            continue
        ids = row.get("test_case_ids")
        ids_text = ", ".join(str(i) for i in ids) if isinstance(ids, list) and ids else DASH
        out.append(
            f"| {_cell(row.get('ac_id'))} "
            f"| {_cell(row.get('acceptance_criterion'))} "
            f"| {_cell(ids_text)} |\n"
        )
    return "".join(out) + "\n"
