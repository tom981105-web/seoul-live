import json
from pathlib import Path
from scripts import build_pages
from server.app import PLACES

def test_unique_place_catalog():
    assert len(PLACES) == 15
    assert len({p["id"] for p in PLACES}) == len(PLACES)
    assert len({p["query"] for p in PLACES}) == len(PLACES)
    assert all(37.3 < p["lat"] < 37.8 and 126.7 < p["lng"] < 127.3 for p in PLACES)

def test_request_budget(monkeypatch, tmp_path):
    monkeypatch.setattr(build_pages, "OUT", tmp_path / "out")
    monkeypatch.setenv("SEOUL_API_KEY", "test-key")
    monkeypatch.setenv("SEOUL_MAX_CALLS", "3")
    monkeypatch.setenv("GITHUB_RUN_NUMBER", "1")
    monkeypatch.setattr(build_pages.time, "sleep", lambda _: None)
    monkeypatch.setattr(build_pages, "previous_json", lambda _: None)
    called=[]
    def fake(place):
        called.append(place["id"])
        return {**place, "status":"LIVE", "congestion":"보통"}
    monkeypatch.setattr(build_pages, "fetch_citydata", fake)
    build_pages.build()
    assert len(called)==3
    assert len(list((build_pages.OUT/"data"/"live").glob("*.json")))==15
    fourth=json.loads((build_pages.OUT/"data"/"live"/"POI004.json").read_text())
    assert fourth["status"]=="UNAVAILABLE"
    assert fourth["error"]=="REQUEST_BUDGET_EXCEEDED"

from scripts.build_pages import choose_batch

def test_rotating_selection():
    catalog=[{"id":str(i)} for i in range(5)]
    assert choose_batch(catalog,1,2)==["0","1"]
    assert choose_batch(catalog,2,2)==["2","3"]
    assert choose_batch(catalog,3,2)==["4","0"]
    assert choose_batch(catalog,4,2)==["1","2"]
    assert choose_batch(catalog,1,0)==[]
