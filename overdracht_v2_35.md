# TrafficCounterSuite v2.35 — Overdracht

Vervolg op de rebrand: in de twee Engelstalige referentie-docs is de Nederlandse productnaam vervangen door het (taalneutrale) domein, op Jay's verzoek. Alleen `snap_methodology.html` en `zip_format_reference.html` wijzigen t.o.v. v2.34; de rest byte-identiek.

## Wijziging

`Telonline Verkeerstellingen` → `telonline.org` in:
- **snap_methodology.html** — title, subtitel, en de body-zin ("…matched to OSM road geometry in telonline.org." — het lidwoord "the" is daar geschrapt zodat de zin met een domein blijft lopen).
- **zip_format_reference.html** — title en subtitel.

De Nederlandstalige tool-pagina's (o.a. `telplanning`, de kop in de handleiding) en de JSON-LD/metadata op `index.html` houden de productnaam "Telonline Verkeerstellingen" — die keuze stond niet ter discussie.

## Bevestigd zonder wijziging

- **#3** — `over.html` toont al "Wat is telonline.org?" (kwam automatisch mee met de `rvmk.nl`→`telonline.org`-swap in v2.34). Geen actie nodig.
- **#5** — release-ZIP blijft `TrafficCounterSuite_vX.zip` (interne artefactnaam, niet in het product).
- **#1** (`telsuite_osm` interne cache-DB) en **#4** (capaciteitstelling `telonline-parkeertelling`-identifier) — niet aangekaart, blijven zoals in v2.34.

## Validatie

- **HTML-tagbalans** schoon op beide bestanden.
- **Merk-sweep:** geen "Telonline Verkeerstellingen" meer in de twee Engelse docs (0 treffers).
- **Byte-identiteit:** t.o.v. v2.34 wijzigden uitsluitend `snap_methodology.html` en `zip_format_reference.html`.

## Backlog (ongewijzigd, wacht op oppakken)

- **`parkeer_reconstructie.html` → `telreconstructie.html`** (bestand + alle verwijzingen).
- **Overpass fallback-helper** in `telrapport.html` (twee losse `fetch()` zonder mirror-fallback).
- **Overpass-mirrornaam** `overpass.kumi.systems` → `overpass.private.coffee` (8 bestanden).
- `over.html`: `__volgt__`-placeholder invullen met de echte QGIS-loader-link.
- Veiligheidsblok-kop `<h1>` → `<h4>` in de handleiding (optioneel).
- Parkeren uit pocket halen; plakkerigheid-kernel naar telrapport; %bezet dag×uur; QGIS-loader joins.
