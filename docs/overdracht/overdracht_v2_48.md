# TrafficCounterSuite v2.48 — Overdracht

**Verse-data-garantie voor Overpass.** Elk antwoord wordt nu op ouderdom gecontroleerd; een achterlopende mirror wordt automatisch overgeslagen. Acht bestanden gewijzigd t.o.v. v2.47.

## Waarom dit, en niet "meer mirrors"

Onderzocht bij de bron (OSM-wiki, lijst publieke instanties). Er zijn maar **drie** instanties met wereldwijde dekking én zonder betaalde sleutel:

| Instantie | Status |
|---|---|
| `overpass-api.de` (FOSSGIS) | primair — v0.7.62.11 |
| VK Maps (Rusland) | door Jay afgewezen |
| `overpass.private.coffee` | fallback — v0.7.62.11, geen rate limit |

Geofabrik, FairwayMapper, Tracestrack en Overspan vereisen allemaal een API-sleutel of betaling. "Zoveel mogelijk mirrors" is dus feitelijk **twee** — meer bestaan er niet in deze categorie.

Over de eerdere zorg: de wiki noemt private.coffee op exact dezelfde softwareversie als de hoofdinstantie (0.7.62.11 87bfad18), mét attic-data. Het forumbericht uit maart over een niet-bijgewerkte database lijkt achterhaald — maar "lijkt" is geen garantie, en dat is precies waarom de oplossing niet in de mirrorlijst zit.

## De oplossing: verifiëren in plaats van aannemen

Elk Overpass-antwoord draagt `osm3s.timestamp_osm_base` — het moment waarop die server zijn dataset voor het laatst bijwerkte. De suite keurt nu elk antwoord zelf:

```js
var OSM_MAX_LAG_DAGEN = 7;
function dataIsVers(data) { … lag <= OSM_MAX_LAG_DAGEN … }
```

Is de data ouder dan de drempel, dan wordt het antwoord als **mislukt** behandeld — waarmee de bestaande fallback-keten vanzelf de volgende endpoint probeert. Geen nieuwe retry-logica nodig.

**Fail-open bij twijfel:** ontbreekt de tijdstempel of is hij onleesbaar, dan wordt het antwoord geaccepteerd. Een parseerfout mag nooit het tellen blokkeren; alleen *aantoonbaar* verouderde data wordt geweigerd.

Dit onderhoudt zichzelf: raakt private.coffee ooit achter, dan merkt de app dat zelf en slaat hem over — zonder dat er een lijst bijgehouden hoeft te worden. Het beschermt bovendien tegen database-lag op de *hoofdserver*, wat nu net zo goed onopgemerkt zou blijven.

## Bereik

Helper + controle toegevoegd in alle acht bestanden die Overpass bevragen, op elke fetch-site (11 in totaal):

| Bestand | Controles |
|---|---|
| `parkeertelling`, `fietsparkeren`, `pocket_count`, `telreconstructie`, `telplanning`, `snaptrace` | 1 elk |
| `capaciteitstelling` | 2 (wegen + parkeerterreinen) |
| `telrapport` | 3 (alle way-geometrie-fetches) |

Drempel instelbaar via `OSM_MAX_LAG_DAGEN` (standaard 7).

## Validatie

- **`node --check`** + **HTML-tagbalans** schoon op alle acht.
- **Functietest (8 gevallen):** verse data (2 min), 1 dag, precies 7 dagen → geaccepteerd; 8 dagen en 6 maanden → geweigerd; ontbrekend `osm3s`-blok, onleesbare tijdstempel en `null` → geaccepteerd (fail-open). Alle correct.
- Geverifieerd: helper exact 1× per bestand, controle op elke fetch-site.
- **Byte-identiteit:** t.o.v. v2.47 wijzigden uitsluitend de acht genoemde bestanden.

## Aandachtspunt

De drempel van 7 dagen is ruim gekozen: de hoofdinstantie loopt normaal minuten achter, dus 7 dagen raakt alleen echt kapotte mirrors. Wil je strenger (bv. 1 dag), dan is dat één getal — maar houd er rekening mee dat een tijdelijke lag op de hoofdserver dan onnodig naar de fallback stuurt.

## Backlog (ongewijzigd)

- Overpass fallback-helper in `telrapport.html` (de twee losse `fetch()` zonder mirror-fallback — de vers-controle zit er nu wél op, de fallback nog niet).
- Dekkingskaart / audio breder uitrollen naar de andere tel-modi.
- Veiligheidsblok-kop `<h1>` → `<h4>` in de handleiding; parkeren-uit-pocket; plakkerigheid naar telrapport; %bezet dag×uur; QGIS-loader joins.
