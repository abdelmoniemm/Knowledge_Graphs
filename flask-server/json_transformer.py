import json
from pathlib import Path

class JsonTransformer:
    def __init__(self, data_json_path: Path):
        self.data_json_path = Path(data_json_path)
        self.data_json_path.parent.mkdir(parents=True, exist_ok=True)

    def write_data_json(self, raw_json: str) -> None:
        try:
            parsed = json.loads(raw_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        if isinstance(parsed, list):
            payload = {"rules": parsed}
        elif isinstance(parsed, dict):
            payload = parsed if isinstance(parsed.get("rules"), list) else {"rules":[parsed]}
        else:
            raise ValueError("JSON must be an array or an object")
        self.data_json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
