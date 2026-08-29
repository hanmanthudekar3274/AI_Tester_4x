import sys
sys.path.insert(0, r"c:\AI_Tester_4x\Test-plan-agent-using_BLAST")
from tools.validate_plan import validate

fails = []
def check(label, cond, detail=""):
    if not cond:
        fails.append(f"{label} {detail}")
    print(("PASS " if cond else "FAIL ") + label + ("" if cond else f"  <- {detail}"))

def norm(criteria):
    return {"issue": {"issue_key": "QA-1", "acceptance_criteria": criteria}}

def case(n, traces, prio="P0"):
    return {"tc_id": f"TC-QA-1-{n:03d}", "title": "t", "type": "Functional",
            "priority": prio, "traces_to": traces, "preconditions": "p",
            "steps": [{"step_no": 1, "action": "do", "test_data": "-"}],
            "expected_result": "A specific observable outcome occurs."}

def plan(cases, matrix, gaps=None):
    return {"plan_id": "TP-QA-1", "source_issue": "QA-1", "title": "T", "overview": "o",
            "scope": {"in_scope": [], "out_of_scope": []}, "assumptions": [],
            "test_strategy": "s", "test_environments": [], "test_data_requirements": [],
            "entry_criteria": [], "exit_criteria": [], "test_cases": cases, "risks": [],
            "traceability_matrix": matrix, "coverage_gaps": gaps or []}

# happy path
r = validate(plan([case(1,"AC-1"), case(2,"AC-2")],
                  [{"ac_id":"AC-1","acceptance_criterion":"a","test_case_ids":["TC-QA-1-001"]},
                   {"ac_id":"AC-2","acceptance_criterion":"b","test_case_ids":["TC-QA-1-002"]}]),
             norm(["a","b"]))
check("valid plan passes", r["valid"], r["errors"])
check("coverage 100%", r["stats"]["coverage_pct"] == 100.0, r["stats"])

# THE critical rule: uncovered AC must be an error
r = validate(plan([case(1,"AC-1")],
                  [{"ac_id":"AC-1","acceptance_criterion":"a","test_case_ids":["TC-QA-1-001"]}]),
             norm(["a","b is a much longer second criterion"]))
check("uncovered AC is an error", not r["valid"])
check("names the uncovered AC", any("AC-2" in e for e in r["errors"]), r["errors"])
check("coverage 50%", r["stats"]["coverage_pct"] == 50.0, r["stats"])

# dangling reference
r = validate(plan([case(1,"AC-1")],
                  [{"ac_id":"AC-1","acceptance_criterion":"a","test_case_ids":["TC-QA-1-099"]}]),
             norm(["a"]))
check("dangling tc_id ref is error", not r["valid"])
check("dangling names the id", any("TC-QA-1-099" in e for e in r["errors"]), r["errors"])

# duplicate ids
c1, c2 = case(1,"AC-1"), case(1,"AC-1")
r = validate(plan([c1,c2], [{"ac_id":"AC-1","acceptance_criterion":"a","test_case_ids":["TC-QA-1-001"]}]),
             norm(["a"]))
check("duplicate tc_id is error", any("Duplicate" in e for e in r["errors"]), r["errors"])

# bad id format
bad = case(1,"AC-1"); bad["tc_id"] = "TC-001"
r = validate(plan([bad], [{"ac_id":"AC-1","acceptance_criterion":"a","test_case_ids":["TC-001"]}]),
             norm(["a"]))
check("bad id format is error", any("format" in e for e in r["errors"]), r["errors"])

# empty traces_to
bad = case(1,"");
r = validate(plan([bad], [{"ac_id":"AC-1","acceptance_criterion":"a","test_case_ids":["TC-QA-1-001"]}]),
             norm(["a"]))
check("empty traces_to is error", any("traces_to" in e for e in r["errors"]), r["errors"])

# missing top-level key
p = plan([case(1,"AC-1")], [{"ac_id":"AC-1","acceptance_criterion":"a","test_case_ids":["TC-QA-1-001"]}])
del p["risks"]
r = validate(p, norm(["a"]))
check("missing top-level key is error", any("risks" in e for e in r["errors"]), r["errors"])

# empty plan + gaps = valid with warning
r = validate(plan([], [], gaps=["Issue has no description"]), norm([]))
check("empty plan with gaps is valid", r["valid"], r["errors"])
check("empty plan with gaps warns", len(r["warnings"]) > 0)

# empty plan + no gaps = error
r = validate(plan([], [], gaps=[]), norm([]))
check("empty plan without gaps is error", not r["valid"])

# no criteria -> coverage rules skipped
r = validate(plan([case(1,"description")], []), norm([]))
check("no ACs, coverage skipped", r["valid"], r["errors"])

# wrong source issue
p = plan([case(1,"AC-1")], [{"ac_id":"AC-1","acceptance_criterion":"a","test_case_ids":["TC-QA-1-001"]}])
p["source_issue"] = "QA-999"
r = validate(p, norm(["a"]))
check("source_issue mismatch is error", any("QA-999" in e for e in r["errors"]), r["errors"])

# vague expected_result -> warning not error
c = case(1,"AC-1"); c["expected_result"] = "it works"
r = validate(plan([c], [{"ac_id":"AC-1","acceptance_criterion":"a","test_case_ids":["TC-QA-1-001"]}]),
             norm(["a"]))
check("vague expected is warning only", r["valid"] and any("vague" in w for w in r["warnings"]),
      (r["errors"], r["warnings"]))

# never raises on garbage
for junk in [None, [], "string", 42, {"test_cases": "notalist"}]:
    try:
        r = validate(junk, norm(["a"]))
        assert isinstance(r, dict) and not r["valid"]
    except Exception as e:
        fails.append(f"raised on {junk!r}: {e}")
print("PASS never raises on garbage input" if not any("raised" in f for f in fails) else "FAIL raises")

# inferred counter
c = case(1,"AC-1"); c["inferred"] = True
r = validate(plan([c], [{"ac_id":"AC-1","acceptance_criterion":"a","test_case_ids":["TC-QA-1-001"]}]),
             norm(["a"]))
check("counts inferred cases", r["stats"]["inferred_count"] == 1, r["stats"])

print("\n" + ("ALL PASS" if not fails else f"{len(fails)} FAILURE(S)"))
for f in fails: print(" - " + str(f))
sys.exit(1 if fails else 0)
