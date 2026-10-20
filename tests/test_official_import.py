import json
import zipfile
from pathlib import Path
from openpyxl import Workbook
import pytest
from scripts.import_official_places import build_catalog, write_catalog

def fixtures(tmp_path, missing=0):
    xlsx=tmp_path/"official.xlsx"
    book=Workbook();sheet=book.active
    sheet.append(["장소명","장소코드"])
    features=[]
    for i in range(121):
        code=f"POI{i:03d}"
        sheet.append([f"장소 {i}",code])
        if i<121-missing:
            x=126.9+i*0.001;y=37.45+i*0.001
            features.append({"type":"Feature","properties":{"code":code},"geometry":{"type":"Polygon","coordinates":[[[x,y],[x+.001,y],[x+.001,y+.001],[x,y+.001],[x,y]]]}})
    book.save(xlsx)
    z=tmp_path/"regions.zip"
    with zipfile.ZipFile(z,"w") as archive:
        archive.writestr("areas.geojson",json.dumps({"type":"FeatureCollection","features":features}))
    return xlsx,z

def test_full_official_import(tmp_path):
    xlsx,z=fixtures(tmp_path)
    data=build_catalog(xlsx,z)
    assert len(data)==121
    assert data[0]["query"]=="POI000"
    output=tmp_path/"catalog.json"
    write_catalog(xlsx,z,output)
    assert len(json.loads(output.read_text()))==121

def test_incomplete_geometry_rejected(tmp_path):
    xlsx,z=fixtures(tmp_path,missing=1)
    with pytest.raises(ValueError,match="120/121"):
        build_catalog(xlsx,z)
