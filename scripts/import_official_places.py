"""Convert the official Seoul XLSX and geographic ZIP into a reviewed 121-place catalog.

Run: python -m scripts.import_official_places places.xlsx areas.zip
No guessed coordinates or names: abort if shapes cannot be matched to codes/names.
Accepts zipped GeoJSON in WGS84 or zipped shapefile with a readable .prj.
"""
import json
import sys
import zipfile
from pathlib import Path
from scripts.validate_places import validate

def centroid_polygon(coordinates):
    points=[]
    def collect(o):
        if isinstance(o,(list,tuple)) and len(o)>=2 and all(isinstance(v,(int,float)) for v in o[:2]):
            points.append((float(o[0]),float(o[1])))
        elif isinstance(o,(list,tuple)):
            for i in o:collect(i)
    collect(coordinates)
    if not points:raise ValueError("Empty geometry")
    return sum(x for x,y in points)/len(points),sum(y for x,y in points)/len(points)

def features_from_zip(path):
    import shapefile
    from pyproj import CRS, Transformer
    with zipfile.ZipFile(path) as archive:
        names=archive.namelist()
        candidates=[n for n in names if n.lower().endswith(".geojson")]
        if candidates:
            if len(candidates)!=1:raise ValueError("Expected exactly one GeoJSON file")
            data=json.loads(archive.read(candidates[0]))
            crs=data.get("crs")
            if crs and "4326" not in json.dumps(crs):raise ValueError("GeoJSON must be EPSG:4326")
            return data["features"]
        shp=[n for n in names if n.lower().endswith(".shp")]
        if len(shp)!=1:raise ValueError("Expected one .shp or one .geojson")
        stem=shp[0][:-4]
        def get(ext):
            name=next((n for n in names if n.lower()==(stem+ext).lower()),None)
            if not name:raise ValueError("Missing shapefile component: "+ext)
            return archive.read(name)
        import io
        reader=shapefile.Reader(shp=io.BytesIO(get(".shp")),shx=io.BytesIO(get(".shx")),dbf=io.BytesIO(get(".dbf")),encoding="cp949")
        crs=CRS.from_wkt(get(".prj").decode("utf-8-sig"))
        trans=Transformer.from_crs(crs,CRS.from_epsg(4326),always_xy=True)
        fields=[f[0] for f in reader.fields[1:]]
        result=[]
        for rec in reader.iterShapeRecords():
            geom=rec.shape.__geo_interface__
            def transform(coords):
                if isinstance(coords,(tuple,list)) and len(coords)>=2 and all(isinstance(v,(float,int)) for v in coords[:2]):
                    return list(trans.transform(coords[0],coords[1]))
                return [transform(x) for x in coords]
            geom["coordinates"]=transform(geom["coordinates"])
            result.append({"properties":dict(zip(fields,list(rec.record))),"geometry":geom})
        return result

def build_catalog(xlsx, geographic_zip):
    official=validate(xlsx)
    features=features_from_zip(geographic_zip)
    by_code={str(r["code"]).strip():r for r in official}
    by_name={r["name"]:r for r in official}
    matched={}
    for feature in features:
        props=feature.get("properties") or {}
        values=[str(x).strip() for x in props.values() if x is not None]
        hits={r["code"]:r for val in values for r in ([by_code[val]] if val in by_code else [by_name[val]] if val in by_name else [])}
        if len(hits)!=1:continue
        record=next(iter(hits.values()))
        code=record["code"]
        if code in matched:raise ValueError("Multiple geometries matched "+code)
        geom=feature.get("geometry") or {}
        if geom.get("type") not in ("Polygon","MultiPolygon"):
            raise ValueError("Unexpected shape for "+code)
        lng,lat=centroid_polygon(geom["coordinates"])
        if not (126.7<lng<127.3 and 37.3<lat<37.8):raise ValueError("Coordinate outside Seoul for "+code)
        matched[code]={"id":code,"name":record["name"],"query":code,"lat":round(lat,6),"lng":round(lng,6)}
    if len(matched)!=121:
        raise ValueError(f"Only {len(matched)}/121 regions matched; refusing partial publication")
    return [matched[r["code"]] for r in official]

def write_catalog(xlsx, geographic_zip, destination):
    places=build_catalog(xlsx,geographic_zip)
    Path(destination).parent.mkdir(parents=True,exist_ok=True)
    Path(destination).write_text(json.dumps(places,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return places

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("Usage: python -m scripts.import_official_places official.xlsx regions.zip")
    places=write_catalog(sys.argv[1],sys.argv[2],"data/official_places.json")
    print(f"Validated {len(places)} official places: data/official_places.json")
