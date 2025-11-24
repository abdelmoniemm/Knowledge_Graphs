import os, re, requests
import google.generativeai as genai
from flask import Blueprint, request, jsonify

# ===== GraphDB/Fuseki config =====
GRAPHDB_BASE = os.environ.get("GRAPHDB_BASE", "http://localhost:3030").rstrip("/")
REPO_ID      = os.environ.get("GRAPHDB_REPO", "bachelor2025")
# Fuseki Query Endpoint
REPO_URL     = f"{GRAPHDB_BASE}/{REPO_ID}/sparql"

# ===== Gemini Config =====
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ ERROR: GEMINI_API_KEY is not found in .env!")
else:
    print("✅ Gemini API Key found.")
GEMINI_MODEL   = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# Configure the native SDK with your key
genai.configure(api_key=api_key, transport="rest")

nl2sparql_bp = Blueprint("nl2sparql_gemini", __name__)

SYSTEM_PROMPT = """You translate natural-language questions about data-quality scores
into SPARQL 1.1 SELECT queries.
PREFIX ex: <http://example.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

Schema:
- Classes: ex:DQRule, ex:Database, ex:Schema, ex:Table
- Properties: ex:ruleCode, ex:score (decimal), ex:techSystem (database), ex:techGroup (schema), ex:dataset (table), ex:dataElement.

INSTRUCTIONS:
1. Return ONLY the SPARQL query inside a markdown code block ```sparql ... ```.
2. Do not explain the query.
3. Cast scores using xsd:double for comparisons (e.g., FILTER(xsd:double(?score) < 70)).
"""

def extract_sparql(text: str) -> str:
    """Pull the query out of a fenced code block; fallback to raw text."""
    if not text: return ""
    # Regex to find ```sparql ... ``` or just ``` ... ```
    m = re.search(r"```(?:sparql)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if m: return m.group(1).strip()
    return text.strip()

def run_sparql(query: str):
    """Execute SPARQL on Fuseki"""
    # Note: We removed auth=() because we set shiro.ini to 'anon' (anonymous access)
    try:
        r = requests.post(
            REPO_URL,
            data={"query": query},
            headers={"Accept": "application/sparql-results+json"},
            timeout=60,
        )
        r.raise_for_status()
        bindings = r.json().get("results", {}).get("bindings", [])
        return [{k: v.get("value") for k, v in b.items()} for b in bindings]
    except Exception as e:
        print(f"Fuseki Query Error: {e}")
        # Return empty list or re-raise depending on preference
        raise

def ask_gemini_for_sparql(question: str) -> str:
    """Call Gemini using the native SDK"""
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Combine system prompt and user question
        full_prompt = f"{SYSTEM_PROMPT}\n\nQuestion: {question}"
        
        response = model.generate_content(full_prompt)
        
        # Access the text result
        return extract_sparql(response.text)
    except Exception as e:
        print(f"Gemini API Error: {e}")
        raise

# ===== Routes =====

@nl2sparql_bp.post("/translate")
def translate_only():
    data = request.get_json(silent=True) or {}
    q = (data.get("question") or "").strip()
    if not q:
        return jsonify(error="Provide JSON with 'question'."), 400
    try:
        sparql = ask_gemini_for_sparql(q)
        return jsonify(query=sparql)
    except Exception as e:
        return jsonify(error=str(e)), 500

@nl2sparql_bp.post("/translate-run")
def translate_and_run():
    data = request.get_json(silent=True) or {}
    q = (data.get("question") or "").strip()
    if not q:
        return jsonify(error="Provide JSON with 'question'."), 400
    try:
        sparql = ask_gemini_for_sparql(q)
        rows = run_sparql(sparql)
        return jsonify(query=sparql, rows=rows)
    except Exception as e:
        return jsonify(error=str(e)), 500