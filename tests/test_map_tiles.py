from pathlib import Path

def test_map_uses_keyless_osm_tiles():
    root = Path(__file__).resolve().parents[1]
    for path in ("index.html", "web/index.html"):
        html = (root / path).read_text(encoding="utf-8")
        assert "https://tile.openstreetmap.org/{z}/{x}/{y}.png" in html
        assert "basemaps.cartocdn.com" not in html
        assert "OpenStreetMap contributors" in html
