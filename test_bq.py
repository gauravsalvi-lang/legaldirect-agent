from google.cloud import bigquery

client = bigquery.Client(project="legaldirect")
rows = client.query("SELECT COUNT(*) AS n FROM `legaldirect.legal_analytics.calls`").result()
for r in rows:
    print("calls row count:", r.n)