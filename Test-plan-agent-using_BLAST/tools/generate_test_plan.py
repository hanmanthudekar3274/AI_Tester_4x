"""Generate a test plan from a normalized Jira issue.

Implements architecture/test_plan_generation_sop.md. This is the ONLY tool in
the pipeline that calls an LLM.

The system prompt is loaded from the SOP markdown at runtime. It is never
duplicated as a string literal here, so editing the prompt means editing the
SOP -- which is the BLAST Golden Rule applied to prompts.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config_store, llm_client, validate_plan
from .llm_client import LLMError

SOP_PATH = config_store.PROJECT_ROOT / "architecture" / "test_plan_generation_sop.md"

_SYSTEM_RE = re.compile(
    r"<!--\s*SYSTEM_PROMPT_START\s*-->(.*?)<!--\s*SYSTEM_PROMPT_END\s*-->", re.DOTALL
)
_RETRY_RE = re.compile(
    r"<!--\s*RETRY_PROMPT_START\s*-->(.*?)<!--\s*RETRY_PROMPT_END\s*-->", re.DOTALL
)


class GenerationError(Exception):
    """Raised when a plan could not be produced after the permitted retry."""


def _load_prompt(pattern: re.Pattern[str], label: str) -> str:
    if not SOP_PATH.exists():
        raise GenerationError(
            f"The generation SOP is missing at {SOP_PATH}. The prompt lives in "
            "that file and cannot be reconstructed from code."
        )
    match = pattern.search(SOP_PATH.read_text(encoding="utf-8"))
    if not match or not match.group(1).strip():
        raise GenerationError(
            f"Could not find the {label} markers in {SOP_PATH.name}."
        )
    return match.group(1).strip()


def load_system_prompt() -> str:
    return _load_prompt(_SYSTEM_RE, "SYSTEM_PROMPT")


def load_retry_prompt() -> str:
    return _load_prompt(_RETRY_RE, "RETRY_PROMPT")


def build_user_prompt(
    normalized: dict[str, Any], budget_chars: int | None = None
) -> tuple[str, list[str]]:
    """Build the user message and report anything trimmed to fit the budget.

    Returns (prompt, notes). Notes name what was dropped so the caller can
    surface it: silently truncating a ticket would mean silently reducing test
    coverage, which is exactly what this project refuses to do.

    Quality flags ride along so the model knows what was missing rather than
    having to guess from absence.
    """
    issue = dict(normalized.get("issue", {}))
    notes: list[str] = []

    def payload_for(current: dict[str, Any]) -> str:
        return json.dumps(
            {
                "issue": current,
                "quality_flags": normalized.get("quality", {}),
                "required_output_schema": _schema_hint(),
            },
            indent=2,
            ensure_ascii=False,
        )

    prompt = payload_for(issue)
    if budget_chars is None or len(prompt) <= budget_chars:
        return prompt, notes

    # Trim in order of least value to a test plan. Acceptance criteria,
    # summary, and description are never dropped -- they are the plan.
    for label, key, keep in (
        ("attachments", "attachments", 0),
        ("linked issues", "linked_issues", 3),
        ("comments", "comments", 5),
        ("subtasks", "subtasks", 10),
    ):
        if len(prompt) <= budget_chars:
            break
        items = issue.get(key) or []
        if len(items) > keep:
            notes.append(f"Dropped {len(items) - keep} of {len(items)} {label} to fit the token budget.")
            issue[key] = items[:keep]
            prompt = payload_for(issue)

    if len(prompt) > budget_chars:
        description = issue.get("description") or ""
        overflow = len(prompt) - budget_chars
        if len(description) > overflow + 500:
            issue["description"] = description[: len(description) - overflow - 200] + "\n[TRUNCATED]"
            notes.append(
                f"Truncated the description by about {overflow} characters to fit "
                "the token budget. Coverage may be incomplete."
            )
            prompt = payload_for(issue)

    return prompt, notes


def _schema_hint() -> dict[str, Any]:
    """A compact shape reminder sent with every request.

    Restating the schema next to the data measurably reduces missing-key
    failures compared with relying on the system prompt alone.
    """
    return {
        "plan_id": "TP-{ISSUE_KEY}",
        "source_issue": "{ISSUE_KEY}",
        "title": "string",
        "generated_at": "ISO-8601 string",
        "overview": "string",
        "scope": {"in_scope": ["string"], "out_of_scope": ["string"]},
        "assumptions": ["string"],
        "test_strategy": "string",
        "test_environments": [{"name": "string", "notes": "string"}],
        "test_data_requirements": ["string"],
        "entry_criteria": ["string"],
        "exit_criteria": ["string"],
        "test_cases": [{
            "tc_id": "TC-{ISSUE_KEY}-001",
            "title": "string",
            "type": "Functional|Negative|Boundary|Integration|Regression|Usability|Performance|Security",
            "priority": "P0|P1|P2|P3",
            "traces_to": "AC-1 | description | subtask key | comment",
            "preconditions": "string",
            "steps": [{"step_no": 1, "action": "string", "test_data": "string or -"}],
            "expected_result": "string",
            "inferred": False,
        }],
        "risks": [{"risk": "string", "severity": "Low|Medium|High",
                   "mitigation": "string", "source": "string"}],
        "traceability_matrix": [{"ac_id": "AC-1", "acceptance_criterion": "string",
                                 "test_case_ids": ["TC-{ISSUE_KEY}-001"]}],
        "coverage_gaps": ["string"],
    }


def generate(
    normalized: dict[str, Any],
    config: dict[str, str] | None = None,
    llm: llm_client.BaseLLM | None = None,
) -> dict[str, Any]:
    """Generate and validate a plan. At most two LLM calls.

    Returns {"plan": dict, "validation": dict, "usage": dict, "attempts": int}.
    Raises GenerationError if no valid plan survives the retry.
    """
    config = config if config is not None else config_store.load_config()
    llm = llm if llm is not None else llm_client.from_config(config)

    system_prompt = load_system_prompt()

    # The input budget must account for the system prompt, which shares the
    # same tokens-per-minute allowance as the issue data.
    budget_chars = None
    if hasattr(llm, "input_budget"):
        budget_chars = max(llm.input_budget() - len(system_prompt), 1500)

    user_prompt, trim_notes = build_user_prompt(normalized, budget_chars)
    max_tokens = config_store.get_int("GROQ_MAX_TOKENS", 6000)

    issue_key = normalized.get("issue", {}).get("issue_key", "UNKNOWN")
    extra_messages: list[dict[str, str]] = []
    usage_log: list[dict[str, Any]] = []
    last_result: dict[str, Any] | None = None
    last_plan: Any = None

    for attempt in (1, 2):
        try:
            raw = llm.complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                json_mode=True,
                extra_messages=extra_messages or None,
            )
        except LLMError as exc:
            raise GenerationError(str(exc)) from exc

        usage_log.append(dict(getattr(llm, "last_usage", {}), attempt=attempt))

        try:
            plan = llm_client.parse_json_response(raw)
            parse_errors: list[str] = []
        except LLMError as exc:
            plan = None
            parse_errors = [str(exc)]

        if plan is not None:
            plan.setdefault("generated_at", datetime.now(timezone.utc).isoformat())
            plan.setdefault("source_issue", issue_key)
            author = str(config.get("DISPLAY_NAME", "")).strip()
            if author:
                plan.setdefault("author", author)

            result = validate_plan.validate(plan, normalized)
        else:
            result = {"valid": False, "errors": parse_errors, "warnings": [], "stats": {}}

        last_plan, last_result = plan, result

        if result["valid"]:
            if trim_notes:
                # Trimming input reduces what the plan could possibly cover, so
                # it belongs in the gaps the reader sees, not only in a log.
                gaps = plan.setdefault("coverage_gaps", [])
                if isinstance(gaps, list):
                    gaps.extend(trim_notes)
            return {
                "plan": plan,
                "validation": result,
                "usage": usage_log,
                "attempts": attempt,
                "trim_notes": trim_notes,
            }

        if attempt == 1:
            # The single permitted retry. The failure is fed back verbatim so
            # the model corrects the specific problem rather than regenerating
            # blindly.
            retry_template = load_retry_prompt()
            extra_messages = [
                {"role": "assistant", "content": raw[:4000]},
                {
                    "role": "user",
                    "content": retry_template.replace(
                        "{errors}", "\n".join(f"- {e}" for e in result["errors"])
                    ),
                },
            ]

    assert last_result is not None
    raise GenerationError(
        "The model could not produce a valid test plan after one retry. "
        "Remaining problems:\n"
        + "\n".join(f"  - {e}" for e in last_result["errors"][:10])
    )


def save_run(issue_key: str, name: str, data: Any) -> Path:
    """Persist a stage output to .tmp/runs/{issue_key}/ for debugging.

    Stage outputs are files, not shared memory, so any stage can be re-run in
    isolation against the previous stage's output.
    """
    run_dir = config_store.PROJECT_ROOT / ".tmp" / "runs" / issue_key
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / name
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
