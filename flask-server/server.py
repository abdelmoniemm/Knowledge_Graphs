# flask-server/server.py
from pathlib import Path
import subprocess, os

from dotenv import load_dotenv
load_dotenv(Path(__file__).with_name(".env"))  # load flask-server/.env

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from json_transformer import JsonTransformer
from queries_api import queries_bp
from graphdb_api import graphdb_bp
from nl2sparql_openai import nl2sparql_bp
# near the other imports


# after other blueprint registrations



app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})



# Blueprints
app.register_blueprint(graphdb_bp, url_prefix="/api/graphdb")
app.register_blueprint(queries_bp,  url_prefix="/api/queries")
app.register_blueprint(nl2sparql_bp, url_prefix="/api/nl2sparql")

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

# Paths
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR   = REPO_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RULES_YML      = DATA_DIR / "rules.yml"
RULES_RML_TTL  = DATA_DIR / "rules.rml.ttl"
OUTPUT_TTL     = DATA_DIR / "output.ttl"
DATA_JSON      = DATA_DIR / "data.json"

# Docker images
YARRRML_IMAGE   = "rmlio/yarrrml-parser:1.10.0"
RMLMAPPER_IMAGE = "rmlio/rmlmapper-java:v7.3.3"

def run(cmd: list) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(
            "Command failed:\n" + " ".join(cmd) +
            "\n\nSTDOUT:\n" + p.stdout + "\nSTDERR:\n" + p.stderr
        )
    return p.stdout

def compile_yarrrml_to_rml():
    if not RULES_YML.exists():
        raise FileNotFoundError(f"Missing {RULES_YML}")
    # Skip if already present
    if RULES_RML_TTL.exists():
        return "rules.rml.ttl already exists; skipping YARRRML → RML."
    return run([
        "docker","run","--rm","-i",
        "-v", f"{str(DATA_DIR)}:/data",
        YARRRML_IMAGE,
        "-i","/data/rules.yml",
        "-o","/data/rules.rml.ttl",
    ])

def run_rmlmapper_to_ttl():
    return run([
        "docker","run","--rm","-i",
        "-v", f"{str(DATA_DIR)}:/data",
        RMLMAPPER_IMAGE,
        "-m","/data/rules.rml.ttl",
        "-o","/data/output.ttl",
    ])

@app.get("/health")
def health():
    return jsonify(ok=True)

@app.get("/")
def home():
    return "<p>Backend is running. POST /api/process-upload with a JSON file.</p>"

@app.post("/api/process-upload")
def process_upload():
    try:
        if "file" not in request.files:
            return jsonify(error="No 'file' in form-data."), 400
        f = request.files["file"]
        if not f or f.filename == "":
            return jsonify(error="No file selected."), 400
        if not f.filename.lower().endswith(".json"):
            return jsonify(error="Please upload a .json file."), 400

        # Write data.json
        raw = f.read().decode("utf-8")
        JsonTransformer(DATA_JSON).write_data_json(raw)

        # YARRRML -> RML (skip if rules.rml.ttl exists)
        compile_yarrrml_to_rml()
        if not RULES_RML_TTL.exists():
            return jsonify(error="rules.rml.ttl was not generated."), 500

        # RML -> TTL
        run_rmlmapper_to_ttl()
        if not OUTPUT_TTL.exists():
            return jsonify(error="output.ttl was not generated."), 500

        return jsonify(
            ok=True,
            note="Ensure rules.yml logical source points to /data/data.json inside the containers.",
            files={
                "data_json": "/files/data.json",
                "rules_rml_ttl": "/files/rules.rml.ttl",
                "output_ttl": "/files/output.ttl",
            }
        )
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

@app.get("/files/<path:filename>")
def files(filename):
    return send_from_directory(str(DATA_DIR), filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)  # 127.0.0.1:5000
