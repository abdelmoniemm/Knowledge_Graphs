import os, requests
from pathlib import Path
from flask import Blueprint, jsonify

# Config
DB_BASE = os.environ.get("GRAPHDB_BASE", "http://localhost:3030")
REPO_ID = os.environ.get("GRAPHDB_REPO", "bachelor2025")

# Fuseki Endpoints
# Data endpoint (Graph Store Protocol) for import/clear
DATA_URL = f"{DB_BASE.rstrip('/')}/{REPO_ID}/data"
# Update endpoint for SPARQL UPDATE queries
UPDATE_URL = f"{DB_BASE.rstrip('/')}/{REPO_ID}/update"

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
OUTPUT_TTL = DATA_DIR / "output.ttl"

triplestore_bp = Blueprint("triplestore", __name__)

@triplestore_bp.post("/import")
def import_ttl():
    if not OUTPUT_TTL.exists():
        return jsonify(error="output.ttl not found."), 400
    
    ttl_data = OUTPUT_TTL.read_bytes()
    
    # Fuseki GSP: PUT or POST to /data?default
    # Content-Type must be text/turtle for .ttl files
    try:
        r = requests.post(
            f"{DATA_URL}?default",
            data=ttl_data,
            headers={"Content-Type": "text/turtle"},
            timeout=60
        )
        r.raise_for_status()
    except requests.RequestException as e:
        return jsonify(error="Import failed", details=str(e)), 502
        
    return jsonify(ok=True)

@triplestore_bp.post("/clear")
def clear_repo():
    # SPARQL Update to clear graph
    sparql_update = "CLEAR DEFAULT"
    
    try:
        r = requests.post(
            UPDATE_URL,
            data={"update": sparql_update},
            # Fuseki accepts form-encoded 'update' parameter
            timeout=60
        )
        r.raise_for_status()
    except requests.RequestException as e:
        return jsonify(error="Clear failed", details=str(e)), 502

    return jsonify(ok=True)