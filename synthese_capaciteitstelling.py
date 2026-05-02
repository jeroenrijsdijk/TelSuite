#!/usr/bin/env python3
"""
synthese_capaciteitstelling.py
==============================

Zet een gemeentelijk parkeervakken-GeoJSON (Spijkenisse / AreaManagerId 612)
om in een ZIP-bestand in het formaat dat capaciteitstelling.html zou exporteren,
zodat het direct in telrapport.html geladen kan worden.

Verschil met de fysieke veldwerk-app: wij genereren de "tellingen" synthetisch
op basis van de gemeentelijke vakkengegevens, en doen de OSM-snapping en
NPR-verrijking offline in plaats van ter plekke met GPS.

Output is een ZIP met de zes bestanden die telrapport verwacht:
  <sid>_sessie.csv      — één rij metadata
  <sid>_telregels.csv   — per vak één rij
  <sid>_capaciteit.csv  — per terrein/straat een aggregaat
  <sid>_netwerk.csv     — alle aangeraakte OSM-ways als WKT
  <sid>_gps.csv         — synthetisch (één centroïde van de bbox)
  <sid>.gpx             — leeg track-bestand

Gebruik:
    pip install shapely pyproj requests
    python synthese_capaciteitstelling.py vakken.geojson

Met opties:
    python synthese_capaciteitstelling.py vakken.geojson \\
        --mapping mapping_612.json \\
        --area-manager 612 \\
        --teller "RVMK" \\
        --output spijkenisse.zip
"""

import argparse
import csv
import io
import json
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path

try:
    import requests
    from shapely.geometry import shape, Polygon, MultiPolygon, LineString, Point, MultiLineString
    from shapely.ops import nearest_points, transform as shp_transform
    from shapely import wkt as shapely_wkt
    from pyproj import Transformer
except ImportError as e:
    sys.exit(
        f"Ontbrekende dependency: {e.name}.\n"
        "Installeer met:  pip install shapely pyproj requests"
    )


# ----------------------------------------------------------------------
# Doelgroep → capaciteitstelling-type mapping
# ----------------------------------------------------------------------
DOELGROEP_TO_TYPE = {
    # gehandicapt
    "invalide vak algemeen gebruik": "gehandicapt",
    "invalide vak op kenteken":      "gehandicapt",
    # laadpaal
    "elektrisch opladen":            "laadpaal",
    "optie tbv elektrisch opladen":  "laadpaal",
    # regulier (gewone parkeervakken)
    "parkeervak":                       "regulier",
    "parkeren niet nader ingedeeld":    "regulier",
    # gereserveerd (alle bijzondere bestemmingen)
    "arts":                          "gereserveerd",
    "camperplaats":                  "gereserveerd",
    "kiss + ride":                   "gereserveerd",
    "laden en lossen":               "gereserveerd",
    "lijnbussen":                    "gereserveerd",
    "opstel minicontainers":         "gereserveerd",
    "prive parkeervak":              "gereserveerd",
    "taxi standplaats":              "gereserveerd",
    "tbv hulpdiensten":              "gereserveerd",
}

# Default voor onbekende waardes
DEFAULT_TYPE = "regulier"


# ----------------------------------------------------------------------
# RDW open data endpoints
# ----------------------------------------------------------------------
RDW_BASE = "https://opendata.rdw.nl/resource"
NPR_DATASET = "nsk3-v9n7"

# ----------------------------------------------------------------------
# Overpass API endpoints (probeer beide)
# ----------------------------------------------------------------------
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

# ----------------------------------------------------------------------
# RD New (EPSG:28992) → WGS84 (EPSG:4326)
# ----------------------------------------------------------------------
_rd_to_wgs = Transformer.from_crs("EPSG:28992", "EPSG:4326", always_xy=True)


def detect_crs(features):
    """Sniff CRS from a sample coordinate."""
    for f in features:
        geom = f.get("geometry") or {}
        coords = geom.get("coordinates")
        if not coords:
            continue
        c = coords
        while isinstance(c, list) and c and isinstance(c[0], list):
            c = c[0]
        if isinstance(c, list) and len(c) >= 2:
            x, y = c[0], c[1]
            if abs(x) <= 180 and abs(y) <= 90:
                return "wgs84"
            if -50000 < x < 350000 and 280000 < y < 700000:
                return "rd"
            return "unknown"
    return "unknown"


def reproject_geojson_to_wgs84(features):
    def tx(coords):
        if isinstance(coords[0], (int, float)):
            lon, lat = _rd_to_wgs.transform(coords[0], coords[1])
            return [lon, lat] + (list(coords[2:]) if len(coords) > 2 else [])
        return [tx(c) for c in coords]
    n = 0
    for f in features:
        if f.get("geometry") and f["geometry"].get("coordinates"):
            f["geometry"]["coordinates"] = tx(f["geometry"]["coordinates"])
            n += 1
    return n


# Globale sanity-bbox voor Nederland — vangt 0,0 en andere uitschieters
NL_BBOX = (3.0, 50.5, 7.5, 53.7)   # (minlon, minlat, maxlon, maxlat)


def is_in_nl(lon, lat):
    """Quick sanity check: is this coordinate plausibly in the Netherlands?"""
    return NL_BBOX[0] <= lon <= NL_BBOX[2] and NL_BBOX[1] <= lat <= NL_BBOX[3]


# ----------------------------------------------------------------------
# Doelgroep mapping
# ----------------------------------------------------------------------
def map_doelgroep(value):
    if value is None:
        return DEFAULT_TYPE
    key = str(value).strip().lower()
    return DOELGROEP_TO_TYPE.get(key, DEFAULT_TYPE)


# ----------------------------------------------------------------------
# WKT parsing (for NPR polygons from RDW)
# ----------------------------------------------------------------------
def parse_wkt_safe(s):
    if not s:
        return None
    try:
        return shapely_wkt.loads(s)
    except Exception:
        return None


# ----------------------------------------------------------------------
# Overpass fetch — both amenity=parking polygons AND highway lines
# ----------------------------------------------------------------------
def fetch_overpass(bbox):
    """Fetch parking polygons and named highway lines for the bbox.

    Returns (parking_features, highway_features) as lists of dicts:
      parking: { 'osm_id': 'way/123', 'name': '...', 'geometry': shapely Polygon, 'tags': {...} }
      highway: { 'osm_id': 'way/456', 'name': '...', 'geometry': shapely LineString, 'highway': '...' }
    """
    s, w, n, e = bbox[1], bbox[0], bbox[3], bbox[2]
    ovp_bbox = f"{s:.6f},{w:.6f},{n:.6f},{e:.6f}"
    query = f"""[out:json][timeout:60];
(
  way["amenity"="parking"]({ovp_bbox});
  relation["amenity"="parking"]({ovp_bbox});
  way["highway"]["name"]({ovp_bbox});
);
out geom;
"""
    last_err = None
    for ep in OVERPASS_ENDPOINTS:
        try:
            print(f"  → Overpass {ep.split('//')[1].split('/')[0]} ...", end=" ", flush=True)
            t0 = time.time()
            r = requests.post(ep, data={"data": query}, timeout=120)
            r.raise_for_status()
            data = r.json()
            print(f"{len(data.get('elements', []))} elementen ({time.time()-t0:.1f}s)")
            return _parse_overpass_response(data)
        except Exception as e:
            print(f"fout: {e}")
            last_err = e
    raise RuntimeError(f"Beide Overpass-endpoints faalden — laatste: {last_err}")


def _parse_overpass_response(data):
    parking = []
    highway = []
    skipped_oob = 0
    for el in data.get("elements", []):
        tags = el.get("tags", {}) or {}
        if el.get("type") == "way":
            geom_pts = el.get("geometry", [])
            if not geom_pts or len(geom_pts) < 2:
                continue
            # Sanity check: all points within NL?
            if not all(is_in_nl(p["lon"], p["lat"]) for p in geom_pts):
                skipped_oob += 1
                continue
            coords = [(p["lon"], p["lat"]) for p in geom_pts]
            osm_id = f"way/{el['id']}"
            if tags.get("amenity") == "parking":
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
                if len(coords) >= 4:
                    try:
                        poly = Polygon(coords)
                        if poly.is_valid and not poly.is_empty:
                            parking.append({
                                "osm_id": osm_id,
                                "name": tags.get("name", ""),
                                "geometry": poly,
                                "tags": tags,
                            })
                    except Exception:
                        pass
            elif tags.get("highway") and tags.get("name"):
                try:
                    line = LineString(coords)
                    highway.append({
                        "osm_id": osm_id,
                        "name": tags.get("name", ""),
                        "geometry": line,
                        "highway": tags.get("highway"),
                    })
                except Exception:
                    pass
        elif el.get("type") == "relation":
            outers = []
            relation_oob = False
            for member in el.get("members", []):
                if member.get("role") == "outer" and member.get("geometry"):
                    pts = member["geometry"]
                    if len(pts) >= 3:
                        if not all(is_in_nl(p["lon"], p["lat"]) for p in pts):
                            relation_oob = True
                            break
                        rc = [(p["lon"], p["lat"]) for p in pts]
                        if rc[0] != rc[-1]:
                            rc.append(rc[0])
                        if len(rc) >= 4:
                            outers.append(rc)
            if relation_oob:
                skipped_oob += 1
                continue
            if outers:
                try:
                    polys = [Polygon(r) for r in outers]
                    polys = [p for p in polys if p.is_valid and not p.is_empty]
                    if len(polys) == 1:
                        geom = polys[0]
                    elif len(polys) > 1:
                        geom = MultiPolygon(polys)
                    else:
                        continue
                    parking.append({
                        "osm_id": f"relation/{el['id']}",
                        "name": tags.get("name", ""),
                        "geometry": geom,
                        "tags": tags,
                    })
                except Exception:
                    pass
    if skipped_oob:
        print(f"    ({skipped_oob} OSM-elementen met coördinaten buiten NL overgeslagen)")
    return parking, highway


# ----------------------------------------------------------------------
# RDW NPR fetch (geometry only — regime + name from mapping)
# ----------------------------------------------------------------------
def fetch_npr(area_manager_id):
    """Fetch the NPR area geometries for a given area-manager-id."""
    url = f"{RDW_BASE}/{NPR_DATASET}.json"
    params = {"$where": f"areamanagerid={area_manager_id}", "$limit": 5000}
    print(f"  → RDW {NPR_DATASET} ...", end=" ", flush=True)
    try:
        r = requests.get(url, params=params, timeout=60)
        r.raise_for_status()
        rows = r.json()
        print(f"{len(rows)} rijen")
        return rows
    except Exception as e:
        print(f"fout: {e}")
        return []


def build_npr_features(rows, mapping):
    """Combine NPR geometry rows with manual mapping → list of dicts."""
    features = []
    for rec in rows:
        wkt_str = rec.get("areageometryastext")
        aid = str(rec.get("areaid", "")).strip()
        if not wkt_str or not aid:
            continue
        geom = parse_wkt_safe(wkt_str)
        if not geom or geom.is_empty:
            continue
        m = mapping.get(aid, {}) if isinstance(mapping.get(aid), dict) else {}
        features.append({
            "areaid": aid,
            "regime": (m.get("regime") or "onbekend"),
            "naam": m.get("naam", ""),
            "tijden_betaald": m.get("tijden_betaald", ""),
            "tijden_vergunning": m.get("tijden_vergunning", ""),
            "geometry": geom,
        })
    return features


# ----------------------------------------------------------------------
# Spatial joins — vakken to parking polygons / highway lines / NPR
# ----------------------------------------------------------------------
def assign_terrein(vak_centroid, parking_features, parking_bboxes):
    """Return the parking feature whose polygon contains this centroid, smallest first."""
    cx, cy = vak_centroid.x, vak_centroid.y
    best = None
    best_area = float("inf")
    for i, bb in enumerate(parking_bboxes):
        if cx < bb[0] or cx > bb[2] or cy < bb[1] or cy > bb[3]:
            continue
        if parking_features[i]["geometry"].contains(vak_centroid):
            a = parking_features[i]["geometry"].area
            if a < best_area:
                best = parking_features[i]
                best_area = a
    return best


def assign_straat(vak_centroid, highway_features, highway_bboxes, max_dist_deg):
    """Return the nearest highway within max_dist (degrees), or None.
    Uses bbox pre-filter for speed."""
    cx, cy = vak_centroid.x, vak_centroid.y
    pad = max_dist_deg
    best = None
    best_dist = max_dist_deg
    for i, bb in enumerate(highway_bboxes):
        if cx < bb[0] - pad or cx > bb[2] + pad or cy < bb[1] - pad or cy > bb[3] + pad:
            continue
        d = highway_features[i]["geometry"].distance(vak_centroid)
        if d < best_dist:
            best = highway_features[i]
            best_dist = d
    return best


def assign_npr(vak_centroid, npr_features, npr_bboxes):
    cx, cy = vak_centroid.x, vak_centroid.y
    for i, bb in enumerate(npr_bboxes):
        if cx < bb[0] or cx > bb[2] or cy < bb[1] or cy > bb[3]:
            continue
        if npr_features[i]["geometry"].contains(vak_centroid):
            return npr_features[i]
    return None


# ----------------------------------------------------------------------
# CSV building
# ----------------------------------------------------------------------
def build_sessie_csv(sid, teller, datum_iso, start_t, end_t, n_waarn):
    out = io.StringIO()
    w = csv.writer(out, delimiter=";", lineterminator="\n")
    w.writerow(["sessie_id", "teller", "datum", "start_tijd", "eind_tijd", "app_type", "n_waarnemingen"])
    w.writerow([sid, teller, datum_iso, start_t, end_t, "capaciteit", n_waarn])
    return out.getvalue()


def build_telregels_csv(sid, vakken_processed):
    """One row per vak. We emulate a wandeling: nr=1..N, ts incrementing per second."""
    out = io.StringIO()
    w = csv.writer(out, delimiter=";", lineterminator="\n")
    w.writerow([
        "sessie_id", "nr", "tijdstip", "type", "zijde", "straat",
        "lat_marker", "lon_marker", "lat_gps", "lon_gps",
        "snapped", "osm_way_id",
        "hdg_kompas", "hdg_gps", "hdg_osm", "hdg_gebruikt",
    ])
    base = datetime.now()
    base_ts = base.replace(microsecond=0)
    for i, v in enumerate(vakken_processed, start=1):
        ts = base_ts.isoformat(timespec="seconds")
        # In de echte tool zit zijde links/rechts — wij weten dat niet, dus L+R neutraal als 'L'
        row = [
            sid, i, ts,
            v["type"], "L",
            v["straat_or_terrein_name"] or "",
            f"{v['lat']:.6f}", f"{v['lon']:.6f}",
            f"{v['lat']:.6f}", f"{v['lon']:.6f}",
            "1" if v["snapped"] else "0",
            v["osm_way_id"] or "",
            "", "", "", "",
        ]
        w.writerow(row)
    return out.getvalue()


def build_capaciteit_csv(sid, vakken_processed, ts_iso):
    """Aggregate per OSM way (terrain or street) per type — same format as
    capaciteitstelling.html's _capaciteit.csv.
    Header: sessie_id;osm_way_id;naam;zijde;soort;capaciteit;eerste_waarneming;laatste_waarneming
    """
    # group by (osm_way_id or '_onsnapped', name) → soort → count
    groups = {}
    notsnapped = {"regulier": 0, "gehandicapt": 0, "laadpaal": 0, "gereserveerd": 0}

    for v in vakken_processed:
        if not v["snapped"]:
            notsnapped[v["type"]] += 1
            continue
        key = (v["osm_way_id"], v["straat_or_terrein_name"] or "")
        if key not in groups:
            groups[key] = {"regulier": 0, "gehandicapt": 0, "laadpaal": 0, "gereserveerd": 0}
        groups[key][v["type"]] += 1

    out = io.StringIO()
    w = csv.writer(out, delimiter=";", lineterminator="\n")
    w.writerow([
        "sessie_id", "osm_way_id", "naam", "zijde", "soort", "capaciteit",
        "eerste_waarneming", "laatste_waarneming",
    ])
    for (way_id, naam), counts in sorted(groups.items()):
        for soort in ["regulier", "gehandicapt", "laadpaal", "gereserveerd"]:
            n = counts.get(soort, 0)
            if n > 0:
                w.writerow([sid, way_id, naam, "L+R", soort, n, ts_iso, ts_iso])
    # not-snapped fallback
    total_ns = sum(notsnapped.values())
    if total_ns > 0:
        for soort, n in notsnapped.items():
            if n > 0:
                w.writerow([sid, "", "(niet gesnapped)", "L+R", soort, n, ts_iso, ts_iso])
    return out.getvalue()


def build_netwerk_csv(parking_features, highway_features, used_osm_ids,
                      processed_vakken):
    """Build the netwerk.csv. Real parking polygons get their actual geometry,
    but for street-snapped vakken we synthesize a 'cluster polygon' from
    a buffered convex hull of the vakken themselves — telrapport's polyMap
    only accepts highway='parking' POLYGONs, so streets-as-LineStrings
    would land at the GPS-centroid fallback and stack into a tower.
    """
    out = io.StringIO()
    w = csv.writer(out, delimiter=";", lineterminator="\n")
    w.writerow(["osm_way_id", "highway", "geometrie_wkt"])

    def coords_str(coords):
        return ", ".join(f"{c[0]:.6f} {c[1]:.6f}" for c in coords)

    # Real terrain polygons from OSM
    terrain_ids = {f["osm_id"] for f in parking_features}
    for f in parking_features:
        if f["osm_id"] not in used_osm_ids:
            continue
        geom = f["geometry"]
        if isinstance(geom, Polygon):
            coords = list(geom.exterior.coords)
            w.writerow([f["osm_id"], "parking", "POLYGON ((" + coords_str(coords) + "))"])
        elif isinstance(geom, MultiPolygon):
            # Take the largest piece for the polygon-render
            biggest = max(geom.geoms, key=lambda p: p.area)
            coords = list(biggest.exterior.coords)
            w.writerow([f["osm_id"], "parking", "POLYGON ((" + coords_str(coords) + "))"])

    # For street-snapped vakken: synthesize cluster polygons per osm_way_id.
    # Group vakken by osm_way_id, compute convex hull + small buffer.
    street_groups = {}
    for v in processed_vakken:
        if not v["snapped"]:
            continue
        if v["osm_way_id"] in terrain_ids:
            continue   # Already handled
        wid = v["osm_way_id"]
        if not wid:
            continue
        street_groups.setdefault(wid, []).append((v["lon"], v["lat"]))

    # Buffer in degrees — about 8 meters at NL latitude
    buffer_deg = 0.00007
    for wid, points in street_groups.items():
        if len(points) < 2:
            # Single point — make a tiny square around it
            cx, cy = points[0]
            d = buffer_deg
            ring = [(cx-d, cy-d), (cx+d, cy-d), (cx+d, cy+d), (cx-d, cy+d), (cx-d, cy-d)]
            w.writerow([wid, "parking", "POLYGON ((" + coords_str(ring) + "))"])
            continue
        try:
            from shapely.geometry import MultiPoint
            mp = MultiPoint(points)
            hull = mp.convex_hull.buffer(buffer_deg)
            # buffer can return Polygon or MultiPolygon
            if isinstance(hull, Polygon):
                coords = list(hull.exterior.coords)
                w.writerow([wid, "parking", "POLYGON ((" + coords_str(coords) + "))"])
            elif isinstance(hull, MultiPolygon):
                biggest = max(hull.geoms, key=lambda p: p.area)
                coords = list(biggest.exterior.coords)
                w.writerow([wid, "parking", "POLYGON ((" + coords_str(coords) + "))"])
        except Exception as e:
            print(f"    ⚠ Cluster-polygoon faalde voor {wid}: {e}")

    return out.getvalue()


def build_verrijkt_csv(parking_features, highway_features, used_osm_ids,
                       processed_vakken, npr_features):
    """One row per OSM way (terrain or street-cluster) with the WKT, the
    counted capacities per type, and the NPR-info. Useful for downstream
    GIS / Excel analysis without having to parse telrapport's CSV layout.
    """
    out = io.StringIO()
    w = csv.writer(out, delimiter=";", lineterminator="\n")
    w.writerow([
        "osm_way_id", "naam", "bron",
        "aantal_totaal", "aantal_regulier", "aantal_gehandicapt",
        "aantal_laadpaal", "aantal_gereserveerd",
        "npr_areaid", "npr_regime",
        "geometrie_wkt",
    ])

    def coords_str(coords):
        return ", ".join(f"{c[0]:.6f} {c[1]:.6f}" for c in coords)

    def poly_to_wkt(geom):
        if isinstance(geom, Polygon):
            return "POLYGON ((" + coords_str(list(geom.exterior.coords)) + "))"
        if isinstance(geom, MultiPolygon):
            biggest = max(geom.geoms, key=lambda p: p.area)
            return "POLYGON ((" + coords_str(list(biggest.exterior.coords)) + "))"
        return ""

    # Group vakken by osm_way_id and collect per-type counts + NPR distribution
    groups = {}
    for v in processed_vakken:
        if not v["snapped"] or not v["osm_way_id"]:
            continue
        wid = v["osm_way_id"]
        g = groups.setdefault(wid, {
            "regulier": 0, "gehandicapt": 0, "laadpaal": 0, "gereserveerd": 0,
            "npr_areaids": {},   # areaid → count
            "npr_regimes": {},   # regime → count
        })
        g[v["type"]] += 1
        if v["npr_areaid"]:
            g["npr_areaids"][v["npr_areaid"]] = g["npr_areaids"].get(v["npr_areaid"], 0) + 1
        if v["npr_regime"]:
            g["npr_regimes"][v["npr_regime"]] = g["npr_regimes"].get(v["npr_regime"], 0) + 1

    # Build a lookup of OSM polygons by id for terrain WKT
    parking_by_id = {f["osm_id"]: f for f in parking_features}
    terrain_ids = set(parking_by_id.keys())

    # Synthesize cluster polygons for street-grouped vakken
    buffer_deg = 0.00007
    cluster_polys = {}
    for wid, g in groups.items():
        if wid in terrain_ids:
            continue
        points = [(v["lon"], v["lat"]) for v in processed_vakken
                  if v["snapped"] and v["osm_way_id"] == wid]
        if len(points) == 0:
            continue
        if len(points) == 1:
            cx, cy = points[0]
            d = buffer_deg
            ring = [(cx-d, cy-d), (cx+d, cy-d), (cx+d, cy+d), (cx-d, cy+d), (cx-d, cy-d)]
            cluster_polys[wid] = Polygon(ring)
        else:
            try:
                from shapely.geometry import MultiPoint
                mp = MultiPoint(points)
                cluster_polys[wid] = mp.convex_hull.buffer(buffer_deg)
            except Exception:
                pass

    # Highway lookup (for naming streets)
    highway_by_id = {f["osm_id"]: f for f in highway_features}

    for wid in sorted(groups.keys()):
        g = groups[wid]
        total = g["regulier"] + g["gehandicapt"] + g["laadpaal"] + g["gereserveerd"]

        if wid in terrain_ids:
            f = parking_by_id[wid]
            naam = f["name"] or "(geen naam)"
            bron = "OSM terrein"
            wkt_str = poly_to_wkt(f["geometry"])
        else:
            naam = highway_by_id[wid]["name"] if wid in highway_by_id else "(geen naam)"
            bron = "Straat-cluster"
            poly = cluster_polys.get(wid)
            wkt_str = poly_to_wkt(poly) if poly else ""

        # Pick majority NPR areaid (>50% of vakken in this group)
        npr_areaid = ""
        npr_regime = ""
        if g["npr_areaids"]:
            top_areaid, top_count = max(g["npr_areaids"].items(), key=lambda x: x[1])
            if top_count > total / 2:
                npr_areaid = top_areaid
            else:
                npr_areaid = "gemengd"
        if g["npr_regimes"]:
            top_regime, top_count = max(g["npr_regimes"].items(), key=lambda x: x[1])
            if top_count > total / 2:
                npr_regime = top_regime
            else:
                npr_regime = "gemengd"

        w.writerow([
            wid, naam, bron,
            total, g["regulier"], g["gehandicapt"], g["laadpaal"], g["gereserveerd"],
            npr_areaid, npr_regime,
            wkt_str,
        ])

    # Also include unsnapped fallback as a single row
    notsnapped = {"regulier": 0, "gehandicapt": 0, "laadpaal": 0, "gereserveerd": 0}
    for v in processed_vakken:
        if not v["snapped"]:
            notsnapped[v["type"]] += 1
    total_ns = sum(notsnapped.values())
    if total_ns > 0:
        w.writerow([
            "", "(niet gesnapped)", "Geen OSM-koppeling",
            total_ns, notsnapped["regulier"], notsnapped["gehandicapt"],
            notsnapped["laadpaal"], notsnapped["gereserveerd"],
            "", "",
            "",
        ])

    return out.getvalue()


def build_verrijkt_geojson(parking_features, highway_features, used_osm_ids,
                            processed_vakken):
    """Same content as build_verrijkt_csv, but as GeoJSON FeatureCollection.
    Convenient for direct loading into QGIS / kepler.gl without WKT-parsing.
    Returns a JSON-serialized string.
    """
    # Group vakken by osm_way_id
    groups = {}
    for v in processed_vakken:
        if not v["snapped"] or not v["osm_way_id"]:
            continue
        wid = v["osm_way_id"]
        g = groups.setdefault(wid, {
            "regulier": 0, "gehandicapt": 0, "laadpaal": 0, "gereserveerd": 0,
            "npr_areaids": {},
            "npr_regimes": {},
        })
        g[v["type"]] += 1
        if v["npr_areaid"]:
            g["npr_areaids"][v["npr_areaid"]] = g["npr_areaids"].get(v["npr_areaid"], 0) + 1
        if v["npr_regime"]:
            g["npr_regimes"][v["npr_regime"]] = g["npr_regimes"].get(v["npr_regime"], 0) + 1

    parking_by_id = {f["osm_id"]: f for f in parking_features}
    terrain_ids = set(parking_by_id.keys())
    highway_by_id = {f["osm_id"]: f for f in highway_features}

    # Synthesize cluster polygons for street groups
    buffer_deg = 0.00007
    cluster_polys = {}
    for wid, g in groups.items():
        if wid in terrain_ids:
            continue
        points = [(v["lon"], v["lat"]) for v in processed_vakken
                  if v["snapped"] and v["osm_way_id"] == wid]
        if not points:
            continue
        if len(points) == 1:
            cx, cy = points[0]
            d = buffer_deg
            ring = [(cx-d, cy-d), (cx+d, cy-d), (cx+d, cy+d), (cx-d, cy+d), (cx-d, cy-d)]
            cluster_polys[wid] = Polygon(ring)
        else:
            try:
                from shapely.geometry import MultiPoint
                mp = MultiPoint(points)
                cluster_polys[wid] = mp.convex_hull.buffer(buffer_deg)
            except Exception:
                pass

    def geom_to_geojson(geom):
        """Convert a shapely geometry to a GeoJSON-style dict."""
        if isinstance(geom, Polygon):
            return {
                "type": "Polygon",
                "coordinates": [[(round(x, 7), round(y, 7)) for x, y in geom.exterior.coords]],
            }
        if isinstance(geom, MultiPolygon):
            return {
                "type": "MultiPolygon",
                "coordinates": [
                    [[(round(x, 7), round(y, 7)) for x, y in p.exterior.coords]]
                    for p in geom.geoms
                ],
            }
        return None

    features = []
    for wid in sorted(groups.keys()):
        g = groups[wid]
        total = g["regulier"] + g["gehandicapt"] + g["laadpaal"] + g["gereserveerd"]

        if wid in terrain_ids:
            f = parking_by_id[wid]
            naam = f["name"] or "(geen naam)"
            bron = "OSM terrein"
            geom_obj = geom_to_geojson(f["geometry"])
        else:
            naam = highway_by_id[wid]["name"] if wid in highway_by_id else "(geen naam)"
            bron = "Straat-cluster"
            poly = cluster_polys.get(wid)
            geom_obj = geom_to_geojson(poly) if poly else None

        if geom_obj is None:
            continue

        npr_areaid = ""
        npr_regime = ""
        if g["npr_areaids"]:
            top_areaid, top_count = max(g["npr_areaids"].items(), key=lambda x: x[1])
            npr_areaid = top_areaid if top_count > total / 2 else "gemengd"
        if g["npr_regimes"]:
            top_regime, top_count = max(g["npr_regimes"].items(), key=lambda x: x[1])
            npr_regime = top_regime if top_count > total / 2 else "gemengd"

        features.append({
            "type": "Feature",
            "properties": {
                "osm_way_id": wid,
                "naam": naam,
                "bron": bron,
                "aantal_totaal": total,
                "aantal_regulier": g["regulier"],
                "aantal_gehandicapt": g["gehandicapt"],
                "aantal_laadpaal": g["laadpaal"],
                "aantal_gereserveerd": g["gereserveerd"],
                "npr_areaid": npr_areaid,
                "npr_regime": npr_regime,
            },
            "geometry": geom_obj,
        })

    fc = {"type": "FeatureCollection", "features": features}
    return json.dumps(fc, ensure_ascii=False, indent=2)


def build_gps_csv(sid, lat, lon, ts_iso):
    """Single synthetic GPS point — telrapport uses gps for fallback centroid."""
    out = io.StringIO()
    w = csv.writer(out, delimiter=";", lineterminator="\n")
    w.writerow([
        "sessie_id", "tijdstip", "lat", "lon", "nauwkeurigheid",
        "hdg_gps", "hdg_kompas", "hdg_fused", "gesnapped", "osm_way_id", "kompas_bevroren",
    ])
    w.writerow([sid, ts_iso, f"{lat:.6f}", f"{lon:.6f}", "10", "", "", "", "0", "", "0"])
    return out.getvalue()


def build_gpx(sid, lat, lon):
    """Empty-but-valid GPX file with one waypoint at the centroid."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<gpx version="1.1" creator="synthese_capaciteitstelling" '
        'xmlns="http://www.topografix.com/GPX/1/1">\n'
        f'  <wpt lat="{lat:.6f}" lon="{lon:.6f}"><name>{sid}</name></wpt>\n'
        '</gpx>\n'
    )


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description="Genereer een capaciteitstelling-ZIP uit een vakken-GeoJSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("vakken", type=Path, help="Pad naar vakken-GeoJSON")
    ap.add_argument("-o", "--output", type=Path, default=None, help="ZIP output-pad")
    ap.add_argument("-m", "--mapping", type=Path, default=Path("mapping_612.json"),
                    help="Handmatige NPR-mapping (default: mapping_612.json)")
    ap.add_argument("-a", "--area-manager", type=int, default=612,
                    help="AreaManagerId (default: 612 = Spijkenisse)")
    ap.add_argument("--teller", default="synthese RVMK",
                    help="Naam van de 'teller' in metadata")
    ap.add_argument("--snap-meters", type=float, default=15.0,
                    help="Maximale snap-afstand voor straat-toewijzing (default 15m)")
    args = ap.parse_args()

    if not args.vakken.exists():
        sys.exit(f"FOUT: {args.vakken} bestaat niet")

    # ===== 1. Load vakken =====
    print(f"Vakken laden: {args.vakken}")
    with args.vakken.open("r", encoding="utf-8") as f:
        vakken_data = json.load(f)
    if vakken_data.get("type") != "FeatureCollection":
        sys.exit("FOUT: input is geen GeoJSON FeatureCollection")
    vakken = vakken_data["features"]
    print(f"  {len(vakken)} features")

    # ===== 2. CRS check =====
    crs = detect_crs(vakken)
    print(f"  CRS: {crs}")
    if crs == "rd":
        n = reproject_geojson_to_wgs84(vakken)
        print(f"  Gereprojecteerd: {n} features RD → WGS84")

    # ===== 3. Doelgroep frequentietabel + type assignment =====
    print("\nDoelgroep-verdeling:")
    counts = {}
    unknowns = {}
    for v in vakken:
        dg = (v.get("properties") or {}).get("Doelgroep")
        key = (dg or "(leeg)")
        counts[key] = counts.get(key, 0) + 1
        if dg and str(dg).strip().lower() not in DOELGROEP_TO_TYPE:
            unknowns[dg] = unknowns.get(dg, 0) + 1
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        mapped = map_doelgroep(k if k != "(leeg)" else None)
        print(f"  {k!r:40s} → {mapped:13s} ({v})")
    if unknowns:
        print(f"\n  ⚠ Onbekende Doelgroep-waardes (worden '{DEFAULT_TYPE}'):")
        for k, v in unknowns.items():
            print(f"    {k!r}: {v}")

    # ===== 4. Compute centroids + bbox =====
    print("\nCentroïden en bbox bepalen ...")
    vak_centroids = []
    skipped_outside_nl = 0
    skipped_invalid = 0
    for v in vakken:
        try:
            shp = shape(v["geometry"])
            cen = shp.centroid
            if cen.is_empty or not cen.is_valid:
                skipped_invalid += 1
                continue
            if not is_in_nl(cen.x, cen.y):
                skipped_outside_nl += 1
                continue
            vak_centroids.append((v, cen))
        except Exception:
            skipped_invalid += 1
            continue
    if not vak_centroids:
        sys.exit("FOUT: geen geldige geometrieën in vakken")
    if skipped_invalid:
        print(f"  {skipped_invalid} vakken met ongeldige geometrie overgeslagen")
    if skipped_outside_nl:
        print(f"  {skipped_outside_nl} vakken buiten NL overgeslagen (vaak (0,0))")
    print(f"  {len(vak_centroids)} bruikbare centroïden")
    minx = min(c.x for _, c in vak_centroids)
    miny = min(c.y for _, c in vak_centroids)
    maxx = max(c.x for _, c in vak_centroids)
    maxy = max(c.y for _, c in vak_centroids)
    pad = 0.0015  # ~150m
    bbox = (minx - pad, miny - pad, maxx + pad, maxy + pad)
    print(f"  bbox: {bbox}")
    width_km = (maxx - minx) * 111 * 0.6   # rough at NL latitude
    height_km = (maxy - miny) * 111
    print(f"  bbox afmeting: ~{width_km:.1f} × {height_km:.1f} km")
    if width_km > 30 or height_km > 30:
        print(f"  ⚠ bbox is groot (>30km) — gemeente of uitschieters? Eerste centroïdes:")
        for v, c in vak_centroids[:5]:
            print(f"    {c.x:.5f}, {c.y:.5f}  OBJECTID={v.get('properties',{}).get('OBJECTID')}")

    # ===== 5. Load mapping =====
    mapping = {}
    if args.mapping.exists():
        print(f"\nMapping laden: {args.mapping}")
        with args.mapping.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        mapping = {k: v for k, v in raw.items() if not k.startswith("_")}
        print(f"  {len(mapping)} gebieden gemapt")
    else:
        print(f"\nGeen mapping-bestand gevonden op {args.mapping} — doorgaan zonder")

    # ===== 6. Fetch Overpass + NPR =====
    print("\nOSM data ophalen ...")
    parking_features, highway_features = fetch_overpass(bbox)
    print(f"  {len(parking_features)} parkeerterreinen, {len(highway_features)} straat-ways")

    print(f"\nNPR data ophalen voor AreaManagerId {args.area_manager} ...")
    npr_rows = fetch_npr(args.area_manager)
    npr_features = build_npr_features(npr_rows, mapping)
    print(f"  {len(npr_features)} NPR-gebieden samengesteld")

    # ===== 7. Pre-compute bboxes for spatial filter =====
    parking_bboxes = [f["geometry"].bounds for f in parking_features]
    highway_bboxes = [f["geometry"].bounds for f in highway_features]
    npr_bboxes = [f["geometry"].bounds for f in npr_features]
    snap_dist_deg = args.snap_meters / 111000.0  # rough degrees-per-meter

    # ===== 8. Process each vak: assign type, snap to terrain or street, NPR =====
    print("\nVakken verwerken (type + snap + NPR) ...")
    processed = []
    n_terrein = 0
    n_straat = 0
    n_orphan = 0
    npr_counts = {}
    for v, cen in vak_centroids:
        props = v.get("properties") or {}
        dg = props.get("Doelgroep")
        vak_type = map_doelgroep(dg)

        # Snap: terrain first, then street
        terrein = assign_terrein(cen, parking_features, parking_bboxes)
        straat = None
        if terrein is None:
            straat = assign_straat(cen, highway_features, highway_bboxes, snap_dist_deg)

        if terrein:
            osm_id = terrein["osm_id"]
            naam = terrein["name"]
            snapped = True
            n_terrein += 1
        elif straat:
            osm_id = straat["osm_id"]
            naam = straat["name"]
            snapped = True
            n_straat += 1
        else:
            osm_id = ""
            naam = ""
            snapped = False
            n_orphan += 1

        # NPR
        npr = assign_npr(cen, npr_features, npr_bboxes)
        npr_areaid = npr["areaid"] if npr else ""
        npr_regime = npr["regime"] if npr else ""
        if npr_regime:
            npr_counts[npr_regime] = npr_counts.get(npr_regime, 0) + 1

        processed.append({
            "type": vak_type,
            "osm_way_id": osm_id,
            "straat_or_terrein_name": naam,
            "snapped": snapped,
            "lat": cen.y,
            "lon": cen.x,
            "npr_areaid": npr_areaid,
            "npr_regime": npr_regime,
        })

    print(f"  Naar terrein: {n_terrein}")
    print(f"  Naar straat:  {n_straat}")
    print(f"  Niet snapped: {n_orphan}")
    if npr_counts:
        print(f"  NPR-verdeling: {npr_counts}")

    # ===== 9. Build CSVs + ZIP =====
    print("\nCSV-bestanden bouwen ...")
    now = datetime.now()
    sid = f"{now.strftime('%Y%m%d_%H%M%S')}"
    datum_iso = now.strftime("%Y-%m-%d")
    start_t = now.strftime("%H:%M:%S")
    end_t = now.strftime("%H:%M:%S")
    ts_iso = now.replace(microsecond=0).isoformat()

    sessie_csv = build_sessie_csv(sid, args.teller, datum_iso, start_t, end_t, len(processed))
    telregels_csv = build_telregels_csv(sid, processed)
    capaciteit_csv = build_capaciteit_csv(sid, processed, ts_iso)

    # Determine which OSM ways we actually used for netwerk.csv
    used_ids = {p["osm_way_id"] for p in processed if p["osm_way_id"]}
    netwerk_csv = build_netwerk_csv(parking_features, highway_features, used_ids, processed)
    verrijkt_csv = build_verrijkt_csv(parking_features, highway_features, used_ids,
                                       processed, npr_features)
    verrijkt_geojson = build_verrijkt_geojson(parking_features, highway_features,
                                               used_ids, processed)

    centroid_lat = (miny + maxy) / 2
    centroid_lon = (minx + maxx) / 2
    gps_csv = build_gps_csv(sid, centroid_lat, centroid_lon, ts_iso)
    gpx = build_gpx(sid, centroid_lat, centroid_lon)

    output = args.output or args.vakken.with_name(f"{args.vakken.stem}_telrapport.zip")
    print(f"\nZIP samenstellen: {output}")
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{sid}_sessie.csv", sessie_csv)
        zf.writestr(f"{sid}_telregels.csv", telregels_csv)
        zf.writestr(f"{sid}_capaciteit.csv", capaciteit_csv)
        zf.writestr(f"{sid}_netwerk.csv", netwerk_csv)
        zf.writestr(f"{sid}_gps.csv", gps_csv)
        zf.writestr(f"{sid}.gpx", gpx)
        zf.writestr(f"{sid}_verrijkt.csv", verrijkt_csv)
        zf.writestr(f"{sid}_verrijkt.geojson", verrijkt_geojson)

    print(f"\nKlaar. Sleep {output.name} naar telrapport.html.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
