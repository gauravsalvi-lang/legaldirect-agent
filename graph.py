"""
LangGraph agent: chat with the Legal Direct call/transcript data.

Loop: user question -> model decides (answer directly | call run_sql |
call run_ml_generate_text) -> tool result returns -> model writes final answer
grounded ONLY in tool output.

The anti-fabrication guardrail lives in SYSTEM_PROMPT. This is the core fix for
the Agent Builder hallucination problem: the model is told, in strong terms, to
echo tool data and to say so when a tool returns NO_DATA / TOOL_ERROR rather
than inventing numbers, column names, or call IDs.
"""

import os
from langgraph.prebuilt import create_react_agent

from .tools import ALL_TOOLS
from .schema import SCHEMA_DESCRIPTION

SYSTEM_PROMPT = f"""You are a data analyst assistant for the Legal Direct team.
You answer questions about phone calls and their transcripts stored in BigQuery.

You have two tools:
  - run_sql: for counts, filters, aggregates, group-bys, joins over the `calls`
    table. Always fully-qualify table names, e.g.
    `legaldirect.legal_analytics.calls`.
  - run_ml_generate_text: for sentiment, intent, topic, or summary extraction
    from transcript text.

DATASET SCHEMA:
{SCHEMA_DESCRIPTION}

ABSOLUTE RULES — these override everything else:
1. NEVER invent data. Every number, name, call_id, or category in your answer
   MUST come from a tool result you actually received in this conversation.
2. If a tool returns "NO_DATA", tell the user there were no matching rows. Do
   NOT substitute a guess.
3. If a tool returns "TOOL_ERROR", tell the user the query failed and show the
   error. Do NOT pretend it succeeded.
4. If you did not call a tool, do not state any specific figure as fact.
5. When you report numbers, they must exactly match the tool's JSON. Do not
   round, embellish, or fill gaps.
6. Be honest about data-quality caveats when relevant (Whisper hallucinations in
   long transcripts, all speakers labelled [Speaker_Unknown], phone-join noise).

Pick the right tool for the question. For "how many", "average", "which firm",
"group by" -> run_sql. For "sentiment", "what did the caller want", "summarize",
"intent", "topic" -> run_ml_generate_text. Write the SQL yourself.
"""


def build_agent():
    """Construct the LangGraph ReAct agent.

    Model selection:
      - If GOOGLE_API_KEY is set -> use AI Studio (langchain_google_genai),
        the unblocked local-dev path.
      - Else -> use Vertex AI (langchain_google_vertexai), which uses gcloud
        auth but needs serviceusage perms on the project.
    """
    if os.environ.get("GOOGLE_API_KEY"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    else:
        from langchain_google_vertexai import ChatVertexAI
        model = ChatVertexAI(
            model="gemini-2.0-flash", temperature=0, project="legaldirect"
        )

    return create_react_agent(model, ALL_TOOLS, prompt=SYSTEM_PROMPT)
