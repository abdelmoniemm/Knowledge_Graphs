import os, requests
from pathlib import Path
from flask import Blueprint, jsonify

# ===== CONFIG =====
GRAPHDB_BASE = os.environ.get("GRAPHDB_BASE", "http://localhost:3030")
REPO_ID      = os.environ.get("GRAPHDB_REPO", "bachelor2025")
# Add Auth Credentials
DB_USER      = "admin"
DB_PASS      = "admin"

# Fuseki Endpoints
DATA_URL     = f"{GRAPHDB_BASE.rstrip('/')}/{REPO_ID}/data"
UPDATE_URL   = f"{GRAPHDB_BASE.rstrip('/')}/{REPO_ID}/update"

REPO_ROOT    = Path(__file__).resolve().parents[1]
DATA_DIR     = REPO_ROOT / "data"
OUTPUT_TTL   = DATA_DIR / "output.ttl"

graphdb_bp = Blueprint("graphdb", __name__)

@graphdb_bp.post("/import")
def import_ttl():
    if not OUTPUT_TTL.exists():
        return jsonify(error="output.ttl not found. Run the pipeline first."), 400

    print(f"--> Importing to Fuseki: {DATA_URL} ...")
    
    try:
        ttl_data = OUTPUT_TTL.read_bytes()
        r = requests.post(
            f"{DATA_URL}?default", 
            data=ttl_data,
            headers={"Content-Type": "text/turtle"},
            auth=(DB_USER, DB_PASS),
            timeout=60
        )
        r.raise_for_status()
        return jsonify(ok=True)
        
    except requests.exceptions.RequestException as e:
        msg = e.response.text if e.response else str(e)
        return jsonify(error="Import failed", status=500, details=msg), 500

@graphdb_bp.post("/clear")
def clear_repo():
    try:
        r = requests.post(
            UPDATE_URL,
            data={"update": "CLEAR DEFAULT"},
            auth=(DB_USER, DB_PASS),  # <--- AUTH ADDED HERE
            timeout=60
        )
        r.raise_for_status()
        return jsonify(ok=True)
    except Exception as e:
        return jsonify(error="Clear failed", details=str(e)), 500