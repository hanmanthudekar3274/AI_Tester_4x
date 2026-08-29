"""Layer 2 - Navigation.

Routes data between tools in the fixed order defined in LLM.md section 5:

    issue_key -> fetch -> normalize -> generate -> validate -> format

This layer does no data transformation of its own. Each stage writes its output
to .tmp/runs/{issue_key}/ so any stage can be re-run in isolation against the
previous stage's output.

Also usable as a CLI:
    python -m tools.pipeline --issue QA-123 --format markdown
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Callable

from . import (
    config_store,
    format_docx,
    format_markdown,
    generate_test_plan,
    jira_client,
    llm_client,
    normalize_issue,
)

STAGES = ("fetch", "normalize", "generate", "format")


class PipelineError(Exception):
    """A stage failed. The message names which one."""

    def __init__(self, stage: str, message: str) -> None:
        super().__init__(f"[{stage}] {message}")
        self.stage = stage
        self.detail = message


def run(
    issue_key: str,
    config: dict[str, str] | None = None,
    on_stage: Callable[[str, str], None] | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Run the full pipeline. Returns plan, validation, markdown, and stats.

    `on_stage(stage, message)` is called before each stage so the UI can show
    progress. It is optional so the CLI can pass nothing.
    """
    config = config if config is not None else config_store.load_config()

    missing = config_store.missing_required(config)
    if missing:
        raise PipelineError(
            "preflight",
            "These settings are required before a plan can be generated: "
            + ", ".join(missing)
            + ". Set them on the Settings page.",
        )

    def announce(stage: str, message: str) -> None:
        if on_stage:
            on_stage(stage, message)

    # --- Stage 1: fetch -------------------------------------------------
    announce("fetch", f"Fetching {issue_key} from Jira")
    try:
        resolved_key = jira_client.resolve_issue_key(issue_key, config)
        raw = jira_client.fetch_issue(resolved_key, config, force_refresh=force_refresh)
    except jira_client.JiraClientError as exc:
        raise PipelineError("fetch", str(exc)) from exc

    # --- Stage 2: normalize ---------------------------------------------
    announce("normalize", "Normalizing issue data")
    normalized = normalize_issue.normalize(raw)
    generate_test_plan.save_run(resolved_key, "normalized.json", normalized)

    quality = normalized.get("quality", {})
    if not quality.get("has_description") and not quality.get("has_acceptance_criteria"):
        # Not fatal. The generator returns a minimal plan whose coverage_gaps
        # explain the absence, which is more useful than refusing outright.
        announce(
            "normalize",
            f"{resolved_key} has no description and no acceptance criteria. "
            "The plan will be thin and will record this as a gap.",
        )

    # --- Stage 3 and 4: generate and validate ---------------------------
    announce("generate", "Generating the test plan")
    llm = llm_client.from_config(config)
    try:
        result = generate_test_plan.generate(normalized, config, llm=llm)
    except generate_test_plan.GenerationError as exc:
        raise PipelineError("generate", str(exc)) from exc

    plan = result["plan"]
    plan.setdefault("url", normalized.get("issue", {}).get("url"))
    generate_test_plan.save_run(resolved_key, "plan.json", plan)
    generate_test_plan.save_run(resolved_key, "validation.json", result["validation"])

    # --- Stage 5: format -------------------------------------------------
    announce("format", "Rendering output")
    markdown = format_markdown.render(plan, result["validation"], model=llm.model)

    return {
        "issue_key": resolved_key,
        "normalized": normalized,
        "plan": plan,
        "validation": result["validation"],
        "markdown": markdown,
        "usage": result["usage"],
        "attempts": result["attempts"],
        "model": llm.model,
    }


def to_docx(result: dict[str, Any]) -> bytes:
    """Render the DOCX on demand. Kept out of run() so a run does not pay the
    cost when the user only wants Markdown."""
    return format_docx.render(result["plan"], result["validation"], model=result.get("model"))


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.pipeline",
        description="Generate a test plan from a Jira issue.",
    )
    parser.add_argument("--issue", required=True, help="Jira issue key, e.g. QA-123")
    parser.add_argument(
        "--format", choices=("markdown", "docx"), default="markdown",
        help="Output format. Default markdown.",
    )
    parser.add_argument("--out", help="Output file path. Defaults to stdout for markdown.")
    parser.add_argument(
        "--refresh", action="store_true", help="Ignore the cached Jira response."
    )
    args = parser.parse_args(argv)

    config_store.init()

    def progress(stage: str, message: str) -> None:
        print(f"  [{stage}] {message}", file=sys.stderr)

    try:
        result = run(args.issue, on_stage=progress, force_refresh=args.refresh)
    except PipelineError as exc:
        print(f"Error {exc}", file=sys.stderr)
        return 1

    stats = result["validation"]["stats"]
    print(
        f"  [done] {stats.get('test_case_count', 0)} test cases, "
        f"{stats.get('coverage_pct', 0)}% criteria coverage, "
        f"{result['attempts']} attempt(s)",
        file=sys.stderr,
    )
    for warning in result["validation"].get("warnings", []):
        print(f"  [warn] {warning}", file=sys.stderr)

    if args.format == "docx":
        out_path = Path(args.out or f"{result['issue_key']}-test-plan.docx")
        out_path.write_bytes(to_docx(result))
        print(f"Wrote {out_path}", file=sys.stderr)
        return 0

    if args.out:
        Path(args.out).write_text(result["markdown"], encoding="utf-8")
        print(f"Wrote {args.out}", file=sys.stderr)
    else:
        print(result["markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
