import sys
sys.path.insert(0, r"c:\AI_Tester_4x\Test-plan-agent-using_BLAST")
from streamlit.testing.v1 import AppTest

fails=[]
def run(path,label,secs=30):
    at=AppTest.from_file(path, default_timeout=secs).run()
    if at.exception:
        for e in at.exception: fails.append(f"{label}: {e.value}")
        print(f"FAIL {label} raised: {[e.value for e in at.exception]}")
        return None
    print(f"PASS {label} renders clean")
    return at

R=r"c:\AI_Tester_4x\Test-plan-agent-using_BLAST"

# The real .env may or may not be populated on this machine. Force a known
# unconfigured state so this suite tests behavior, not the developer's setup.
import tools.config_store as _cs
_real_missing = _cs.missing_required
_cs.missing_required = lambda config=None: ["JIRA_BASE_URL", "GROQ_API_KEY"]

# Screen 1
at=run(R+r"\ui\app.py","chat screen")
if at:
    txt=" ".join(m.value for m in at.markdown)+" ".join(str(e.value) for e in at.error)
    print("   - blocks when unconfigured:", "Not configured" in " ".join(str(e.value) for e in at.error) or "Missing" in " ".join(str(e.value) for e in at.error))
    print("   - has chat input:", len(at.chat_input)>0)
    # simulate asking without a key configured
    at.chat_input[0].set_value("Create a test plan for QA-123").run()
    errs=" ".join(str(e.value) for e in at.error)
    ok = "missing" in errs.lower()
    print(("PASS " if ok else "FAIL ")+"  chat blocks generation when unconfigured")
    if not ok: fails.append("chat did not block when unconfigured")

_cs.missing_required = _real_missing

# Screen 2
at2=run(R+r"\ui\pages\settings.py","settings screen")
if at2:
    labels=[t.label for t in at2.text_input]
    need=["Jira Base URL","Jira Email","Jira API Token","Groq API Key","Model ID","Display Name"]
    for n in need:
        ok=any(n in l for l in labels)
        print(("PASS " if ok else "FAIL ")+f"  field present: {n}")
        if not ok: fails.append(f"missing field {n}")
    # password masking on secrets
    for t in at2.text_input:
        if t.label in ("Jira API Token","Groq API Key"):
            ok = t.proto.type == 1  # 1 = password widget in the protobuf
            print(("PASS " if ok else "FAIL ")+f"  {t.label} is masked")
            if not ok: fails.append(f"{t.label} not password type")
    btns=[b.label for b in at2.button]
    n_test=sum(1 for b in btns if "Test Connection" in b)
    print(("PASS " if n_test==2 else "FAIL ")+f"  two Test Connection buttons (found {n_test})")
    if n_test!=2: fails.append(f"test buttons={n_test} {btns}")
    n_save=sum(1 for b in btns if b=="Save")
    print(("PASS " if n_save==3 else "FAIL ")+f"  three Save buttons (found {n_save})")

    # click Test Connection with empty fields -> must not crash, must warn
    for b in at2.button:
        if "Test Connection" in b.label:
            b.click().run()
            break
    if at2.exception:
        fails.append(f"Test Connection crashed: {[e.value for e in at2.exception]}")
        print("FAIL   Test Connection with blanks crashed")
    else:
        print("PASS   Test Connection with blanks handled")

print("\n"+("ALL PASS" if not fails else f"{len(fails)} FAILURE(S)"))
for f in fails: print(" - "+str(f))
sys.exit(1 if fails else 0)
