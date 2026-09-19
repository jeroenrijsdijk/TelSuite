# TrafficCounterSuite v2.47 — Overdracht

Twee backlog-items afgehandeld: de Overpass-mirror omgezet en de QGIS-loader-link ingevuld. Tien bestanden gewijzigd t.o.v. v2.46.

## 1. Overpass-mirror: kumi.systems → private.coffee

`https://overpass.kumi.systems/api/interpreter` → `https://overpass.private.coffee/api/interpreter` op **10 plekken in 8 bestanden** (capaciteitstelling ×2, telrapport ×2, en fietsparkeren, parkeertelling, pocket_count, snaptrace, telplanning, telreconstructie elk ×1). Nul restanten van de oude naam.

Het pad `/api/interpreter` is identiek, dus de fallback-logica werkt ongewijzigd. De mirror blijft de **tweede** keuze; `overpass-api.de` blijft primair.

### ⚠ Bevinding om te weten

Bij het verifiëren van de URL kwam ik een melding tegen op het OSM-community-forum (maart 2026) dat private.coffee **werkt maar zijn database niet meer bijwerkt**. Dat is voor een fallback-mirror relevant: bij uitval van de hoofdserver zou je dan met verouderde OSM-data kunnen snappen — nieuwe of gewijzigde straten ontbreken dan.

Dit is niet geverifieerd voor de huidige situatie (de melding is een half jaar oud en kan achterhaald zijn). Drie opties, ter beoordeling:
- **Laten zoals nu** — een verouderde mirror is nog altijd beter dan geen fallback, en hij wordt alleen gebruikt als de hoofdserver faalt.
- **Een derde fallback toevoegen** — bv. `overpass.openstreetmap.fr` of `z.overpass-api.de`, zodat er een verse mirror in de keten zit.
- **Terug naar kumi** als die alsnog blijkt te werken (de naam is hernoemd, niet per se de dienst).

Zet op de backlog; geen actie nu.

## 2. QGIS-loader-link ingevuld

De `__volgt__`-placeholder in `over.html` is vervangen door de echte link: `https://telonline.org/telonline_qgis_loader.py` (https, conform de canonical van de site).

**Naamgeving gelijkgetrokken.** Het script staat op de server als `telonline_qgis_loader.py`, terwijl de handleiding en de outputs nog `recon_qgis_loader.py` heetten. De handleiding noemt nu de gepubliceerde naam **plus de downloadlink**, en het script is als `telonline_qgis_loader.py` opgeleverd (kopie van de laatste versie — met gecorrigeerde stippen en GPS-route — met bijgewerkte kopregel; `py_compile` schoon).

## Validatie

- **`node --check`** + **HTML-tagbalans** schoon op alle tien.
- Nul restanten: `kumi` (0), `__volgt__` (0).
- Loader-link aanwezig in zowel `over.html` als de handleiding.
- **Byte-identiteit:** t.o.v. v2.46 wijzigden uitsluitend de tien genoemde bestanden.

## Backlog (bijgewerkt)

- ~~Overpass-mirrornaam kumi → private.coffee~~ ✓ gedaan.
- ~~`over.html` `__volgt__`-placeholder~~ ✓ gedaan.
- **NIEUW:** private.coffee zou een niet-bijgewerkte database hebben — overwegen een verse derde fallback toe te voegen.
- Overpass fallback-helper in `telrapport.html` (twee losse `fetch()` zonder mirror-fallback).
- Dekkingskaart / audio breder uitrollen naar de andere tel-modi.
- Veiligheidsblok-kop `<h1>` → `<h4>` in de handleiding; parkeren-uit-pocket; plakkerigheid naar telrapport; %bezet dag×uur; QGIS-loader joins.
