"""Fetch ITS national transport CCTV metadata securely at Pages build time.

No API keys or stream URLs are published. Embedding remains disabled without
explicit provider permission. Official TOPIS map is the viewing fallback.
"""
import json
import os
import urllib.parse
import urllib.request

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

def fetch_cameras(key):
    if not key:
        return []
    gathered = []
    for road in ("its", "ex"):
        for camera_type in ("4", "5"):
            query = urllib.parse.urlencode({
                "apiKey": key, "type": road, "cctvType": camera_type,
                "minX": BOUNDS[0], "maxX": BOUNDS[1],
                "minY": BOUNDS[2], "maxY": BOUNDS[3],
                "getType": "json"})
            # Request URLs containing keys must never be printed or logged.
            with urllib.request.urlopen(ENDPOINT + "?" + query, timeout=12) as res:
                body = res.read(2_000_001)
            if len(body) > 2_000_000:
                raise ValueError("ITS response is too large")
            gathered.extend(parse_items(json.loads(body)))
    unique = {(x["name"], x["lat"], x["lng"]): x for x in gathered}
    return list(unique.values())
