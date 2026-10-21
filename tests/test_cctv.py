import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_cctv_ui_has_verified_topis_fallback():
    html=(ROOT/"web"/"index.html").read_text(encoding="utf-8")
    assert "https://topis.seoul.go.kr/map/openCctvMap.do" in html
    assert 'id="cctv-list"' in html
    assert "kmBetween(" in html
    assert "embed_allowed===true" in html
    assert "공식 CCTV 목록을 아직 연결하지 않았습니다" in html

def test_no_unverified_cameras_fabricated():
    cameras=json.loads((ROOT/"web"/"data"/"cctv.json").read_text(encoding="utf-8"))
    assert cameras == []
