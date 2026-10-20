from fastapi.testclient import TestClient
from server.app import app, parse_citydata
import pytest

client = TestClient(app)

def test_health():
    assert client.get("/api/health").json()["ok"] is True

def test_places():
    assert len(client.get("/api/places").json()) == 121

def test_missing_place():
    assert client.get("/api/places/unknown/live").status_code == 404

def test_parse_citydata():
    xml = b"<root><AREA_CONGEST_LVL>Normal</AREA_CONGEST_LVL><AREA_PPLTN_MIN>1,000</AREA_PPLTN_MIN><AREA_PPLTN_MAX>2,000</AREA_PPLTN_MAX></root>"
    assert parse_citydata(xml)["population_min"] == 1000

def test_api_error():
    with pytest.raises(ValueError, match="INFO-100"):
        parse_citydata(b"<root><RESULT><CODE>INFO-100</CODE></RESULT></root>")
