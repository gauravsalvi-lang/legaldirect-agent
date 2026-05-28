"""
Offline test: proves the tool + mock layer works end to end with NO model API
key and NO BigQuery IAM. This is the layer Agent Builder broke (tool result ->
consumer relay). If real tool data flows through cleanly here, the architecture
is sound.

Run:  LEGALDIRECT_MOCK=1 python test_tools.py   (mac/linux)
      $env:LEGALDIRECT_MOCK=1; python test_tools.py   (windows powershell)
"""

import os
os.environ["LEGALDIRECT_MOCK"] = "1"  # force mock for this test

from agent.tools import run_sql, run_ml_generate_text


def check(label, got, expect_substr):
    ok = expect_substr in got
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    print(f"        tool returned: {got}")
    assert ok, f"expected '{expect_substr}' in result"


# 1. A count query -> mock returns the REAL answer (25), proving the value the
#    model sees is the value the tool produced. No hallucination possible.
check("count query returns 25",
      run_sql.invoke({"sql": "SELECT COUNT(*) AS n FROM `legaldirect.legal_analytics.calls`"}),
      '"n": 25')

# 2. A group-by -> mock returns disposition breakdown.
check("group-by returns categories",
      run_sql.invoke({"sql": "SELECT disposition_category, COUNT(*) c FROM x GROUP BY 1"}),
      "converted")

# 3. A query the mock doesn't recognize -> NO_DATA, NOT a fabricated number.
check("unknown query yields honest NO_DATA",
      run_sql.invoke({"sql": "SELECT something_weird FROM nowhere"}),
      "NO_DATA")

# 4. ML.GENERATE_TEXT with no matching transcripts -> honest NO_DATA.
check("ml_generate_text honest failure",
      run_ml_generate_text.invoke({"prompt_instruction": "classify sentiment", "where_clause": "1=0"}),
      "NO_DATA")

print("\nAll tool-layer tests passed. The honest-failure path works.")
