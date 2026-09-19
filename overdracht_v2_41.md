# TrafficCounterSuite v2.41 — Overdracht

**Automatische ZIP-download na de stop-knop** in de drie parkeer-apps, zodat alle telmodi zich hetzelfde gedragen. Drie bestanden wijzigen t.o.v. v2.40; de rest byte-identiek.

## Diagnose (alle telmodi gecontroleerd, op verzoek)

| App / modus | Stop → download vóór v2.41 |
|---|---|
| pocket (simpel/transect/winkelstraat/parkeren) | **automatisch** ✓ (`stopTelling`) |
| traffic_counter (static) | **automatisch** ✓ ("downloading CSV…") |
| parkeertelling | handmatig — alleen knop aan ✗ |
| fietsparkeren | handmatig — alleen knop aan ✗ |
| capaciteitstelling | handmatig — alleen knop aan ✗ |

De drie parkeer-apps waren onderling consistent (alle drie geen auto-download); Jay merkte het bij fietsparkeren, maar het gold voor alle drie. `stopSession()` zette alleen de download-knoppen aan en toonde "download CSV en kaart hieronder".

## Fix

Aan het eind van het `entries>0`-blok in `stopSession()` wordt nu **`exportZip()`** aangeroepen — dezelfde, complete functie die de ZIP-knop al gebruikte (bouwt sessie/telregels/straten/gps/netwerk-CSV + GPX + kaart-PNG, en deelt/downloadt via `navigator.share` op iOS of een download-link op Android/desktop, precies zoals pocket en static). De statusmelding is aangepast naar "ZIP wordt gedownload… (of gebruik de knoppen hieronder)".

De handmatige download-knoppen blijven als terugval enabled; `exportZip()` ruimt bij succes de herstelkopie op (`clearSession()`), net als voorheen bij de knop.

Waarom dit veilig is: `exportZip()` guardt zelf op lege sessies, is idempotent qua opbouw, en werd al bewezen via de knop — ik roep 'm nu alleen automatisch aan vanuit dezelfde gebruikers-gesture (de stop-tik), wat gelijk of beter is voor de iOS-share-timing dan de tweede tik op de ZIP-knop.

## Validatie

- **`node --check`** + **HTML-tagbalans** schoon op alle drie.
- Geverifieerd: `exportZip()` staat binnen `stopSession()` in alle drie.
- **Byte-identiteit:** t.o.v. v2.40 wijzigden uitsluitend `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html`.

## Backlog (ongewijzigd)

- Dekkingskaart / audio breder uitrollen; eventueel zijde-offset op de kaartstippen.
- `parkeer_reconstructie.html` → `telreconstructie.html`; Overpass fallback-helper + mirrornaam; `over.html` `__volgt__`-link; veiligheidsblok-kop `<h1>`→`<h4>`; parkeren-uit-pocket; plakkerigheid naar telrapport; %bezet dag×uur; QGIS-loader joins.
