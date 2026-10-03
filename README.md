# TelSuite — browser-based traffic counting

Free, GPS-aware tools for traffic counting and parking surveys, running entirely
in the browser. Live at **[telonline.org](https://telonline.org)**.

Every tool is a single HTML file: no framework, no build step, no account, no
installation. Fieldwork happens on a phone; processing and reporting on a
desktop. The interfaces are in Dutch; the technical reference is in English.

# Let me know if you use it! 

## How it works

```
  telplanning ──assignment──▶ field app ──ZIP──▶ telreconstructie ──_recon.zip──▶ telrapport
  (before)                    (phone)            (optional, desktop)              (map + analysis)
       ▲                                                                                │
       └──────────────────────────────── coverage feedback ─────────────────────────────┘
```

Each counting session produces a ZIP with semicolon-delimited CSV files.
Reconstruction is optional: it re-snaps the walked route onto the OSM road
network, determines walking direction and places parking observations on the
correct side of the street. The report tool reads raw and reconstructed ZIPs
alike. The ZIPs also load into QGIS or a KNIME pipeline.

## Tools

**Field (phone)**

| File | Purpose |
|---|---|
| `traffic_counter.html` | count from a fixed point |
| `parkeertelling.html` | car parking, walking a route |
| `fietsparkeren.html` | bicycle parking, walking a route |
| `capaciteitstelling.html` | parking capacity per bay and per lot |
| `pocket_count.html` | phone-in-pocket counting: simple, transect, shopping street, parking |

**Desktop**

| File | Purpose |
|---|---|
| `telplanning.html` | plan a survey and assess coverage |
| `telreconstructie.html` | post-processing: re-snapping, direction, manual correction |
| `telrapport.html` | map visualisation and analysis |

**Documentation**: `traffic_counter_help.html` (manual, Dutch),
`zip_format_reference.html` (ZIP and CSV specification, English),
`snap_methodology.html` (how GPS points are matched to roads, English).

## Privacy

Count data never leaves the browser; it is only handed to you as a ZIP.
The tools do make requests to public services (map tiles, OpenStreetMap
Overpass, Nominatim, Open-Meteo), and those requests reveal the area you are
working in.

## Running it yourself

Put all files in one folder on any web server. The tools link to each other
relatively; field app and reconstruction tool must share an origin, because
the "reconstruct now" hand-off uses IndexedDB.

Saving plannings from `telplanning.html` needs PHP (5.6+) and a writable
`planningen/` folder. **These endpoints have no authentication** — protect the
folder on your server (for example with HTTP basic auth) if it is reachable
from the internet. Everything else works without a server-side component.

External dependencies, loaded at runtime: Leaflet, JSZip, PapaParse and
Leaflet.draw via CDN; map tiles from OpenStreetMap, CARTO and PDOK; road
network from Overpass; street names from Nominatim. The CARTO API key in the
source is restricted to the author's domain — use your own key when self-hosting.
Please respect the [Nominatim](https://operations.osmfoundation.org/policies/nominatim/)
and Overpass usage policies.

## Development

Developer notes are in Dutch: start with [`docs/ONTWIKKELEN.md`](docs/ONTWIKKELEN.md)
and [`docs/OVERDRACHT_STAND_VAN_ZAKEN.md`](docs/OVERDRACHT_STAND_VAN_ZAKEN.md).
Release notes per version live in `docs/overdracht/`.

## License

Copyright © 2026 Jeroen Rijsdijk

TelSuite is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version. See [`LICENSE`](LICENSE).
