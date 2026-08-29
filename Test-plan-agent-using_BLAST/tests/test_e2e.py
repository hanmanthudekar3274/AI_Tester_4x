import sys, json, re
sys.path.insert(0, r"c:\AI_Tester_4x\Test-plan-agent-using_BLAST")
from tools import format_markdown, format_docx, validate_plan, normalize_issue

fails=[]
def check(l,c,d=""):
    if not c: fails.append(f"{l} {d}")
    print(("PASS " if c else "FAIL ")+l+("" if c else f"  <- {d}"))

PLAN={"plan_id":"TP-QA-1","source_issue":"QA-1","title":"Test Plan: Password reset",
 "generated_at":"2026-08-29T12:00:00Z","author":"Hanmant","url":"https://x/browse/QA-1",
 "overview":"Testing reset flow.","scope":{"in_scope":["reset"],"out_of_scope":["oauth"]},
 "assumptions":["[INFERRED] email service already tested"],"test_strategy":"Risk-based.",
 "test_environments":[{"name":"Staging","notes":"seeded accounts"}],
 "test_data_requirements":["verified email account"],
 "entry_criteria":["build deployed"],"exit_criteria":["P0 pass"],
 "test_cases":[
   {"tc_id":"TC-QA-1-001","title":"Email delivered","type":"Functional","priority":"P0",
    "traces_to":"AC-1","preconditions":"account exists",
    "steps":[{"step_no":1,"action":"Click Forgot | Password","test_data":"qa@x.com"},
             {"step_no":2,"action":"Submit\nthe form","test_data":"-"}],
    "expected_result":"Email arrives within 30 seconds.","inferred":False},
   {"tc_id":"TC-QA-1-002","title":"Link expires","type":"Boundary","priority":"P1",
    "traces_to":"AC-2","preconditions":"token issued","steps":[],
    "expected_result":"Expired link is rejected.","inferred":True}],
 "risks":[{"risk":"rate limit","severity":"Medium","mitigation":"throttle","source":"QA-99"}],
 "traceability_matrix":[
   {"ac_id":"AC-1","acceptance_criterion":"email in 30s","test_case_ids":["TC-QA-1-001"]},
   {"ac_id":"AC-2","acceptance_criterion":"expiry 24h","test_case_ids":["TC-QA-1-002"]}],
 "coverage_gaps":["Unregistered email behavior unspecified"]}

NORM={"issue":{"issue_key":"QA-1","acceptance_criteria":["email in 30s","expiry 24h"]}}
v=validate_plan.validate(PLAN,NORM)
check("sample plan validates", v["valid"], v["errors"])

md=format_markdown.render(PLAN,v,model="openai/gpt-oss-120b")

# pipe escaping - the silent table-breaker
check("pipe in action escaped", r"Click Forgot \| Password" in md)
check("newline in cell -> <br>", "Submit<br>the form" in md)

# gaps must appear BEFORE test cases
check("gaps before test cases", md.index("Coverage Gaps") < md.index("## Test Cases"),
      (md.index("Coverage Gaps"), md.index("## Test Cases")))
check("coverage summary before gaps", md.index("Coverage Summary") < md.index("Coverage Gaps"))
check("inferred marked", "[INFERRED] Link expires" in md)
check("empty steps handled", "_No steps provided._" in md)
check("matrix rendered", "Traceability Matrix" in md and "TC-QA-1-002" in md)
check("model in metadata", "openai/gpt-oss-120b" in md)
check("empty section omitted", "## Risks" in md)

# table integrity: every table row has consistent pipe count
for block in re.findall(r"(?:^\|.*\n)+", md, re.M):
    rows=[r for r in block.strip().split("\n")]
    counts={r.count("|")-r.count(r"\|") for r in rows}
    if len(counts)>1:
        fails.append(f"ragged table: {rows[0][:60]} counts={counts}")
print("PASS all markdown tables well-formed" if not any("ragged" in str(f) for f in fails) else "FAIL ragged table")

# docx
b=format_docx.render(PLAN,v,model="openai/gpt-oss-120b")
check("docx produced", isinstance(b,bytes) and len(b)>5000, len(b) if isinstance(b,bytes) else type(b))
check("docx is a zip/OOXML", b[:2]==b"PK")

# formatters never raise on degenerate plans
for junk in [{}, {"test_cases":None}, {"test_cases":[{"tc_id":None}]}, {"scope":"notadict"}]:
    try:
        format_markdown.render(junk,{})
        format_docx.render(junk,{})
    except Exception as e:
        fails.append(f"formatter raised on {junk}: {e!r}")
print("PASS formatters never raise on degenerate input" if not any("raised" in str(f) for f in fails) else "FAIL formatter raised")

print("\n"+("ALL PASS" if not fails else f"{len(fails)} FAILURE(S)"))
for f in fails: print(" - "+str(f))
sys.exit(1 if fails else 0)
