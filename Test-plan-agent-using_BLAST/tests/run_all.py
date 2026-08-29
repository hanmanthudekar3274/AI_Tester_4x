"""Run every test suite. No network, no API keys needed.

    python tests/run_all.py
"""
import subprocess
import sys
from pathlib import Path

SUITES = ["test_normalize", "test_validate", "test_generate", "test_budget", "test_e2e", "test_ui"]
here = Path(__file__).parent

failed = []
for suite in SUITES:
    print(f"\n=== {suite} ===")
    result = subprocess.run([sys.executable, str(here / f"{suite}.py")],
                            capture_output=True, text=True)
    tail = [ln for ln in result.stdout.splitlines() if ln.startswith(("FAIL", "ALL", " -"))]
    print("\n".join(tail) or result.stdout[-500:])
    if result.returncode != 0:
        failed.append(suite)

print("\n" + "=" * 40)
print("ALL SUITES PASS" if not failed else f"FAILED: {', '.join(failed)}")
sys.exit(1 if failed else 0)
