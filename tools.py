"""
The two tools the agent can call.

  run_sql                 -> structured queries over the `calls` table (counts,
                             filters, aggregates, joins).
  run_ml_generate_text    -> sentiment / intent / topic / summary extraction over
                             transcript_text via BQML ML.GENERATE_TEXT.

Design rule (honest failure): if a tool gets no data back, it SAYS SO. It never
returns a fabricated value. This is the whole point of moving off Agent Builder.
"""

import json
from langchain_core.tools import tool

from . import bq
from .schema import DATASET

# BQML model for ML.GENERATE_TEXT. Currently lives in legal-ai-387622; copy to
# legaldirect is in progress. Update when the copy lands.
ML_MODEL = "`legal-ai-387622.legal_analytics.gemini_flash`"


@tool
def run_sql(sql: str) -> str:
    """Run a BigQuery SQL query over the legaldirect.legal_analytics dataset and
    return the rows as JSON.

    Use this for structured questions: counts, filters, aggregates, group-bys,
    and joins over the `calls` table (and joins to `transcripts` on call_id).
    Always use fully-qualified table names like
    `legaldirect.legal_analytics.calls`.

    If the query returns no rows, this reports that explicitly. Do not invent
    results.
    """
    try:
        rows = bq.run_query(sql)
    except Exception as e:
        return f"TOOL_ERROR: query failed: {e}"
    if not rows:
        return "NO_DATA: the query returned zero rows."
    return json.dumps(rows, default=str)


@tool
def run_ml_generate_text(prompt_instruction: str, where_clause: str = "") -> str:
    """Run sentiment / intent / topic / summary extraction over call transcripts
    using BQML ML.GENERATE_TEXT.

    prompt_instruction: what to extract, e.g.
        "Classify the caller's sentiment as positive, neutral, or negative."
        "In one short phrase, what did the caller want?"
    where_clause: optional SQL WHERE filter on the transcripts table, WITHOUT
        the word WHERE, e.g. "primary_language = 'en'". Leave empty for all.

    Returns one result per transcript as JSON. Reports NO_DATA if nothing
    matched. Does not fabricate.
    """
    where = f"WHERE {where_clause}" if where_clause.strip() else ""
    # Learnings baked in:
    #   - flatten_json_output=TRUE  -> clean string output
    #   - temperature 0.2           -> stable classification
    #   - NO ORDER BY RAND()        -> catastrophic overhead on GENERATE_TEXT
    sql = f"""
    SELECT
      call_id,
      ml_generate_text_llm_result AS result
    FROM ML.GENERATE_TEXT(
      MODEL {ML_MODEL},
      (
        SELECT
          call_id,
          CONCAT(@instruction, '\\n\\nTRANSCRIPT:\\n', transcript_text) AS prompt
        FROM `{DATASET}.transcripts`
        {where}
      ),
      STRUCT(
        0.2 AS temperature,
        TRUE AS flatten_json_output,
        1024 AS max_output_tokens
      )
    )
    """
    # NOTE: parameterizing @instruction requires a parameterized job; for the
    # mock path we just inline-substitute. The live path (bq.run_query) will be
    # upgraded to pass query params once we wire real execution.
    sql = sql.replace("@instruction", json.dumps(prompt_instruction))
    try:
        rows = bq.run_query(sql)
    except Exception as e:
        return f"TOOL_ERROR: ML.GENERATE_TEXT failed: {e}"
    if not rows:
        return "NO_DATA: no transcripts matched."
    return json.dumps(rows, default=str)


ALL_TOOLS = [run_sql, run_ml_generate_text]
