from pathlib import Path
from openpyxl import Workbook
import pytest
from scripts.validate_places import validate

def test_official_catalog_validator(tmp_path):
    wb=Workbook();ws=wb.active;ws.append(["장소명","장소코드"])
    for n in range(121):ws.append([f"장소{n}",f"POI{n:03d}"])
    path=tmp_path/"catalog.xlsx";wb.save(path)
    assert len(validate(path))==121

def test_rejects_unverified_incomplete_catalog(tmp_path):
    wb=Workbook();ws=wb.active;ws.append(["장소명","장소코드"]);ws.append(["A","POI001"])
    path=tmp_path/"partial.xlsx";wb.save(path)
    with pytest.raises(ValueError):validate(path)

def test_cluster_script_present():
    html=(Path(__file__).resolve().parents[1]/"web"/"index.html").read_text()
    assert "L.markerClusterGroup" in html
    assert "cluster.addLayer(layer)" in html
