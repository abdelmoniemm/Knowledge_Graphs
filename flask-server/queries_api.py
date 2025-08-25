import os, re, requests
from flask import Blueprint, request, jsonify

GRAPHDB_BASE = os.environ.get("GRAPHDB_BASE", "http://localhost:7200")
REPO_ID      = os.environ.get("GRAPHDB_REPO", "bachelor2025")
REPO_URL     = f"{GRAPHDB_BASE.rstrip('/')}/repositories/{REPO_ID}"

QUERIES = {
    "Average score per database (asc)": """
        PREFIX ex: <http://example.org/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT ?database (AVG(xsd:decimal(?score)) AS ?avgScore)
        WHERE { ?rule a ex:DQRule ; ex:techSystem ?database ; ex:score ?score . }
        GROUP BY ?database
        ORDER BY ASC(?avgScore)
    """,
    "Average score per schema (asc)": """
        PREFIX ex: <http://example.org/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT ?schema (AVG(xsd:decimal(?score)) AS ?avgScore)
        WHERE { ?rule a ex:DQRule ; ex:techGroup ?schema ; ex:score ?score . }
        GROUP BY ?schema
        ORDER BY ASC(?avgScore)
    """,
    "Databases with lowest avg score (with path)": """
        PREFIX ex: <http://example.org/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT ?database ?path ?avgScore
        WHERE {
          {
            SELECT ?database (AVG(xsd:decimal(?score)) AS ?avgScore)
            WHERE { ?r a ex:DQRule ; ex:techSystem ?database ; ex:score ?score . }
            GROUP BY ?database
          }
          {
            SELECT (MIN(?avg) AS ?minAvg)
            WHERE {
              SELECT (AVG(xsd:decimal(?score)) AS ?avg)
              WHERE { ?r a ex:DQRule ; ex:techSystem ?db ; ex:score ?score . }
              GROUP BY ?db
            }
          }
          FILTER (?avgScore = ?minAvg)
          BIND(STR(?database) AS ?path)
        }
    """,
    "Schemas with lowest avg score (with path)": """
        PREFIX ex: <http://example.org/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT ?database ?schema ?path ?avgScore
        WHERE {
          {
            SELECT ?database ?schema (AVG(xsd:decimal(?score)) AS ?avgScore)
            WHERE { ?r a ex:DQRule ; ex:techSystem ?database ; ex:techGroup ?schema ; ex:score ?score . }
            GROUP BY ?database ?schema
          }
          {
            SELECT (MIN(?avg) AS ?minAvg)
            WHERE {
              SELECT (AVG(xsd:decimal(?score)) AS ?avg)
              WHERE { ?r a ex:DQRule ; ex:techSystem ?db ; ex:techGroup ?sch ; ex:score ?score . }
              GROUP BY ?db ?sch
            }
          }
          FILTER (?avgScore = ?minAvg)
          BIND(CONCAT(STR(?database), ".", STR(?schema)) AS ?path)
        }
    """,
    "Tables with lowest avg score (with path)": """
        PREFIX ex: <http://example.org/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT ?database ?schema ?dataset ?path ?avgScore
        WHERE {
          {
            SELECT ?database ?schema ?dataset (AVG(xsd:decimal(?score)) AS ?avgScore)
            WHERE { ?r a ex:DQRule ; ex:techSystem ?database ; ex:techGroup ?schema ; ex:dataset ?dataset ; ex:score ?score . }
            GROUP BY ?database ?schema ?dataset
          }
          {
            SELECT (MIN(?avg) AS ?minAvg)
            WHERE {
              SELECT (AVG(xsd:decimal(?score)) AS ?avg)
              WHERE { ?r a ex:DQRule ; ex:techSystem ?db ; ex:techGroup ?sch ; ex:dataset ?ds ; ex:score ?score . }
              GROUP BY ?db ?sch ?ds
            }
          }
          FILTER (?avgScore = ?minAvg)
          BIND(CONCAT(STR(?database), ".", STR(?schema), ".", STR(?dataset)) AS ?path)
        }
    """,
    "Rules with lowest score (with code & path)": """
        PREFIX ex: <http://example.org/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT ?rule ?ruleCode ?techSystem ?techGroup ?dataset ?dataElement ?path ?score
        WHERE {
          { SELECT (MIN(xsd:decimal(?s)) AS ?minScore) WHERE { ?r a ex:DQRule ; ex:score ?s . } }
          ?rule a ex:DQRule ; ex:score ?score ; ex:techSystem ?techSystem ; ex:techGroup ?techGroup ; ex:dataset ?dataset .
          OPTIONAL { ?rule ex:dataElement ?dataElement }
          OPTIONAL { ?rule ex:dataelement ?dataElement }  # lower-case tolerance
          OPTIONAL { ?rule ex:ruleCode ?ruleCode }
          FILTER (xsd:decimal(?score) = ?minScore)
          BIND(CONCAT(STR(?techSystem), ".", STR(?techGroup), ".", STR(?dataset),
                      IF(BOUND(?dataElement), CONCAT(".", STR(?dataElement)), "")) AS ?path)
        }
    """,
}

DEFAULT_PREFIX_LINES = [
    "PREFIX ex: <http://example.org/>",
    "PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>",
]

def _normalize_query(q: str) -> str:
    if not q: return ""
    q = re.sub(r"```(?:sparql)?\s*([\s\S]*?)```", r"\1", q, flags=re.IGNORECASE)
    q = q.replace("“", '"').replace("”", '"').replace("’", "'")
    return q.strip()

def _ensure_prefixes(q: str) -> str:
    has_ex  = re.search(r"(?im)^\s*prefix\s+ex\s*:", q) is not None
    has_xsd = re.search(r"(?im)^\s*prefix\s+xsd\s*:", q) is not None
    needs_ex  = ("ex:"  in q) and not has_ex
    needs_xsd = ("xsd:" in q) and not has_xsd
    if needs_ex or needs_xsd:
        header = []
        if needs_ex:  header.append(DEFAULT_PREFIX_LINES[0])
        if needs_xsd: header.append(DEFAULT_PREFIX_LINES[1])
        q = "\n".join(header) + "\n" + q
    return q

def run_sparql(query: str):
    q = _ensure_prefixes(_normalize_query(query))
    r = requests.post(
        REPO_URL,
        data=q.encode("utf-8"),
        headers={"Content-Type": "application/sparql-query", "Accept": "application/sparql-results+json"},
        timeout=60,
    )
    if r.status_code != 200:
        raise requests.HTTPError(f"GraphDB {r.status_code}: {r.text}", response=r)
    bindings = r.json().get("results", {}).get("bindings", [])
    return [{k: v.get("value") for k, v in b.items()} for b in bindings]

queries_bp = Blueprint("queries", __name__)

@queries_bp.get("/list")
def list_queries():
    return jsonify(sorted(list(QUERIES.keys())))

@queries_bp.get("/run")
def run_named():
    name = request.args.get("name")
    if not name: return jsonify(error="Missing ?name=..."), 400
    q = QUERIES.get(name)
    if not q: return jsonify(error=f"Unknown query name: {name}"), 404
    try:
        rows = run_sparql(q)
        return jsonify(name=name, rows=rows)
    except requests.HTTPError as e:
        return jsonify(error="GraphDB error", status=getattr(e.response,"status_code",500),
                       details=getattr(e.response,"text","")), 502
    except Exception as e:
        return jsonify(error=str(e)), 500

@queries_bp.post("/run-raw")
def run_raw():
    if request.is_json:
        q = (request.json or {}).get("query", "")
    else:
        q = request.get_data(as_text=True) or ""
    q = _normalize_query(q)
    if not q.strip(): return jsonify(error="Provide a SPARQL query."), 400
    try:
        rows = run_sparql(q)
        return jsonify(rows=rows, query=q)
    except requests.HTTPError as e:
        return jsonify(error="GraphDB error", status=getattr(e.response,"status_code",500),
                       details=getattr(e.response,"text",""), query=q), 502
    except Exception as e:
        return jsonify(error=str(e), query=q), 500
