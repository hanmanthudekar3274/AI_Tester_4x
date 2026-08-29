"""Token budget regression tests.

Groq bills input and output against one tokens-per-minute allowance, so a
max_tokens at or above the TPM limit is rejected with a 413 before the request
even runs. These tests pin the clamping and trimming behavior that prevents it.

No network access required.
"""

import sys

sys.path.insert(0, r"c:\AI_Tester_4x\Test-plan-agent-using_BLAST")

import json

from tools import generate_test_plan as gen
from tools import llm_client as lc

fails = []


def check(label, cond, detail=""):
    if not cond:
        fails.append(f"{label} {detail}")
    print(("PASS " if cond else "FAIL ") + label + ("" if cond else f"  <- {detail}"))


class Spy(lc.GroqLLM):
    """Captures the kwargs that would have been sent, without calling Groq."""

    def __init__(self, **kw):
        super().__init__(api_key="fake", **kw)
        self.sent = None

    def _client(self):
        spy = self

        class FakeCompletions:
            def create(self, **kwargs):
                spy.sent = kwargs
                raise RuntimeError("stop-before-network")

        class FakeChat:
            completions = FakeCompletions()

        class FakeClient:
            chat = FakeChat()

        return FakeClient()


# --- max_tokens is clamped below the TPM limit ---------------------------
spy = Spy(tpm_limit=8000)
try:
    spy.complete("system", "user", max_tokens=32000)
except lc.LLMError:
    pass
check("oversized max_tokens is clamped", spy.sent is not None and spy.sent["max_tokens"] < 8000,
      spy.sent["max_tokens"] if spy.sent else "no call made")
check("clamped value leaves room for input",
      spy.sent["max_tokens"] <= 8000 - lc.TPM_SAFETY_MARGIN, spy.sent["max_tokens"])

# --- a modest request is left alone --------------------------------------
spy = Spy(tpm_limit=8000)
try:
    spy.complete("sys", "usr", max_tokens=3000)
except lc.LLMError:
    pass
check("reasonable max_tokens is not reduced", spy.sent["max_tokens"] == 3000, spy.sent["max_tokens"])

# --- a huge prompt is refused with an actionable message -----------------
spy = Spy(tpm_limit=8000)
try:
    spy.complete("s" * 200_000, "u", max_tokens=2000)
    check("huge prompt refused", False, "no error raised")
except lc.LLMError as exc:
    msg = str(exc)
    check("huge prompt refused before the network", spy.sent is None)
    check("refusal names the budget", "tokens-per-minute" in msg and "8000" in msg, msg[:120])

# --- a higher tier gets a bigger budget ----------------------------------
small, large = Spy(tpm_limit=8000), Spy(tpm_limit=300_000)
check("higher TPM tier raises the input budget",
      large.input_budget() > small.input_budget() * 5,
      (small.input_budget(), large.input_budget()))

# --- 413 maps to an actionable message -----------------------------------
msg = lc.GroqLLM._explain(Exception("Error code: 413 - Request too large for model"))
check("413 explained actionably", "tokens-per-minute" in msg and "Settings" in msg, msg[:100])

# --- trimming order protects what matters --------------------------------
issue = {
    "issue_key": "QA-9",
    "summary": "Critical summary",
    "description": "D" * 2000,
    "acceptance_criteria": ["AC one must survive", "AC two must survive"],
    "comments": [{"author": "a", "created": "t", "body": "c" * 900} for _ in range(50)],
    "linked_issues": [{"key": f"L-{i}", "summary": "s", "link_type": "blocks"} for i in range(25)],
    "attachments": [{"filename": f"f{i}.png"} for i in range(12)],
    "subtasks": [{"key": f"S-{i}", "summary": "z" * 150} for i in range(25)],
}
normalized = {"issue": issue, "quality": {}}

budget = 12000
prompt, notes = gen.build_user_prompt(normalized, budget)
check("trimmed prompt fits the budget", len(prompt) <= budget, (len(prompt), budget))
check("trimming is reported", len(notes) > 0, notes)

trimmed = json.loads(prompt)["issue"]
check("acceptance criteria never dropped",
      trimmed["acceptance_criteria"] == issue["acceptance_criteria"], trimmed["acceptance_criteria"])
check("summary never dropped", trimmed["summary"] == "Critical summary")
check("attachments dropped first", len(trimmed["attachments"]) == 0, trimmed["attachments"])
check("comments reduced", len(trimmed["comments"]) < 50, len(trimmed["comments"]))

# --- no budget means no trimming -----------------------------------------
prompt_full, notes_full = gen.build_user_prompt(normalized, None)
check("no budget leaves content untouched", notes_full == [], notes_full)
check("untrimmed prompt is larger", len(prompt_full) > len(prompt))

# --- a small ticket is never trimmed -------------------------------------
tiny = {"issue": {"issue_key": "QA-1", "summary": "s", "description": "short",
                  "acceptance_criteria": ["a"], "comments": [], "linked_issues": [],
                  "attachments": [], "subtasks": []}, "quality": {}}
_, tiny_notes = gen.build_user_prompt(tiny, 19520)
check("small ticket untouched", tiny_notes == [], tiny_notes)

print("\n" + ("ALL PASS" if not fails else f"{len(fails)} FAILURE(S)"))
for f in fails:
    print(" - " + str(f))
sys.exit(1 if fails else 0)
