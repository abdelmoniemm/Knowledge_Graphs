
import os, requests
from pathlib import Path
from flask import Blueprint, jsonify

GRAPHDB_BASE = os.environ.get("GRAPHDB_BASE", "http://localhost:7200")
REPO_ID      = os.environ.get("GRAPHDB_REPO", "bachelor2025")
REPO_URL     = f"{GRAPHDB_BASE.rstrip('/')}/repositories/{REPO_ID}"
REPO_ROOT    = Path(__file__).resolve().parents[1]
DATA_DIR     = REPO_ROOT / "data"
OUTPUT_TTL   = DATA_DIR / "output.ttl"

graphdb_bp = Blueprint("graphdb", __name__)

@graphdb_bp.post("/import")
def import_ttl():
    if not OUTPUT_TTL.exists():
        return jsonify(error="output.ttl not found. Run the pipeline first."), 400
    # GraphDB REST for import via /statements
    ttl = OUTPUT_TTL.read_bytes()
    r = requests.post(
        f"{REPO_URL}/statements",
        data=ttl,
        headers={"Content-Type": "text/turtle"},
        timeout=60,
    )
    if r.status_code not in (200,204):
        return jsonify(error="Import failed", status=r.status_code, details=r.text), 502
    return jsonify(ok=True)

@graphdb_bp.post("/clear")
def clear_repo():
    update = "CLEAR ALL"
    r = requests.post(
        f"{REPO_URL}/statements",
        data=update.encode("utf-8"),
        headers={"Content-Type": "application/sparql-update"},
        timeout=60,
    )
    if r.status_code not in (200,204):
        return jsonify(error="Clear failed", status=r.status_code, details=r.text), 502
    return jsonify(ok=True)
