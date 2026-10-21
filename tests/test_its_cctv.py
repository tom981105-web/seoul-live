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

def test_safe_http_error_redacts_url():
    import io
    from urllib.error import HTTPError
    from scripts.its_cctv import safe_error
    exc=HTTPError("https://example.com/?apiKey=SECRET", 403, "Forbidden", {}, io.BytesIO())
    assert safe_error(exc)=="HTTP_403"

def test_partial_cctv_failure_retains_results(monkeypatch, capsys):
    import io
    import json
    from urllib.error import HTTPError
    from scripts import its_cctv
    class Response:
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def read(self,n):return json.dumps({"response":{"header":{"resultCode":"0"},"data":[{"cctvname":"A","coordx":"127.01","coordy":"37.55"}]}}).encode()
    count=[0]
    def urlopen(url,timeout=12):
        count[0]+=1
        if count[0]==1:
            raise HTTPError(url,403,"Forbidden",{},io.BytesIO())
        return Response()
    monkeypatch.setattr(its_cctv.urllib.request,"urlopen",urlopen)
    cameras=its_cctv.fetch_cameras("SECRET")
    assert len(cameras)==1
    log=capsys.readouterr().out
    assert "HTTP_403" in log
    assert "success=3 failed=1" in log
    assert "SECRET" not in log
