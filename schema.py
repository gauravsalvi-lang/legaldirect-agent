"""
Schema knowledge for the legaldirect.legal_analytics dataset.

Hardcoded intentionally: the agent needs to know table/column shape to write
correct SQL WITHOUT making a BigQuery call first. Keep this in sync with the
real schema (or regenerate from INFORMATION_SCHEMA once IAM access lands).
"""

DATASET = "legaldirect.legal_analytics"

SCHEMA_DESCRIPTION = """
TABLE: calls  (one row per phone call; partitioned)
  call_id              STRING    REQUIRED  Unique call identifier from Five9
  call_start_time      TIMESTAMP REQUIRED  When the call started
  call_direction       STRING              'inbound' or 'outbound'
  call_platform        STRING              Source telephony platform (e.g. 'five9')
  received_by_firm     STRING              Law firm whose number was dialed
  assigned_to_firm     STRING              Law firm that ultimately works the case
  firm_practice_area   STRING              e.g. Personal Injury, Workers Comp
  caller_phone_hash    STRING              SHA-256 hash of caller phone number
  talk_duration_seconds INTEGER            Length of the call in seconds
  disposition_native   STRING              Raw Five9 disposition label
  disposition_category STRING              Normalized outcome: converted, followup, ...
  case_type            STRING              Case category: Auto Accident, Workers Comp, ...
  case_close_reason    STRING              Reason a case closed without conversion
  retainer_signed_date DATE                Date client signed retainer, if converted
  audio_file_uri       STRING              GCS path to original audio
  agent_id             STRING              Five9 agent identifier
  campaign_id          STRING              Five9 campaign identifier (outbound only)
  ingestion_timestamp  TIMESTAMP           When row was loaded into BigQuery

TABLE: transcripts  (one row per call's transcript)
  call_id                STRING   REQUIRED  Foreign key to calls.call_id
  transcript_text        STRING             Full call transcript, PII redacted. May be very long.
  primary_language       STRING             Dominant language: en, es, ...
  language_segments      RECORD  REPEATED   Per-segment language detection
  transcription_service  STRING             Which provider produced the text
  transcription_confidence FLOAT            Service-reported confidence 0.0-1.0
  redaction_method       STRING             regex, NER, third-party DLP
  redacted_pii_types     STRING  REPEATED   Types of PII scrubbed
  created_at             TIMESTAMP          When transcript was produced

VIEW: calls_with_transcripts  (calls JOINed to transcripts on call_id)

KNOWN DATA QUALITY ISSUES (be honest about these in answers):
  - Some transcripts are Whisper hallucinations and can exceed 170k chars.
  - Diarization labels every speaker [Speaker_Unknown]; you CANNOT reliably
    distinguish agent vs caller turns.
  - Joining cases by phone number can produce multi-case noise.
"""

# Quick lookups used by the router / validation.
CALLS_COLUMNS = {
    "call_id", "call_start_time", "call_direction", "call_platform",
    "received_by_firm", "assigned_to_firm", "firm_practice_area",
    "caller_phone_hash", "talk_duration_seconds", "disposition_native",
    "disposition_category", "case_type", "case_close_reason",
    "retainer_signed_date", "audio_file_uri", "agent_id", "campaign_id",
    "ingestion_timestamp",
}

TRANSCRIPTS_COLUMNS = {
    "call_id", "transcript_text", "primary_language", "language_segments",
    "transcription_service", "transcription_confidence", "redaction_method",
    "redacted_pii_types", "created_at",
}
