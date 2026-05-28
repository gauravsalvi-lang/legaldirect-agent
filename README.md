# Legal Direct conversational data agent

LangGraph agent that lets users chat with call/transcript data in
`legaldirect.legal_analytics` (BigQuery), in natural language.

## Why this exists
Vertex AI Agent Builder's preview runtime hallucinated tool results (returned
1,523 / 148k / 221k for a query whose real answer is 25). The bug was in its
tool-result -> model relay, not the MCP server or data (Cowork returned correct
data against the same MCP). This is a custom Python agent that calls BigQuery
directly and never fabricates.

## Layout
    agent/schema.py   hardcoded dataset schema (calls, transcripts)
    agent/bq.py       BigQuery access layer  <-- ONLY part gated by IAM
    agent/tools.py    run_sql + run_ml_generate_text, with honest-failure logic
    agent/graph.py    the LangGraph agent + anti-fabrication system prompt
    test_tools.py     offline test (no API key, no IAM) proving the wiring

## Run the offline test (works today, no credentials)
    # PowerShell
    $env:LEGALDIRECT_MOCK=1; python test_tools.py

## Run for real (once IAM + API key are ready)
1. IAM on legaldirect for your account:
     roles/serviceusage.serviceUsageConsumer
     roles/bigquery.jobUser
     roles/bigquery.dataViewer
2. Gemini API key from AI Studio:
     $env:GOOGLE_API_KEY="..."   (or use Vertex via gcloud auth)
3. Unset mock and run the chat (Streamlit UI added next step).
