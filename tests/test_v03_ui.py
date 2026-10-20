from pathlib import Path

def test_crowd_layers_search_filter_and_static_urls():
    root = Path(__file__).resolve().parents[1]
    for page in ["index.html", "web/index.html"]:
        html = (root / page).read_text(encoding="utf-8")
        for expected in ['id="search"', 'id="filter"', 'function updateMap(', 'function draw()', 'className:"map-label"', './data/live/']:
            assert expected in html
        assert '"/api/places"' not in html
