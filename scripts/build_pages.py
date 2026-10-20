"""Build a GitHub Pages artifact using public citydata API snapshots.

No secret values or raw upstream request URLs are written to output.
"""
import json
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

from server.app import PLACES, fetch_citydata

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"

def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "web", OUT)
    folder = OUT / "data" / "live"
    folder.mkdir(parents=True, exist_ok=True)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUT / "data" / "places.json").write_text(
        json.dumps(PLACES, ensure_ascii=False, indent=2), encoding="utf-8")
    key = os.environ.get("SEOUL_API_KEY", "").strip()
    max_calls = max(0, min(int(os.environ.get("SEOUL_MAX_CALLS", "15")), 15))
    calls = 0
    for place in PLACES:
        if (key or place["id"] == "POI001") and calls < max_calls:
            calls += 1
            if calls > 1:
                time.sleep(0.25)
            record = fetch_citydata(place)
        else:
            record = {**place, "congestion": None, "population_min": None,
                      "population_max": None, "observed_at": None,
                      "fetched_at": datetime.now(timezone.utc).isoformat(),
                      "status": "UNAVAILABLE", "source": "서울시 실시간 도시데이터",
                      "error": "API_KEY_REQUIRED" if not key and place["id"] != "POI001" else "REQUEST_BUDGET_EXCEEDED"}
        (folder / (place["id"] + ".json")).write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Pages artifact ready: {OUT}; API requests: {calls}/{max_calls}")

if __name__ == "__main__":
    build()
