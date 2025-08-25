# flask-server/nl2sparql_openai.py
import os, re, time, requests
from flask import Blueprint, request, jsonify
from openai import OpenAI

# ===== GraphDB config =====
GRAPHDB_BASE = os.environ.get("GRAPHDB_BASE", "http://localhost:7200").rstrip("/")
REPO_ID = os.environ.get("GRAPHDB_REPO", "bachelor2025")
REPO_URL = f"{GRAPHDB_BASE}/repositories/{REPO_ID}"

# ===== OpenAI config (Responses API) =====
# The client will read OPENAI_API_KEY from the environment automatically.
client = OpenAI()
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")  # match the quickstart example

nl2sparql_bp = Blueprint("nl2sparql_openai", __name__)

SYSTEM_PROMPT = """You translate natural-language questions about data-quality scores
into SPARQL 1.1 SELECT queries for GraphDB.

Use these prefixes exactly:
PREFIX ex: <http://example.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

Data model:
- ex:DQRule is the class for rules.
- Properties: ex:ruleCode, ex:score (xsd:decimal), ex:techSystem (database),
  ex:techGroup (schema), ex:dataset (table), ex:dataElement (field).
- For numeric comparisons/aggregates, cast scores with xsd:decimal.

Return ONLY one SPARQL query inside a single fenced code block:
```sparql
...query...
```"""

def extract_sparql(text: str) -> str:
    """Pull the query out of a fenced code block; fallback to raw text."""
    if not text:
        return ""
    m = re.search(r"```sparql\s+([\s\S]*?)```", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r"```\s*([\s\S]*?)```", text)
    if m:
        return m.group(1).strip()
    return text.strip()

def run_sparql(query: str):
    """Execute SPARQL on GraphDB and return flattened rows."""
    r = requests.post(
        REPO_URL,
        data={"query": query},
        headers={"Accept": "application/sparql-results+json"},
        timeout=60,
    )
    r.raise_for_status()
    bindings = r.json().get("results", {}).get("bindings", [])
    return [{k: v.get("value") for k, v in b.items()} for b in bindings]

def ask_openai_for_sparql(question: str) -> str:
    """Call OpenAI Responses API with a system prompt via 'instructions'."""
    # simple 3-try backoff on rate limits
    for attempt in range(3):
        try:
            resp = client.responses.create(
                model=OPENAI_MODEL,
                instructions=SYSTEM_PROMPT,
                input=question.strip(),     # exactly like the "haiku" example
                
            )
            # Responses API: easiest way to read is output_text
            text = resp.output_text
            return extract_sparql(text)
        except Exception as e:
            # If it looks like a rate-limit, back off briefly and retry
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status == 429 and attempt < 2:
                time.sleep(2 ** attempt)  # 1s, 2s
                continue
            raise

@nl2sparql_bp.post("/translate")
def translate_only():
    data = request.get_json(silent=True) or {}
    q = (data.get("question") or "").strip()
    if not q:
        return jsonify(error="Provide JSON with 'question'."), 400
    try:
        sparql = ask_openai_for_sparql(q)
        return jsonify(query=sparql)
    except requests.HTTPError as e:
        body = _safe_body(e)
        return jsonify(error=f"GraphDB HTTP error {e.response.status_code}", details=body), 502
    except Exception as e:
        return jsonify(error=str(e)), 500

@nl2sparql_bp.post("/translate-run")
def translate_and_run():
    data = request.get_json(silent=True) or {}
    q = (data.get("question") or "").strip()
    if not q:
        return jsonify(error="Provide JSON with 'question'."), 400
    try:
        sparql = ask_openai_for_sparql(q)
        rows = run_sparql(sparql)
        return jsonify(query=sparql, rows=rows)
    except requests.HTTPError as e:
        body = _safe_body(e)
        return jsonify(error=f"HTTP error {e.response.status_code}", details=body), 502
    except Exception as e:
        return jsonify(error=str(e)), 500

def _safe_body(e: requests.HTTPError):
    try:
        return e.response.json()
    except Exception:
        return getattr(e.response, "text", "")
