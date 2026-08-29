import sys, json
sys.path.insert(0, r"c:\AI_Tester_4x\Test-plan-agent-using_BLAST")
from tools.normalize_issue import normalize, adf_to_text, _doc_to_text, split_criteria

def adf(*blocks):
    return {"type": "doc", "version": 1, "content": list(blocks)}

def para(*texts):
    return {"type": "paragraph", "content": [{"type": "text", "text": t} for t in texts]}

def bullets(*items):
    return {"type": "bulletList", "content": [
        {"type": "listItem", "content": [para(i)]} for i in items]}

fails = []
def check(label, got, want):
    if got != want:
        fails.append(f"{label}\n   got:  {got!r}\n   want: {want!r}")
    print(("PASS " if got == want else "FAIL ") + label)

# --- ADF flattening ---
check("plain string passthrough", _doc_to_text("hello"), "hello")
check("None -> empty", _doc_to_text(None), "")
check("paragraph", _doc_to_text(adf(para("Login must work."))), "Login must work.")
check("bullets",
      _doc_to_text(adf(bullets("first", "second"))),
      "- first\n- second")
check("unknown node type recurses",
      _doc_to_text(adf({"type": "weirdPanel", "content": [para("inner text")]})),
      "inner text")
check("inlineCard emits url",
      adf_to_text({"type": "inlineCard", "attrs": {"url": "https://x.test"}}),
      "https://x.test")
check("media emits attachment marker",
      adf_to_text({"type": "media", "attrs": {"alt": "wireframe.png"}}),
      "[attachment: wireframe.png]")
check("table row pipes",
      adf_to_text({"type": "tableRow", "content": [
          {"type": "tableCell", "content": [para("a")]},
          {"type": "tableCell", "content": [para("b")]}]}),
      "a | b")

# cyclic-ish deep nesting must not blow the stack
deep = {"type": "paragraph", "content": [{"type": "text", "text": "x"}]}
for _ in range(200):
    deep = {"type": "paragraph", "content": [deep]}
try:
    _doc_to_text(adf(deep))
    print("PASS deep nesting capped, no crash")
except RecursionError:
    fails.append("deep nesting caused RecursionError")
    print("FAIL deep nesting caused RecursionError")

# --- criteria splitting ---
check("split bullets", split_criteria("- one\n- two\n- three"), ["one", "two", "three"])
check("split numbered", split_criteria("1. alpha\n2) beta"), ["alpha", "beta"])
check("drop tiny entries", split_criteria("- ok entry\n- x"), ["ok entry"])

# --- criteria source fallbacks ---
def build(desc_adf, ac_field=None, ac_id=None, itype="Story"):
    fields = {"summary": "S", "description": desc_adf, "issuetype": {"name": itype},
              "priority": {"name": "High"}, "status": {"name": "In Progress"},
              "labels": [], "components": [], "subtasks": [], "issuelinks": [],
              "attachment": []}
    if ac_id:
        fields[ac_id] = ac_field
    return {"issue": {"key": "QA-1", "self": "https://acme.atlassian.net/rest/api/3/issue/1",
                      "fields": fields},
            "comments": [], "field_map": {"acceptance_criteria": ac_id},
            "fetched_at": "2026-08-29T00:00:00Z"}

r = normalize(build(adf(para("desc")), adf(bullets("AC one", "AC two")), "customfield_10016"))
check("source=custom_field", r["quality"]["acceptance_criteria_source"], "custom_field")
check("custom field criteria", r["issue"]["acceptance_criteria"], ["AC one", "AC two"])

r = normalize(build(adf(para("Acceptance Criteria:"), bullets("must log in", "must log out"))))
check("source=description_heading", r["quality"]["acceptance_criteria_source"], "description_heading")
check("heading criteria", r["issue"]["acceptance_criteria"], ["must log in", "must log out"])

r = normalize(build(adf(para("Given a user"), para("When they click"), para("Then it works"),
                        para("Given a second case"), para("Then it also works"))))
check("source=gherkin", r["quality"]["acceptance_criteria_source"], "gherkin")
check("gherkin grouped into 2", len(r["issue"]["acceptance_criteria"]), 2)

r = normalize(build(adf(para("just a description"))))
check("source=none", r["quality"]["acceptance_criteria_source"], "none")
check("no criteria -> empty list", r["issue"]["acceptance_criteria"], [])

# --- empty / hostile payloads ---
r = normalize({})
check("empty payload key", r["issue"]["issue_key"], "UNKNOWN")
check("empty payload description", r["issue"]["description"], "")
check("empty payload has_description", r["quality"]["has_description"], False)

r = normalize(build(None))
check("null description", r["issue"]["description"], "")

# --- schema completeness: every key always present ---
SCHEMA_KEYS = {"issue_key","url","summary","description","issue_type","priority","status",
               "assignee","reporter","parent_key","labels","components","acceptance_criteria",
               "subtasks","linked_issues","comments","attachments","fetched_at"}
missing = SCHEMA_KEYS - set(normalize({})["issue"].keys())
check("all schema keys present on empty input", missing, set())

# --- url construction ---
r = normalize(build(adf(para("d"))))
check("browse url", r["issue"]["url"], "https://acme.atlassian.net/browse/QA-1")

# --- epic flag ---
r = normalize(build(adf(para("d")), itype="Epic"))
check("epic flag", r["quality"]["is_epic"], True)

print("\n" + ("ALL PASS" if not fails else f"{len(fails)} FAILURE(S)"))
for f in fails:
    print(" - " + f)
sys.exit(1 if fails else 0)
