"""SEOUL LIVE MVP: Seoul citydata adapter and web API."""
from __future__ import annotations
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="SEOUL LIVE", version="0.1.0")
# Representative marker coordinates, not official polygon centroids.
PLACES = [
    {"id": "POI001", "name": "광화문·덕수궁", "query": "광화문·덕수궁", "lat": 37.571, "lng": 126.9769},
    {"id": "POI002", "name": "강남역", "query": "강남역", "lat": 37.4979, "lng": 127.0276},
    {"id": "POI003", "name": "홍대 관광특구", "query": "홍대 관광특구", "lat": 37.5558, "lng": 126.9237},
    {"id": "POI004", "name": "잠실 관광특구", "query": "잠실 관광특구", "lat": 37.5133, "lng": 127.1001},
    {"id": "POI005", "name": "여의도한강공원", "query": "여의도한강공원", "lat": 37.526, "lng": 126.934},
    {"id": "POI006", "name": "명동 관광특구", "query": "명동 관광특구", "lat": 37.5636, "lng": 126.9845},
    {"id": "POI007", "name": "이태원 관광특구", "query": "이태원 관광특구", "lat": 37.5346, "lng": 126.9941},
    {"id": "POI008", "name": "동대문 관광특구", "query": "동대문 관광특구", "lat": 37.5689, "lng": 127.0092},
    {"id": "POI009", "name": "광화문광장", "query": "광화문광장", "lat": 37.5725, "lng": 126.9769},
    {"id": "POI010", "name": "서울숲공원", "query": "서울숲공원", "lat": 37.5446, "lng": 127.0374},
    {"id": "POI011", "name": "반포한강공원", "query": "반포한강공원", "lat": 37.5097, "lng": 126.9947},
    {"id": "POI012", "name": "뚝섬한강공원", "query": "뚝섬한강공원", "lat": 37.5293, "lng": 127.0662},
    {"id": "POI013", "name": "남산공원", "query": "남산공원", "lat": 37.5507, "lng": 126.9909},
    {"id": "POI014", "name": "서울광장", "query": "서울광장", "lat": 37.5657, "lng": 126.978},
    {"id": "POI015", "name": "어린이대공원", "query": "어린이대공원", "lat": 37.5483, "lng": 127.0819},
]
_cache: dict[str, tuple[float, dict]] = {}

def _text(root: ET.Element, tag: str) -> str | None:
    node = root.find(".//" + tag)
    return node.text.strip() if node is not None and node.text else None

def parse_citydata(xml: bytes) -> dict:
    root = ET.fromstring(xml)
    code = _text(root, "CODE")
    if code and code != "INFO-000":
        raise ValueError("Upstream API status: " + code)
    level = _text(root, "AREA_CONGEST_LVL")
    if not level:
        raise ValueError("Citydata congestion field missing")
    def num(tag):
        value = _text(root, tag)
        return int(value.replace(",", "")) if value else None
    return {"congestion": level, "population_min": num("AREA_PPLTN_MIN"),
            "population_max": num("AREA_PPLTN_MAX"), "observed_at": _text(root, "PPLTN_TIME"),
            "source": "서울시 실시간 도시데이터", "status": "LIVE"}

def fetch_citydata(place: dict) -> dict:
    now = time.monotonic()
    cached = _cache.get(place["id"])
    if cached and now - cached[0] < 300:
        return cached[1]
    key = os.getenv("SEOUL_API_KEY", "sample").strip() or "sample"
    url = ("http://openapi.seoul.go.kr:8088/" + urllib.parse.quote(key, safe="")
           + "/xml/citydata/1/5/" + urllib.parse.quote(place["query"], safe=""))
    try:
        with urllib.request.urlopen(url, timeout=8) as response:
            xml = response.read(3_000_001)
        if len(xml) > 3_000_000:
            raise ValueError("Citydata response too large")
        parsed = parse_citydata(xml)
        item = {**place, **parsed, "fetched_at": datetime.now(timezone.utc).isoformat()}
        _cache[place["id"]] = (now, item)
        return item
    except Exception as exc:
        # Never return exception string: upstream errors can contain the API key in URL.
        error = type(exc).__name__
        if cached:
            return {**cached[1], "status": "DELAYED", "error": error}
        return {**place, "status": "API_ERROR", "congestion": None,
                "population_min": None, "population_max": None,
                "observed_at": None, "error": error}

@app.get("/api/health")
def health():
    return {"ok": True, "version": "0.1.0"}

@app.get("/api/places")
def places():
    return PLACES

@app.get("/api/places/{place_id}/live")
def live(place_id: str):
    place = next((p for p in PLACES if p["id"] == place_id), None)
    if place is None:
        raise HTTPException(status_code=404, detail="Unknown place")
    return fetch_citydata(place)

@app.get("/")
def homepage():
    return FileResponse(Path(__file__).resolve().parent.parent / "web" / "index.html")
