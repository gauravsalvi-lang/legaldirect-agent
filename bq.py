"""
BigQuery access layer.

This is the ONLY module gated by IAM permissions. Everything else (routing,
tools, graph) is testable today via mock mode.

Mock mode: set env LEGALDIRECT_MOCK=1 to return canned results without touching
BigQuery. Turn it off once the serviceusage.serviceUsageConsumer +
bigquery.jobUser/dataViewer roles land on the legaldirect project.
"""

import os

_MOCK = os.environ.get("LEGALDIRECT_MOCK") == "1"

# Lazily created so importing this module never requires credentials in mock mode.
_client = None


def _get_client():
    global _client
    if _client is None:
        from google.cloud import bigquery
        _client = bigquery.Client(project="legaldirect")
    return _client


# --- Mock fixtures -------------------------------------------------
# Canned responses keyed by a substring of the SQL. Lets us exercise the
# agent's routing + honest-failure logic without real data.
_MOCK_ROWS = {
    "count(*)": [{"n": 25}],
    "disposition_category": [
        {"disposition_category": "converted", "c": 8},
        {"disposition_category": "followup", "c": 11},
        {"disposition_category": "no_action", "c": 6},
    ],
}


def run_query(sql: str) -> list[dict]:
    """Execute SQL against BigQuery and return rows as a list of dicts.

    Returns an empty list if the query returns no rows. Raises on real errors
    (auth, syntax) so the agent can report an honest failure rather than guess.
    """
    if _MOCK:
        low = sql.lower()
        # Most-specific key first so a group-by on disposition_category isn't
        # swallowed by the generic count(*) fixture.
        if "group by" in low and "disposition_category" in low:
            return _MOCK_ROWS["disposition_category"]
        if "count(*)" in low:
            return _MOCK_ROWS["count(*)"]
        return []  # default: no data -> forces honest-failure path

    client = _get_client()
    job = client.query(sql)
    return [dict(row) for row in job.result()]
