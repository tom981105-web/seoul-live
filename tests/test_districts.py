from pathlib import Path
from server.app import PLACES

def test_districts_and_filter():
    assert len(PLACES)==15
    assert all(p.get("district") for p in PLACES)
    html=(Path(__file__).resolve().parents[1]/"web"/"index.html").read_text()
    assert 'id="district"' in html
    assert 'el("district").addEventListener("change",draw)' in html
