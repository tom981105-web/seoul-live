from scripts.build_pages import compatible_snapshot, load_previous
from server.app import PLACES

def test_rejects_pre_official_place_code_reuse():
    place=PLACES[0]
    assert place["id"]=="POI001"
    assert not compatible_snapshot(place, {"id":"POI001","name":"광화문·덕수궁","congestion":"보통"})
    assert compatible_snapshot(place, {"id":"POI001","name":place["name"],"congestion":"보통"})

def test_concurrent_cache_rejects_misidentified_history(monkeypatch):
    from scripts import build_pages
    def fake(path):
        if path.startswith("live/"):
            return {"id":"POI001","name":"광화문·덕수궁"}
        return [{"observed_at":"2026-10-20 11:00","population_min":100}]
    monkeypatch.setattr(build_pages,"previous_json",fake)
    cache=load_previous(PLACES[:2])
    assert cache["POI001"]==(None,None)
