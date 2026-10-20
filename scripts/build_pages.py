"""Build a GitHub Pages artifact using public citydata API snapshots.

No secret values or raw upstream request URLs are written to output.
"""
import json
import os
import shutil
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

from server.app import PLACES, fetch_citydata

PUBLIC_BASE = "https://tom981105-web.github.io/seoul-live/data/"
HISTORY_LIMIT = 48
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"

def previous_json(path):
    """Best effort: read last published Pages snapshot; no API key involved."""
    try:
        with urllib.request.urlopen(PUBLIC_BASE + path, timeout=5) as response:
            if response.status != 200:
                return None
            data = response.read(250_001)
        if len(data) > 250_000:
            return None
        return json.loads(data)
    except (OSError, ValueError, UnicodeError, urllib.error.URLError):
        return None

def keep_history(previous, record):
    """Keep valid, distinct time observations only; never fabricate values."""
    items = previous if isinstance(previous, list) else []
    items = [p for p in items if isinstance(p, dict) and p.get("observed_at")]
    if record.get("status") == "LIVE" and record.get("observed_at") and record.get("population_min") is not None and record.get("population_max") is not None:
        items.append({"observed_at": record["observed_at"],
                      "population_min": record["population_min"],
                      "population_max": record["population_max"],
                      "congestion": record.get("congestion")})
    unique = {p["observed_at"]: p for p in items}
    return sorted(unique.values(), key=lambda p: p["observed_at"])[-HISTORY_LIMIT:]

def choose_batch(places, run_number, max_calls):
    """Round-robin fixed-size slice with wrap-around, no unnecessary requests."""
    if not places or max_calls <= 0:
        return []
    size = min(max_calls, len(places))
    start = ((max(1, run_number) - 1) * size) % len(places)
    return [places[(start+i) % len(places)]["id"] for i in range(size)]

def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "web", OUT)
    folder = OUT / "data" / "live"
    folder.mkdir(parents=True, exist_ok=True)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUT / "data" / "places.json").write_text(
        json.dumps(PLACES, ensure_ascii=False, indent=2), encoding="utf-8")
    history_dir = OUT / "data" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    key = os.environ.get("SEOUL_API_KEY", "").strip()
    max_calls = max(0, min(int(os.environ.get("SEOUL_MAX_CALLS", "15")), 15))
    run_number = int(os.environ.get("GITHUB_RUN_NUMBER", "1"))
    eligible = [p for p in PLACES if key or p["id"] == "POI001"]
    batch_ids = set(choose_batch(eligible, run_number, max_calls))
    calls = 0
    for place in PLACES:
        previous = previous_json("live/" + place["id"] + ".json")
        history = previous_json("history/" + place["id"] + ".json")
        if place["id"] in batch_ids:
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
        if record.get("status") != "LIVE" and isinstance(previous, dict) and previous.get("congestion") and previous.get("observed_at"):
            record = {**previous, "status": "DELAYED", "error": record.get("error", "NOT_REFRESHED")}
        elif record.get("status") == "LIVE" and record.get("observed_at") == (previous or {}).get("observed_at"):
            # Repeated source observation must not be shown as newly updated.
            record = {**record, "status": "DELAYED", "error": "OBSERVATION_UNCHANGED"}
        latest_history = keep_history(history, record)
        (history_dir / (place["id"] + ".json")).write_text(
            json.dumps(latest_history, ensure_ascii=False, indent=2), encoding="utf-8")
        (folder / (place["id"] + ".json")).write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "data" / "collection-status.json").write_text(
        json.dumps({"run_number": run_number, "requests": calls,
                    "budget": max_calls, "catalog_size": len(PLACES),
                    "generated_at": datetime.now(timezone.utc).isoformat()},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Pages artifact ready: {OUT}; API requests: {calls}/{max_calls}; rotation: {run_number}")

if __name__ == "__main__":
    build()
