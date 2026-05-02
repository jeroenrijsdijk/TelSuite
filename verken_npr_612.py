#!/usr/bin/env python3
"""
verken_npr_612.py — Verkent de NPR-data voor Spijkenisse en zet
beide ID-schema's naast elkaar zodat we kunnen zien welke gebieden
bij elkaar horen.

Gebruik:
    pip install requests
    python verken_npr_612.py

Geen andere dependencies nodig.
"""

import requests
import json
from datetime import datetime

BASE = "https://opendata.rdw.nl/resource"
AREA_MANAGER = 612

print(f"\nVerken NPR data voor AreaManagerId {AREA_MANAGER} (Spijkenisse)")
print("=" * 75)

# ----- Tabel 1: Geometrie (nsk3-v9n7) -----
print("\n[1] GEOMETRIE-tabel (nsk3-v9n7)")
print("-" * 75)
r = requests.get(f"{BASE}/nsk3-v9n7.json",
                 params={"$where": f"areamanagerid={AREA_MANAGER}", "$limit": 5000})
r.raise_for_status()
geom = r.json()
print(f"Aantal rijen: {len(geom)}")
print(f"Beschikbare kolommen: {sorted(geom[0].keys()) if geom else '(leeg)'}")

print(f"\nAlle areaids in geometrie-tabel:")
for i, rec in enumerate(geom, 1):
    aid = rec.get("areaid", "?")
    # Toon ook eventuele andere bruikbare velden
    extra = []
    for key in ["startdatedataareageometry", "enddatedataareageometry",
                "areadesc", "areacode"]:
        v = rec.get(key)
        if v:
            extra.append(f"{key}={v}")
    extra_s = " · ".join(extra) if extra else ""
    print(f"  {i:3d}. {aid:20s}  {extra_s}")

# ----- Tabel 2: Gebied (adw6-9hsg) -----
print("\n[2] GEBIED-tabel (adw6-9hsg)")
print("-" * 75)
r = requests.get(f"{BASE}/adw6-9hsg.json",
                 params={"$where": f"areamanagerid={AREA_MANAGER}", "$limit": 5000})
r.raise_for_status()
gebied = r.json()
print(f"Aantal rijen: {len(gebied)}")
print(f"Beschikbare kolommen: {sorted(gebied[0].keys()) if gebied else '(leeg)'}")

# Groepeer per areaid (kan meerdere rijen per gebied hebben)
per_aid = {}
for rec in gebied:
    aid = str(rec.get("areaid", "?"))
    per_aid.setdefault(aid, []).append(rec)

print(f"\nUnieke areaids in gebied-tabel: {len(per_aid)}")
print(f"\nAlle gebieden met details:")
for aid in sorted(per_aid.keys()):
    rows = per_aid[aid]
    # Combineer info uit alle rijen
    descs = set(r.get("areadesc", "") for r in rows if r.get("areadesc"))
    usages = set(r.get("usageid", "") for r in rows if r.get("usageid"))
    starts = set(r.get("startdatearea", "") for r in rows if r.get("startdatearea"))
    ends = set(r.get("enddatearea", "") for r in rows if r.get("enddatearea"))
    print(f"  {aid:10s}  desc={list(descs) or '-'}  "
          f"usage={list(usages) or '-'}  "
          f"start={list(starts) or '-'}  "
          f"eind={list(ends) or '-'}")

# ----- Tabel 3: Tijdvak — dataset-id is niet zeker, dus best-effort -----
print("\n[3] TIJDVAK-tabel (kandidaten zoeken)")
print("-" * 75)

# Zoek in de RDW catalogus naar tijdvak-datasets
try:
    r = requests.get(
        "https://opendata.rdw.nl/api/views/metadata/v1",
        params={"q": "tijdvak", "limit": 30},
        timeout=20,
    )
    if r.ok:
        catalog = r.json()
        print("Mogelijke tijdvak-datasets in de RDW catalogus:")
        for entry in catalog if isinstance(catalog, list) else []:
            name = entry.get("name", "")
            ds_id = entry.get("id", "")
            if "tijdvak" in name.lower() or "tijdvak" in ds_id.lower():
                print(f"  {ds_id}  ·  {name}")
except Exception as e:
    print(f"  Catalogus-zoekopdracht mislukt: {e}")

# Probeer een paar plausibele dataset-ids
TIJDVAK_CANDIDATES = ["xt5b-7m4q", "iiba-wtnq", "wbgg-9k2c"]
tijdvak = []
tijdvak_per_aid = {}
working_id = None

for ds_id in TIJDVAK_CANDIDATES:
    try:
        r = requests.get(
            f"{BASE}/{ds_id}.json",
            params={"$where": f"areamanagerid={AREA_MANAGER}", "$limit": 5000},
            timeout=20,
        )
        if r.ok:
            data = r.json()
            print(f"\n  ✓ {ds_id} bestaat — {len(data)} rijen voor 612")
            if data and not tijdvak:
                tijdvak = data
                working_id = ds_id
        else:
            print(f"  ✗ {ds_id} — HTTP {r.status_code}")
    except Exception as e:
        print(f"  ✗ {ds_id} — {e}")

if tijdvak:
    print(f"\nGevonden tijdvak-dataset: {working_id}")
    print(f"Aantal rijen: {len(tijdvak)}")
    print(f"Beschikbare kolommen: {sorted(tijdvak[0].keys())}")
    for rec in tijdvak:
        aid = str(rec.get("areaid", "?"))
        tijdvak_per_aid.setdefault(aid, []).append(rec)
    print(f"Unieke areaids in tijdvak-tabel: {len(tijdvak_per_aid)}")
    print(f"\nEerste 3 tijdvak-rijen volledig:")
    for rec in tijdvak[:3]:
        for k, v in rec.items():
            print(f"  {k}: {v}")
        print()
else:
    print("\nGeen werkende tijdvak-dataset gevonden — gebruik handmatige tijden in mapping.")

# ----- Naast elkaar: misschien matchen ze via areadesc of een andere kolom? -----
print("\n[4] NAAST ELKAAR — geometrie vs gebied")
print("-" * 75)
print(f"\nGeometrie-areaids ({len(geom)}):")
geom_aids = sorted(set(str(r.get("areaid", "?")) for r in geom))
for a in geom_aids:
    print(f"  {a}")

print(f"\nGebied-areaids ({len(per_aid)}):")
gebied_aids = sorted(per_aid.keys())
for a in gebied_aids:
    descs = set(r.get("areadesc", "") for r in per_aid[a] if r.get("areadesc"))
    usages = sorted(set(r.get("usageid", "") for r in per_aid[a] if r.get("usageid")))
    print(f"  {a}  →  {list(descs) or '(geen desc)'}  ·  usage={usages}")

print("\n[5] OVERLAP CHECK")
print("-" * 75)
overlap = set(geom_aids) & set(gebied_aids)
print(f"areaids die in BEIDE tabellen voorkomen: {len(overlap)}")
if overlap:
    for a in sorted(overlap):
        print(f"  {a}")

# Schrijf alles weg voor offline inspectie
print("\n[6] RAW DATA OPSLAAN")
print("-" * 75)
out = {
    "geometrie": [{k: v for k, v in r.items() if k != "areageometryastext"} for r in geom],  # WKT eruit voor leesbaarheid
    "gebied": gebied,
    "tijdvak": tijdvak,
    "fetched_at": datetime.now().isoformat(),
}
with open("npr_612_raw.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("Geschreven: npr_612_raw.json")

print("\nKlaar.")
