from pathlib import Path
from scripts.build_pages import build

def test_build_without_key(monkeypatch):
    monkeypatch.delenv("SEOUL_API_KEY", raising=False)
    # Avoid network in CI; mock live adapter for sample place.
    monkeypatch.setattr("scripts.build_pages.fetch_citydata",
                        lambda place: {**place, "status": "API_ERROR", "congestion": None})
    build()
    root = Path(__file__).resolve().parent.parent / "_site"
    assert (root / "index.html").exists()
    assert (root / "data" / "places.json").exists()
    assert (root / "data" / "live" / "POI001.json").exists()
    assert (root / "data" / "live" / "POI005.json").exists()
    assert "/api/places" not in (root / "index.html").read_text(encoding="utf-8")
