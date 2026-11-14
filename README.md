# TelSuite — browser-based traffic counting

Free, GPS-aware tools for traffic counting, parking surveys and pedestrian
counts in shopping streets, running entirely in the browser. Live at
**[telonline.org](https://telonline.org)**.

Every tool is a single HTML file: no framework, no build step, no account, no
installation. Fieldwork happens on a phone; processing and reporting on a
desktop. The interfaces are mostly in Dutch: the start page and the pocket
tool switch to English, and the fixed-point tool is in English. The technical
reference is in English.

## How it works

```
  telplanning ──assignment──▶ field app ──ZIP──▶ telreconstructie ──_recon.zip──▶ telrapport
  (before)                    (phone)            (optional, desktop)              (map + analysis)
       ▲                                                                                │
       └──────────────────────────────── coverage feedback ─────────────────────────────┘
```

Shopping-street counts also go to `passanten` (pedestrians per hour), and
`telarchief` keeps all your ZIPs on one map, checked and sorted.

Each counting session produces a ZIP with semicolon-delimited CSV files.
Reconstruction is optional: it re-snaps the walked route onto the OSM road
network, determines walking direction and places parking observations on the
correct side of the street. The report tools read raw and reconstructed ZIPs
alike. The ZIPs also load into QGIS or a KNIME pipeline, and the report exports
a GeoPackage with a ready-made QGIS project.

## The tools

A survey with telonline.org usually runs in four steps: you plan it at a desk,
count in the field with a phone, optionally straighten the result out, and look
at it on a map. Each step has its own tool, and each tool is one HTML file.

**Start**

- `index.html` — the start page: pick the tool that fits what you want to count, and see any count on this device that has not been saved yet.

**Before you go**

- `telplanning.html` — draw an area, choose the road types from OpenStreetMap and turn them into a counting assignment (sent as a link that opens the field app), or see which streets have already been counted.

**In the field (phone)**

- `traffic_counter.html` — stand at one spot by the road and count vehicles, cyclists and pedestrians per direction, with an hourly figure at the end.
- `pocket_count.html` — count while walking: everything that passes (simple), traffic per direction and vehicle type (transect), pedestrians in a shopping street, or taken and free parking spaces per side of the street (`pocket_count.html#parkeren`).
- `parkeertelling.html` — a full car-parking survey along a route: every space parked correctly, parked wrongly, empty or special, placed on the map on its side of the street.
- `fietsparkeren.html` — count parked bicycles along a route or at a rack, with mopeds, cargo bikes and wrecks kept apart.
- `capaciteitstelling.html` — map how many parking spaces there are, bay by bay along the street or per car park, as the base for later occupancy counts.

**Afterwards (desktop)**

- `telreconstructie.html` — optional: put each tap of a walked count on the right street and side of the road, with walking direction, without changing the totals.
- `telrapport.html` — drop in the ZIPs for a map of the counts per road segment, a day-by-hour week profile, a quality report per count and a GeoPackage export with a QGIS project. Built to stay quick with a few hundred counts and tens of thousands of road segments.
- `passanten.html` — pedestrians per hour in a shopping street, from walking counts: a map per weekday and hour with a margin, a week overview per street segment, and a day curve (an index per hour and day type, with weekday factors and margins) for all segments or the ones you pick. Exports the day curve and the underlying passages as CSV.
- `telarchief.html` — all your counts on one map and in one table: where and when, what is a duplicate, which walked counts still lack a reconstruction. It can also sort your ZIPs into folders by kind, with a log of what moved.

**Reading**

- `over.html` — what telonline.org is and who it is for (Dutch); `about.html` is the same introduction in English.
- `traffic_counter_help.html` — the manual for all tools (Dutch).
- `verantwoording.html` — for lawyers and advisers: what a count records, what happens to it afterwards, and its strengths and weaknesses next to a tally sheet (Dutch).
- `privacy.html` — which data is processed and where it goes (Dutch, with a summary in English).
- `zip_format_reference.html` — the ZIP and CSV format, column by column, for anyone who processes the files further (English).
- `snap_methodology.html` — how GPS points are matched to roads (English).
- `simulatieronde.html` — a simulated shopping-street count, down to each pedestrian: what the walking counter meets and taps, and what Passanten makes of it next to the truth. The calibration factor of Passanten comes from it (Dutch).

**Behind the scenes** (not linked from the site)

- `snaptrace.html` — a test bench that matches a raw GPS trace (GPX or CSV) to OpenStreetMap ways.
- `winkelstraat_rekenrig.html` — the prototype that became `passanten.html`: moving-observer counts in a shopping street turned into pedestrians per hour.

## Privacy

Count data never leaves the browser; it is only handed to you as a ZIP. The
one exception is a fingerprint (SHA-256) of a ZIP's name, for the counter on
the front page (see below). The tools do make requests to public services (map
tiles, OpenStreetMap Overpass, Nominatim, Open-Meteo), and those requests reveal
the area you are working in.

## Running it yourself

Put all files in one folder on any web server. The tools link to each other
relatively; field app and reconstruction tool must share an origin, because
the "reconstruct now" hand-off uses IndexedDB.

The only server-side part is `teller/index.php` (since v3.37), the counter on
the front page: a field app sends the SHA-256 of a ZIP's name when it is saved,
and the script keeps those fingerprints outside the web root (set `TELLER_MAP`
if the default, next to the web root, does not suit). Without PHP the tools work
as before and the front page leaves the line out. A planning from
`telplanning.html` travels to the field app as a link (since v3.15 nothing is
saved on the server).

External dependencies, loaded at runtime: Leaflet, JSZip, PapaParse,
Leaflet.draw and sql.js (for the GeoPackage) via CDN; map tiles from
OpenStreetMap, CARTO and PDOK; road network from Overpass; street names from
Nominatim; weather from Open-Meteo. The fonts are in `fonts/`, so no request
goes to a font service. The CARTO API key in the source is restricted to the
author's domain — use your own key when self-hosting. Please respect the
[Nominatim](https://operations.osmfoundation.org/policies/nominatim/) and
Overpass usage policies.

## Development

Developer notes are in Dutch: start with [`docs/ONTWIKKELEN.md`](docs/ONTWIKKELEN.md)
and [`docs/OVERDRACHT_STAND_VAN_ZAKEN.md`](docs/OVERDRACHT_STAND_VAN_ZAKEN.md).
Release notes per version live in `docs/overdracht/`.

The regression tests are in [`_archief/overpass_rig/`](_archief/overpass_rig/):
functional tests in Node (`functest_*.js`) and browser tests in Chromium with
Playwright (`*test.py`), with a README that lists them. GitHub Actions runs them
all on every pull request. A merge to `main` goes live: the release workflow
builds `telsuite-<version>.zip`, and its contents are published to
telonline.org.

## License

Copyright © 2026 Jeroen Rijsdijk

TelSuite is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version. See [`LICENSE`](LICENSE).
