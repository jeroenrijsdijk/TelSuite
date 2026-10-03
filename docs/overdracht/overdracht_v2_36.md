# TrafficCounterSuite v2.36 — Overdracht

De live-snap van de veld-apps ziet nu dezelfde OSM-topologie als de reconstructor: **gebouwdoorgangen (`tunnel=building_passage`) worden voortaan óók opgehaald**. Vijf bestanden gewijzigd t.o.v. v2.35; de rest byte-identiek. De reconstructor (bron van waarheid) is ongewijzigd.

## Aanleiding

De highway-typelijst (`HIGHWAY_RE`, 16 typen) was al byte-identiek in alle zes de OSM-fetchende apps, maar alléén `parkeer_reconstructie.html` haalde daarnaast `building_passage` op. Gevolg: een tik ín een overdekte doorgang/winkelpassage snapte tijdens het veldwerk naar de dichtstbijzijnde ándere way (de confidence-stip kon alsnog groen zijn), en werd pas bij reconstructie rechtgezet. Nu sluit de live-snap aan op de reconstructor.

## Gewijzigde bestanden (5)

| Bestand | Query-vorm | Output |
|---|---|---|
| `parkeertelling.html` | `around:` | `out tags geom` |
| `fietsparkeren.html` | `around:` | `out tags geom` |
| `capaciteitstelling.html` | `around:` | `out tags geom` |
| `pocket_count.html` | `around:` | `out body geom` |
| `snaptrace.html` | `bbox` | `out body geom` |

Elke fetch is nu een **union** `(way[highway~RE]["area"!="yes"](…); way["tunnel"="building_passage"](…);)`, met de passage-clausule in exact dezelfde ruimtelijke vorm die de app al gebruikte (`around:` of `bbox`), en met elk z'n eigen output-clausule behouden. `snaptrace` kreeg een `bb`-variabele zodat de bbox-coördinaten niet dubbel in de string staan.

## Waarom dit veilig is (geverifieerd)

- **Geen verwerkings-wijziging nodig.** Alle vijf apps normaliseren een ontbrekende highway-tag al naar `''` (`(el.tags&&el.tags.highway)||''`), dus een tag-loze doorgang geeft geen `undefined`-crash.
- **Niet uitgesloten door de weging.** `snapWeight('')` = 2.5 (een afstands-multiplier, geen 0/∞) — een doorgang wordt behandeld als elke andere "minor" way (steps/track/corridor krijgen óók 2.5): een geldige kandidaat, gedeprioriteerd t.o.v. rijwegen. Omdat je ín de doorgang loopt, is 'ie doorgaans toch de dichtstbijzijnde.
- Dit is exact het patroon dat de reconstructor al bewezen draait (zelfde union, alleen `around:` i.p.v. `bbox`).

## Validatie

- **`node --check`** schoon op alle vijf; **HTML-tagbalans** schoon.
- **Query-render:** beide vormen (around: en bbox) produceren geldige Overpass-QL-unions met gebalanceerde haakjes.
- **Byte-identiteit:** exact 5 bestanden gewijzigd t.o.v. v2.35; `parkeer_reconstructie.html` byte-identiek (ongemoeid).

## Kanttekening

De extra clausule kost een fractie meer Overpass-belasting per fetch (één way-statement erbij over hetzelfde gebied). Verwaarloosbaar; de meeste doorgangen met een highway-tag (footway/corridor) werden al opgehaald — de winst zit in de doorgangen zónder passende highway-tag.

## Backlog (ongewijzigd)

- **`parkeer_reconstructie.html` → `telreconstructie.html`** (bestand + verwijzingen).
- **Overpass fallback-helper** in `telrapport.html` (twee losse `fetch()` zonder mirror-fallback).
- **Overpass-mirrornaam** `overpass.kumi.systems` → `overpass.private.coffee` (8 bestanden).
- `over.html`: `__volgt__`-placeholder invullen met de QGIS-loader-link.
- Veiligheidsblok-kop `<h1>` → `<h4>` in de handleiding (optioneel).
- Parkeren uit pocket halen; plakkerigheid-kernel naar telrapport; %bezet dag×uur; QGIS-loader joins.
