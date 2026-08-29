import sys, json
sys.path.insert(0, r"c:\AI_Tester_4x\Test-plan-agent-using_BLAST")
from tools import generate_test_plan as gen
from tools.llm_client import BaseLLM

fails=[]
def check(l,c,d=""):
    if not c: fails.append(f"{l} {d}")
    print(("PASS " if c else "FAIL ")+l+("" if c else f"  <- {d}"))

sp = gen.load_system_prompt()
check("system prompt loads from SOP", "GROUNDING RULES" in sp and len(sp)>1000, len(sp))
check("prompt not in python source", "GROUNDING RULES" not in open(gen.__file__,encoding='utf-8').read())
check("retry prompt loads", "{errors}" in gen.load_retry_prompt())

NORM={"issue":{"issue_key":"QA-1","summary":"s","acceptance_criteria":["a","b"]},
      "quality":{"has_description":True}}

def good_plan(cover_both=True):
    m=[{"ac_id":"AC-1","acceptance_criterion":"a","test_case_ids":["TC-QA-1-001"]}]
    if cover_both: m.append({"ac_id":"AC-2","acceptance_criterion":"b","test_case_ids":["TC-QA-1-002"]})
    cs=[{"tc_id":f"TC-QA-1-{n:03d}","title":"t","type":"Functional","priority":"P0",
         "traces_to":f"AC-{n}","preconditions":"p",
         "steps":[{"step_no":1,"action":"do it","test_data":"-"}],
         "expected_result":"A specific observable outcome occurs."}
        for n in (1,2)[:2 if cover_both else 1]]
    return {"plan_id":"TP-QA-1","source_issue":"QA-1","title":"T","overview":"o",
            "scope":{"in_scope":[],"out_of_scope":[]},"assumptions":[],"test_strategy":"s",
            "test_environments":[],"test_data_requirements":[],"entry_criteria":[],
            "exit_criteria":[],"test_cases":cs,"risks":[],"traceability_matrix":m,
            "coverage_gaps":[]}

class Fake(BaseLLM):
    def __init__(self, replies): self.replies=list(replies); self.calls=[]; self.last_usage={"total_tokens":10}
    @property
    def name(self): return "fake"
    def is_available(self): return True,"ok"
    def complete(self, system_prompt, user_prompt, max_tokens=8192, json_mode=True, extra_messages=None):
        self.calls.append({"extra":extra_messages})
        return self.replies.pop(0)

# 1. valid first time -> 1 call
f=Fake([json.dumps(good_plan())])
r=gen.generate(NORM, {"DISPLAY_NAME":"Hanmant"}, llm=f)
check("valid on attempt 1", r["attempts"]==1 and r["validation"]["valid"])
check("only one LLM call", len(f.calls)==1, len(f.calls))
check("author stamped", r["plan"].get("author")=="Hanmant")
check("generated_at added", "generated_at" in r["plan"])

# 2. invalid then valid -> retry works, 2 calls
f=Fake([json.dumps(good_plan(cover_both=False)), json.dumps(good_plan())])
r=gen.generate(NORM, {}, llm=f)
check("recovers on retry", r["attempts"]==2 and r["validation"]["valid"])
check("retry fed errors back", f.calls[1]["extra"] is not None and
      any("AC-2" in m["content"] for m in f.calls[1]["extra"]), f.calls[1])

# 3. invalid twice -> raises, exactly 2 calls (no infinite loop)
f=Fake([json.dumps(good_plan(False)), json.dumps(good_plan(False))])
try:
    gen.generate(NORM, {}, llm=f); check("raises after 2 failures", False)
except gen.GenerationError as e:
    check("raises after 2 failures", True)
    check("stops at exactly 2 calls", len(f.calls)==2, len(f.calls))
    check("error names uncovered AC", "AC-2" in str(e), str(e)[:120])

# 4. prose response -> parse error triggers retry
f=Fake(["Sure! Here is your plan.", json.dumps(good_plan())])
r=gen.generate(NORM, {}, llm=f)
check("prose reply recovers via retry", r["validation"]["valid"] and r["attempts"]==2)

# 5. fenced json tolerated
f=Fake(["```json\n"+json.dumps(good_plan())+"\n```"])
r=gen.generate(NORM, {}, llm=f)
check("fenced json tolerated", r["attempts"]==1)

# 6. usage recorded
check("usage log recorded", r["usage"] and r["usage"][0]["total_tokens"]==10, r["usage"])

print("\n"+("ALL PASS" if not fails else f"{len(fails)} FAILURE(S)"))
for x in fails: print(" - "+str(x))
sys.exit(1 if fails else 0)
