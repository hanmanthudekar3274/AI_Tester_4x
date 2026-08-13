import json
from dataclasses import dataclass, field
from typing import Callable

from llm.llm_router import LLMRouter
from prompts.test_plan_prompts import (
    REQUIREMENTS_EXTRACTION,
    DISCUSSION_ANALYSIS,
    TEST_PLAN_GENERATION,
)


MAX_CONTEXT_CHARS = 48_000  # ~12 000 tokens at ~4 chars/token


@dataclass
class AnalysisResult:
    unified_context: str = ""
    requirements_json: dict = field(default_factory=dict)
    discussion_json: dict = field(default_factory=dict)
    test_plan_markdown: str = ""
    error: str = ""


class AnalyzerAgent:
    """
    4-step pipeline: Fuse → Extract → Analyze → Generate.

    Each step calls the active LLM backend via LLMRouter.
    """

    def __init__(self, router: LLMRouter):
        self.router = router

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(
        self,
        context_blocks: list[str],
        feature_name: str = "",
        product: str = "",
        release: str = "",
        team_size: str = "",
        timeline: str = "",
        on_step: Callable[[str], None] | None = None,
    ) -> AnalysisResult:
        result = AnalysisResult()

        def notify(msg: str):
            if on_step:
                on_step(msg)

        try:
            # Step 1 — FUSE
            notify("Fusing context blocks…")
            result.unified_context = self._fuse(context_blocks)

            # Step 2 — EXTRACT REQUIREMENTS
            notify("Extracting requirements (LLM call 1/3)…")
            result.requirements_json = self._extract_requirements(result.unified_context)

            # Step 3 — ANALYZE DISCUSSIONS
            notify("Analysing discussions (LLM call 2/3)…")
            result.discussion_json = self._analyze_discussions(result.unified_context)

            # Step 4 — GENERATE TEST PLAN
            notify("Generating test plan (LLM call 3/3)…")
            result.test_plan_markdown = self._generate_test_plan(
                result.requirements_json,
                result.discussion_json,
                feature_name=feature_name,
                product=product,
                release=release,
                team_size=team_size,
                timeline=timeline,
            )

            notify("Done.")

        except Exception as exc:
            result.error = str(exc)

        return result

    # ------------------------------------------------------------------
    # Pipeline steps
    # ------------------------------------------------------------------

    def _fuse(self, blocks: list[str]) -> str:
        combined = "\n\n".join(b.strip() for b in blocks if b and b.strip())
        if len(combined) > MAX_CONTEXT_CHARS:
            combined = combined[:MAX_CONTEXT_CHARS] + "\n\n[...context truncated for token budget]"
        return combined

    def _extract_requirements(self, unified_context: str) -> dict:
        prompt = REQUIREMENTS_EXTRACTION
        user_msg = prompt["user_template"].format(unified_context=unified_context)
        raw = self.router.complete(prompt["system"], user_msg, max_tokens=4096)
        return self._parse_json(raw)

    def _analyze_discussions(self, unified_context: str) -> dict:
        prompt = DISCUSSION_ANALYSIS
        user_msg = prompt["user_template"].format(unified_context=unified_context)
        raw = self.router.complete(prompt["system"], user_msg, max_tokens=2048)
        return self._parse_json(raw)

    def _generate_test_plan(
        self,
        requirements_json: dict,
        discussion_json: dict,
        **kwargs,
    ) -> str:
        prompt = TEST_PLAN_GENERATION
        user_msg = prompt["user_template"].format(
            requirements_json=json.dumps(requirements_json, indent=2),
            discussion_json=json.dumps(discussion_json, indent=2),
            feature_name=kwargs.get("feature_name", ""),
            product=kwargs.get("product", ""),
            release=kwargs.get("release", ""),
            team_size=kwargs.get("team_size", ""),
            timeline=kwargs.get("timeline", ""),
        )
        return self.router.complete(prompt["system"], user_msg, max_tokens=8192)

    # ------------------------------------------------------------------

    def _parse_json(self, raw: str) -> dict:
        """Extract and parse the first JSON object found in the LLM response."""
        raw = raw.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rsplit("```", 1)[0]
        try:
            return json.loads(raw.strip())
        except json.JSONDecodeError:
            return {"raw_response": raw, "parse_error": "LLM did not return valid JSON"}
