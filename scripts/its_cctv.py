"""Fetch ITS national transport CCTV metadata securely at Pages build time.

No API keys or stream URLs are published. Embedding remains disabled without
explicit provider permission. Official TOPIS map is the viewing fallback.
"""
import json
import os
import urllib.parse
import urllib.request
import urllib.error
import socket

ENDPOINT = "https://openapi.its.go.kr:9443/cctvInfo"
TOPIS = "https://topis.seoul.go.kr/map/openCctvMap.do"
BOUNDS = (126.76, 127.24, 37.40, 37.72)

def parse_items(document):
    response = document.get("response", {})
    header = response.get("header", {})
    if header.get("resultCode") not in (None, "0", 0):
        raise ValueError("ITS API returned unsuccessful status")
    items = response.get("data") or []
    if isinstance(items, dict):
        items = items.get("item", []) or []
    if isinstance(items, dict):
        items = [items]
    if not isinstance(items, list):
        raise ValueError("Invalid ITS CCTV response")
    result = []
    seen = set()
    for obj in items:
        if not isinstance(obj, dict):
            continue
        try:
            lat, lng = float(obj["coordy"]), float(obj["coordx"])
        except (KeyError, ValueError, TypeError):
            continue
        if not (37.3 < lat < 37.8 and 126.7 < lng < 127.3):
            continue
        name = str(obj.get("cctvname") or "").strip()[:120]
        if not name:
            continue
        ident = (name, round(lat, 5), round(lng, 5))
        if ident in seen:
            continue
        seen.add(ident)
        result.append({"name": name, "lat": lat, "lng": lng,
                       "source": "ITS 국가교통정보센터",
                       "official_url": TOPIS, "embed_allowed": False})
    return result

def safe_error(exc):
    """Emit only a safe category; exception text may contain the secret URL."""
    if isinstance(exc, urllib.error.HTTPError):
        return "HTTP_" + str(exc.code)
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "TIMEOUT"
    if isinstance(exc, urllib.error.URLError):
        return "NETWORK_ERROR"
    if isinstance(exc, json.JSONDecodeError):
        return "INVALID_JSON"
    if isinstance(exc, ValueError):
        return "INVALID_RESPONSE"
    return "REQUEST_ERROR"

def fetch_cameras(key):
    if not key:
        return []
    gathered = []
    successes = 0
    failures = 0
    for road in ("its", "ex"):
        for camera_type in ("4", "5"):
            query = urllib.parse.urlencode({
                "apiKey": key, "type": road, "cctvType": camera_type,
                "minX": BOUNDS[0], "maxX": BOUNDS[1],
                "minY": BOUNDS[2], "maxY": BOUNDS[3],
                "getType": "json"})
            # Request URLs containing keys must never be printed or logged.
            try:
                with urllib.request.urlopen(ENDPOINT + "?" + query, timeout=12) as res:
                    body = res.read(2_000_001)
                if len(body) > 2_000_000:
                    raise ValueError("ITS response is too large")
                document = json.loads(body)
                code = (document.get("response") or {}).get("header", {}).get("resultCode")
                items = parse_items(document)
                gathered.extend(items)
                successes += 1
                print(f"ITS CCTV request road={road} type={camera_type} result={code} count={len(items)}")
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, ValueError, TypeError, KeyError) as exc:
                failures += 1
                print(f"ITS CCTV request road={road} type={camera_type} error={safe_error(exc)}")
    print(f"ITS CCTV requests: success={successes} failed={failures}")
    if successes == 0:
        raise ValueError("ALL_ITS_CCTV_REQUESTS_FAILED")
    unique = {(x["name"], x["lat"], x["lng"]): x for x in gathered}
    return list(unique.values())
