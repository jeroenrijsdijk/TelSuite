#!/usr/bin/env python3
"""
verrijk_parkeervakken.py
========================

Verrijk een gemeentelijk parkeervakken-GeoJSON (in RD New / EPSG:28992)
met NPR-gebiedscodes en regime-info uit de RDW open data, specifiek voor
Spijkenisse (AreaManagerId 612).

Voor Spijkenisse geldt een ID-mismatch tussen de NPR-tabellen:
  - adw6-9hsg (gebied)     gebruikt synthetische numerieke IDs
  - nsk3-v9n7 (geometrie)  gebruikt 612_BBG, 612_CPG, etc.

Daarom is een handmatige mapping (mapping_612.json) nodig voor het
toekennen van regime + venstertijden aan elk gebied.

Voorbeeldgebruik:

    python verrijk_parkeervakken.py vakken.geojson

    python verrijk_parkeervakken.py vakken.geojson \\
        --output verrijkt.geojson \\
        --mapping mapping_612.json \\
        --area-manager 612

Dependencies:
    pip install shapely pyproj requests
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import requests
    from shapely.geometry import shape, Point, mapping
    from shapely.strtree import STRtree
    from shapely import wkt as shapely_wkt
    from pyproj import Transformer
except ImportError as e:
    sys.exit(
        f"Ontbrekende dependency: {e.name}.\n"
        "Installeer met:  pip install shapely pyproj requests"
    )


# ----------------------------------------------------------------------
# RDW open data endpoints
# ----------------------------------------------------------------------
RDW_BASE = "https://opendata.rdw.nl/resource"
DATASETS = {
    "geometrie": "nsk3-v9n7",   # areaid + areageometryastext (WKT) — vereist
    "gebied":    "adw6-9hsg",   # areaid + usageid + areadesc + dates — optioneel
    # Tijdvak: dataset-id niet definitief bekend. Voor Spijkenisse (612) bestaat
    # er momenteel geen werkende tijdvak-tabel; tijden komen daar uit mapping.json.
    # Voor andere gemeenten kan dit ID later aangepast worden als bekend.
    "tijdvak":   "kjbm-77vz",   # placeholder — optioneel, valt netjes terug bij 404
}

# Welke usage-codes zijn voor straatparkeren relevant
RELEVANT_USAGES = {"BETAALDP", "BETAALDPV", "VERGUNP", "VERGUNPV"}

# Mapping van usageid naar regime-categorie
USAGE_TO_REGIME = {
    "BETAALDP":  "betaald",
    "BETAALDPV": "betaald",
    "VERGUNP":   "vergunning",
    "VERGUNPV":  "vergunning",
}

# Dagnaam-mapping (NPR gebruikt 1=ma t/m 7=zo)
DAY_NAMES = {1: "ma", 2: "di", 3: "wo", 4: "do", 5: "vr", 6: "za", 7: "zo"}


# ----------------------------------------------------------------------
# RD New (EPSG:28992) → WGS84 (EPSG:4326) reprojection
# ----------------------------------------------------------------------
_rd_to_wgs = Transformer.from_crs("EPSG:28992", "EPSG:4326", always_xy=True)


def detect_crs(features: list[dict]) -> str:
    """Sniff the CRS by looking at a sample coordinate."""
    for f in features:
        geom = f.get("geometry") or {}
        coords = geom.get("coordinates")
        if not coords:
            continue
        # Drill down to first leaf coordinate
        c = coords
        while isinstance(c, list) and c and isinstance(c[0], list):
            c = c[0]
        if isinstance(c, list) and len(c) >= 2:
            x, y = c[0], c[1]
            if abs(x) <= 180 and abs(y) <= 90:
                return "wgs84"
            # RD New range: x ~0-300k, y ~300k-650k
            if -50000 < x < 350000 and 280000 < y < 700000:
                return "rd"
            return "unknown"
    return "unknown"


def reproject_geometry(geom: dict) -> dict:
    """Reproject a GeoJSON geometry from RD to WGS84 in-place-ish."""
    def tx(coords):
        if isinstance(coords[0], (int, float)):
            lon, lat = _rd_to_wgs.transform(coords[0], coords[1])
            return [lon, lat] + (list(coords[2:]) if len(coords) > 2 else [])
        return [tx(c) for c in coords]

    new_geom = dict(geom)
    new_geom["coordinates"] = tx(geom["coordinates"])
    return new_geom


# ----------------------------------------------------------------------
# RDW API fetcher
# ----------------------------------------------------------------------
def fetch_rdw(dataset_id: str, area_manager_id: int, limit: int = 50000,
              required: bool = True) -> list[dict]:
    """Query a Socrata endpoint for all rows matching the area manager id.

    If required=False, returns [] on any error instead of raising. Useful
    for optional datasets that may not exist for every area manager (e.g.
    Spijkenisse has no tijdvak-data because NPR was sunset in 2020).
    """
    url = f"{RDW_BASE}/{dataset_id}.json"
    params = {"$where": f"areamanagerid={area_manager_id}", "$limit": limit}
    print(f"  → GET {dataset_id} ...", end=" ", flush=True)
    try:
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        print(f"{len(data)} rijen")
        return data
    except requests.HTTPError as e:
        if required:
            raise
        status = e.response.status_code if e.response is not None else "?"
        print(f"HTTP {status} (overgeslagen, optioneel)")
        return []
    except (requests.RequestException, ValueError) as e:
        if required:
            raise
        print(f"fout (overgeslagen): {e}")
        return []


# ----------------------------------------------------------------------
# Tijdvak summarization
# ----------------------------------------------------------------------
def normalize_time(t: Any) -> str | None:
    """RDW timefrom/timeto can be HHMM int, '0900', '09:00:00.000' etc."""
    if t is None or t == "":
        return None
    s = str(t).strip()
    # Strip ISO timestamp wrappers like 'T09:00:00.000'
    m = re.search(r"(\d{2}):(\d{2})", s)
    if m:
        return f"{m.group(1)}:{m.group(2)}"
    # Plain HHMM (3 or 4 digits)
    s_digits = re.sub(r"\D", "", s)
    if len(s_digits) == 4:
        return f"{s_digits[:2]}:{s_digits[2:]}"
    if len(s_digits) == 3:
        return f"0{s_digits[0]}:{s_digits[1:]}"
    return s


def format_day_range(d_from: int, d_to: int) -> str:
    """1,5 → 'ma-vr', 6,7 → 'za-zo', 1,1 → 'ma'."""
    f, t = DAY_NAMES.get(d_from, "?"), DAY_NAMES.get(d_to, "?")
    return f if f == t else f"{f}-{t}"


def summarize_tijdvakken(rows: list[dict]) -> str:
    """Format a list of tijdvak-rows into a compact human-readable string."""
    parts = []
    seen = set()
    for r in rows:
        try:
            d_from = int(r.get("dayfrom") or r.get("dayfromnumber") or 0)
            d_to = int(r.get("dayto") or r.get("daytonumber") or d_from)
        except (TypeError, ValueError):
            continue
        if d_from < 1 or d_from > 7:
            continue
        t_from = normalize_time(r.get("timefrom") or r.get("starttime"))
        t_to = normalize_time(r.get("timeto") or r.get("endtime"))
        days = format_day_range(d_from, d_to)
        if t_from and t_to:
            entry = f"{days} {t_from}-{t_to}"
        else:
            entry = f"{days} (24u)"
        if entry not in seen:
            seen.add(entry)
            parts.append(entry)
    return "; ".join(parts)


def normalize_regime(value: str | None) -> str | None:
    """
    Map free-text regime values to a canonical category.
    Accepts informal forms like 'betaald + vergunning', 'betaald | vergunning',
    'betaald/vergunning', etc., and normalizes to 'mixed'.
    """
    if value is None:
        return None
    s = str(value).strip().lower()
    if not s:
        return None
    # Detect combined regime
    has_betaald = "betaald" in s
    has_vergun = "vergun" in s
    if has_betaald and has_vergun:
        return "mixed"
    if has_betaald:
        return "betaald"
    if has_vergun:
        return "vergunning"
    if "blauw" in s or s == "other":
        return "other"
    if s in ("mixed", "gemengd"):
        return "mixed"
    if s == "onbekend" or s == "unknown" or s == "?":
        return "onbekend"
    return s   # pass through whatever else is there


# ----------------------------------------------------------------------
# Build NPR features from RDW data + manual mapping
# ----------------------------------------------------------------------
def build_npr_features(
    geom_rows: list[dict],
    gebied_rows: list[dict],
    tijdvak_rows: list[dict],
    mapping: dict,
    area_manager_id: int,
) -> list[dict]:
    """
    Build a list of GeoJSON-like NPR area features in WGS84.
    Joins geometry to (manual mapping || adw6 attributes), and to tijdvakken.
    """
    # Build attribute map from adw6 (areaid → usageids/areadesc)
    adw_attrs: dict[str, dict] = {}
    for r in gebied_rows:
        aid = str(r.get("areaid", "")).strip()
        if not aid:
            continue
        slot = adw_attrs.setdefault(aid, {"usageids": set(), "areadesc": ""})
        if r.get("usageid"):
            slot["usageids"].add(str(r["usageid"]).strip())
        if r.get("areadesc") and not slot["areadesc"]:
            slot["areadesc"] = r["areadesc"]

    # Build tijdvak map keyed by (areaid, regime-bucket)
    # Note: same key as adw_attrs so we can find tijden by areaid + regime
    tijdvak_per_areaid_regime: dict[tuple[str, str], list[dict]] = {}
    for r in tijdvak_rows:
        aid = str(r.get("areaid", "")).strip()
        usage = str(r.get("usageid", "")).strip()
        regime = USAGE_TO_REGIME.get(usage)
        if not regime or not aid:
            continue
        tijdvak_per_areaid_regime.setdefault((aid, regime), []).append(r)

    features = []
    skipped_no_wkt = 0
    skipped_bad_wkt = 0

    for rec in geom_rows:
        wkt_str = rec.get("areageometryastext")
        if not wkt_str:
            skipped_no_wkt += 1
            continue

        aid = str(rec.get("areaid", "")).strip()
        try:
            geom = shapely_wkt.loads(wkt_str)
        except Exception as e:
            print(f"    ! WKT parse fout voor {aid}: {e}")
            skipped_bad_wkt += 1
            continue

        # Resolve regime: manual > adw6 > unknown
        manual_entry = mapping.get(aid, {}) if isinstance(mapping.get(aid), dict) else {}
        manual_regime = normalize_regime(manual_entry.get("regime"))
        manual_naam = manual_entry.get("naam") or ""
        manual_tijden_betaald = manual_entry.get("tijden_betaald") or ""
        manual_tijden_vergun = manual_entry.get("tijden_vergunning") or ""

        adw_match = adw_attrs.get(aid)

        if manual_regime and manual_regime != "onbekend":
            regime = manual_regime
            regime_source = "manual"
        elif adw_match and adw_match["usageids"]:
            usages = adw_match["usageids"]
            if any(u.startswith("BETAALD") for u in usages) and any(u.startswith("VERGUN") for u in usages):
                regime = "mixed"
            elif any(u.startswith("BETAALD") for u in usages):
                regime = "betaald"
            elif any(u.startswith("VERGUN") for u in usages):
                regime = "vergunning"
            else:
                regime = "other"
            regime_source = "adw6"
        else:
            regime = "onbekend"
            regime_source = "unknown"

        # Compose tijden — prefer manual if given, else derive from tijdvakken
        tijden_betaald = manual_tijden_betaald or summarize_tijdvakken(
            tijdvak_per_areaid_regime.get((aid, "betaald"), [])
        )
        tijden_vergun = manual_tijden_vergun or summarize_tijdvakken(
            tijdvak_per_areaid_regime.get((aid, "vergunning"), [])
        )

        areadesc = manual_naam or (adw_match["areadesc"] if adw_match else "")

        features.append({
            "areaid": aid,
            "areamanagerid": area_manager_id,
            "regime": regime,
            "regime_source": regime_source,
            "areadesc": areadesc,
            "tijden_betaald": tijden_betaald,
            "tijden_vergunning": tijden_vergun,
            "geometry": geom,   # shapely Geometry, in WGS84 (RDW already serves WGS84)
        })

    # Diagnostic: print ALL features to verify what's being built
    print(f"  Alle samengestelde NPR-features:")
    for f in features:
        print(f"    {f['areaid']:12s} regime={f['regime']!r:30s} bron={f['regime_source']:10s} naam={f['areadesc']!r}")

    if skipped_no_wkt or skipped_bad_wkt:
        print(f"  Geometrie overgeslagen: {skipped_no_wkt} zonder WKT, {skipped_bad_wkt} corrupt")

    return features


# ----------------------------------------------------------------------
# Spatial join: vakken (WGS84 centroids) against NPR areas
# ----------------------------------------------------------------------
def enrich_vakken(vakken_features: list[dict], npr_features: list[dict]) -> dict:
    """
    Add NPR enrichment fields to each vak in-place. Returns counters.
    Uses simple linear scan — N=16 polygons makes STRtree overhead useless.
    """
    if not npr_features:
        return {"matched": 0, "unmatched": len(vakken_features)}

    # CRS sanity: NPR geometries should be in WGS84 (lon roughly 3-7, lat 50-54).
    # If we see RD-like coords (x in tens of thousands), reproject the NPR
    # polygons to WGS84 so they match the (already-WGS84) vakken.
    sample_geom = npr_features[0]["geometry"]
    sample_x, sample_y = list(sample_geom.exterior.coords)[0][:2] if hasattr(sample_geom, "exterior") else (None, None)
    if sample_x is None:
        # MultiPolygon — drill in
        try:
            sample_x, sample_y = list(sample_geom.geoms)[0].exterior.coords[0][:2]
        except Exception:
            sample_x, sample_y = 0, 0

    if abs(sample_x) > 180 or abs(sample_y) > 90:
        print(f"  NPR geometrieën zijn niet in WGS84 (sample: {sample_x:.1f}, {sample_y:.1f}) — reprojecteren...")
        from shapely.ops import transform
        rd_to_wgs_xy = lambda x, y, z=None: _rd_to_wgs.transform(x, y) if z is None else (*_rd_to_wgs.transform(x, y), z)
        for f in npr_features:
            f["geometry"] = transform(rd_to_wgs_xy, f["geometry"])
        # Re-sample after reprojection
        new_sample = list(npr_features[0]["geometry"].exterior.coords)[0][:2] if hasattr(npr_features[0]["geometry"], "exterior") else "?"
        print(f"  Na reprojectie sample: {new_sample}")

    # Pre-compute bboxes for cheap exclusion
    bboxes = [g["geometry"].bounds for g in npr_features]   # (minx, miny, maxx, maxy)
    geoms = [g["geometry"] for g in npr_features]

    matched = 0
    unmatched = 0
    for vak in vakken_features:
        gj = vak.get("geometry")
        if not gj or not gj.get("coordinates"):
            unmatched += 1
            _set_empty_npr(vak)
            continue
        try:
            shp = shape(gj)
            cen = shp.centroid
        except Exception:
            unmatched += 1
            _set_empty_npr(vak)
            continue

        cx, cy = cen.x, cen.y
        chosen = None
        for i, bb in enumerate(bboxes):
            if cx < bb[0] or cx > bb[2] or cy < bb[1] or cy > bb[3]:
                continue
            if geoms[i].contains(cen):
                chosen = npr_features[i]
                break

        if chosen:
            matched += 1
            _set_npr(vak, chosen)
        else:
            unmatched += 1
            _set_empty_npr(vak)

    return {"matched": matched, "unmatched": unmatched}


def _set_npr(vak: dict, area: dict) -> None:
    p = vak.setdefault("properties", {})
    p["npr_areaid"] = area["areaid"]
    p["npr_areamanagerid"] = area["areamanagerid"]
    p["npr_regime"] = area["regime"]
    p["npr_regime_source"] = area["regime_source"]
    p["npr_areadesc"] = area["areadesc"]
    p["npr_tijden_betaald"] = area["tijden_betaald"]
    p["npr_tijden_vergunning"] = area["tijden_vergunning"]


def _set_empty_npr(vak: dict) -> None:
    p = vak.setdefault("properties", {})
    p["npr_areaid"] = None
    p["npr_areamanagerid"] = None
    p["npr_regime"] = None
    p["npr_regime_source"] = None
    p["npr_areadesc"] = None
    p["npr_tijden_betaald"] = None
    p["npr_tijden_vergunning"] = None


# ----------------------------------------------------------------------
# I/O
# ----------------------------------------------------------------------
def load_vakken(path: Path) -> dict:
    print(f"Vakken laden: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if data.get("type") != "FeatureCollection":
        sys.exit(f"FOUT: {path} is geen GeoJSON FeatureCollection")
    print(f"  {len(data['features'])} features")
    return data


def reproject_vakken_to_wgs84(data: dict) -> int:
    """Detect CRS and reproject if needed. Returns count of reprojected features."""
    crs = detect_crs(data["features"])
    print(f"Detected CRS: {crs}")
    if crs != "rd":
        return 0
    print("  Reprojecting RD → WGS84 ...")
    n = 0
    for feat in data["features"]:
        if feat.get("geometry"):
            feat["geometry"] = reproject_geometry(feat["geometry"])
            n += 1
    # Strip a CRS marker if present
    data.pop("crs", None)
    return n


def load_mapping(path: Path | None) -> dict:
    if path is None or not path.exists():
        if path:
            print(f"Geen mapping-bestand gevonden op {path}, doorgaan zonder.")
        return {}
    print(f"Mapping laden: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # Strip metadata-keys (those starting with underscore)
    cleaned = {k: v for k, v in data.items() if not k.startswith("_")}
    print(f"  {len(cleaned)} gebieden gemapt")
    return cleaned


def write_geojson(data: dict, path: Path) -> None:
    print(f"GeoJSON schrijven: {path}")
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_csv(features: list[dict], path: Path) -> None:
    """Flatten features to CSV — only properties + lat/lon centroid."""
    print(f"CSV schrijven: {path}")
    if not features:
        print("  Geen features om te schrijven")
        return
    # Collect all property keys
    keys: list[str] = []
    seen_keys = set()
    for f in features:
        for k in (f.get("properties") or {}).keys():
            if k not in seen_keys:
                seen_keys.add(k)
                keys.append(k)
    extra_cols = ["centroid_lon", "centroid_lat"]
    with path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerow(keys + extra_cols)
        for f in features:
            props = f.get("properties") or {}
            row = [props.get(k, "") for k in keys]
            try:
                cen = shape(f["geometry"]).centroid
                row += [f"{cen.x:.7f}", f"{cen.y:.7f}"]
            except Exception:
                row += ["", ""]
            writer.writerow(row)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(
        description="Verrijk parkeervakken-GeoJSON met NPR-gebiedscodes en regime-info.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("vakken", type=Path, help="Pad naar parkeervakken-GeoJSON (in RD)")
    ap.add_argument("-o", "--output", type=Path, default=None,
                    help="Pad naar verrijkt GeoJSON (default: <vakken>_verrijkt.geojson)")
    ap.add_argument("--csv", type=Path, default=None,
                    help="Pad naar CSV-output (default: naast GeoJSON)")
    ap.add_argument("-m", "--mapping", type=Path, default=Path("mapping_612.json"),
                    help="Handmatige mapping JSON (default: mapping_612.json)")
    ap.add_argument("-a", "--area-manager", type=int, default=612,
                    help="AreaManagerId in NPR (default: 612 = Spijkenisse)")
    ap.add_argument("--no-csv", action="store_true",
                    help="Sla CSV-output over")
    args = ap.parse_args()

    if not args.vakken.exists():
        sys.exit(f"FOUT: {args.vakken} bestaat niet")

    # Default outputs
    output_path = args.output or args.vakken.with_name(args.vakken.stem + "_verrijkt.geojson")
    csv_path = args.csv or output_path.with_suffix(".csv")

    # Load + reproject vakken
    vakken_data = load_vakken(args.vakken)
    n_reproj = reproject_vakken_to_wgs84(vakken_data)
    if n_reproj:
        print(f"  {n_reproj} features gereprojecteerd")

    # Load manual mapping
    mapping = load_mapping(args.mapping)

    # Fetch NPR data
    print(f"\nNPR data ophalen voor AreaManagerId {args.area_manager} ...")
    geom_rows = fetch_rdw(DATASETS["geometrie"], args.area_manager, required=True)
    gebied_rows = fetch_rdw(DATASETS["gebied"], args.area_manager, required=False)
    tijdvak_rows = fetch_rdw(DATASETS["tijdvak"], args.area_manager, required=False)

    if not geom_rows:
        sys.exit(f"FOUT: geen geometrie-data gevonden voor AreaManagerId {args.area_manager}")

    if not gebied_rows:
        print("  (geen gebied-data — regimes komen volledig uit mapping)")
    if not tijdvak_rows:
        print("  (geen tijdvak-data — tijden komen volledig uit mapping)")

    # Build NPR features
    print("\nNPR-gebieden samenstellen ...")
    npr_features = build_npr_features(
        geom_rows, gebied_rows, tijdvak_rows, mapping, args.area_manager
    )
    print(f"  {len(npr_features)} gebieden")
    sources = {}
    for f in npr_features:
        sources[f["regime_source"]] = sources.get(f["regime_source"], 0) + 1
    print(f"  Bronnen: {sources}")

    # Spatial enrichment
    print("\nVakken verrijken via spatial join ...")
    counters = enrich_vakken(vakken_data["features"], npr_features)
    print(f"  Gekoppeld: {counters['matched']}")
    print(f"  Buiten alle gebieden: {counters['unmatched']}")

    # Per-area match counter
    per_area: dict[str, int] = {}
    for v in vakken_data["features"]:
        aid = (v.get("properties") or {}).get("npr_areaid")
        if aid:
            per_area[aid] = per_area.get(aid, 0) + 1
    if per_area:
        print(f"  Vakken per NPR-gebied:")
        for aid, n in sorted(per_area.items(), key=lambda x: -x[1]):
            # Find the regime for this area
            area = next((f for f in npr_features if f["areaid"] == aid), None)
            r = area["regime"] if area else "?"
            print(f"    {aid:12s} {n:5d} vakken  regime={r!r}")

    # Diagnostiek bij 0 hits — toon coordinate ranges van beide kanten
    if counters["matched"] == 0 and counters["unmatched"] > 0:
        print("\n  ⚠ DIAGNOSTIEK — geen enkele match, mogelijke oorzaken:")
        # Vakken bbox
        try:
            from shapely.geometry import shape as _sh
            v_bounds = None
            for v in vakken_data["features"][:1000]:
                if v.get("geometry"):
                    bb = _sh(v["geometry"]).bounds
                    if v_bounds is None:
                        v_bounds = list(bb)
                    else:
                        v_bounds[0] = min(v_bounds[0], bb[0])
                        v_bounds[1] = min(v_bounds[1], bb[1])
                        v_bounds[2] = max(v_bounds[2], bb[2])
                        v_bounds[3] = max(v_bounds[3], bb[3])
            if v_bounds:
                print(f"    Vakken-bbox (sample 1000): {v_bounds}")
        except Exception as e:
            print(f"    Kon vakken-bbox niet bepalen: {e}")
        # NPR bbox
        if npr_features:
            n_bounds = list(npr_features[0]["geometry"].bounds)
            for f in npr_features[1:]:
                bb = f["geometry"].bounds
                n_bounds[0] = min(n_bounds[0], bb[0])
                n_bounds[1] = min(n_bounds[1], bb[1])
                n_bounds[2] = max(n_bounds[2], bb[2])
                n_bounds[3] = max(n_bounds[3], bb[3])
            print(f"    NPR-bbox: {n_bounds}")
        print("    Als de bboxes geheel niet overlappen, klopt er iets niet met CRS of data.")

    # Regime-distribution among matched vakken
    regime_counts: dict[str, int] = {}
    for v in vakken_data["features"]:
        r = (v.get("properties") or {}).get("npr_regime")
        if r:
            regime_counts[r] = regime_counts.get(r, 0) + 1
    if regime_counts:
        print(f"  Regime-verdeling: {regime_counts}")

    # Write outputs
    print()
    write_geojson(vakken_data, output_path)
    if not args.no_csv:
        write_csv(vakken_data["features"], csv_path)

    print("\nKlaar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
