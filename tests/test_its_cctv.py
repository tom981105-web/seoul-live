import json
from scripts.its_cctv import parse_items, fetch_cameras, TOPIS

def test_parse_official_cameras_does_not_publish_stream_or_key():
    data={"response":{"header":{"resultCode":"0"},"data":[
      {"cctvname":"서울 테스트 도로 CCTV","coordx":"127.010","coordy":"37.550",
       "cctvurl":"https://stream.example/test.m3u8?secret=PRIVATE"},
      {"cctvname":"invalid","coordx":"124","coordy":"34"}
    ]}}
    got=parse_items(data)
    assert len(got)==1
    assert got[0]["official_url"]==TOPIS
    assert got[0]["embed_allowed"] is False
    assert "stream" not in json.dumps(got)
    assert "PRIVATE" not in json.dumps(got)

def test_no_key_no_external_call():
    assert fetch_cameras("")==[]

def test_non_success_is_not_silent():
    import pytest
    with pytest.raises(ValueError):
        parse_items({"response":{"header":{"resultCode":"1"},"data":[]}})
