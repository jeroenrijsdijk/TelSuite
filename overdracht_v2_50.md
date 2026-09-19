# Overdracht v2.50 — telrapport op het gedeelde Overpass-transport

Vervolg op v2.49, en daarmee is het laatste losse Overpass-verkeer in de suite
opgeruimd. Twee bestanden gewijzigd.

`telrapport.html` had drie fetch-plekken die alle drie dezelfde vraag stelden
(`way(id:…);out geom;`) maar elk hun eigen afhandeling hadden. Twee gingen
rechtstreeks naar de hoofdserver **zonder mirror-fallback**: viel die weg, dan
verdween de weggeometrie stilzwijgend uit de kaart. De derde had de
endpoint-lijst twee keer inline als array-literal staan, waarvan één keer alleen
om er `.length` van te nemen.

Nu is er één ingang, `haalWayGeometrie()`, bovenop het gedeelde transport.

---

## 1. Gewijzigde bestanden

| Bestand | Verschil | Wat |
|---|---|---|
| `telrapport.html` | +4.638 | OVP-blok, gedeeld `overpassFetch`, `haalWayGeometrie()`, drie plekken omgezet |
| `telreconstructie.html` | +165 | `overpassFetch` neutraal geformuleerd zodat het écht gedeeld is |

De overige dertien bestanden zijn byte-identiek aan v2.49.

---

## 2. `overpassFetch` is nu een gedeeld blok

Het stond al in `telreconstructie.html` en had daar de juiste vorm: transport
gescheiden van query en verwerking. De tekst verwees alleen nog naar de
reconstructor. Die is neutraal gemaakt en het blok staat nu byte-identiek in
twee bestanden (`grep overpassFetch`), md5 `0ac3b21d`. Geen gedragswijziging in
`telreconstructie.html` — alleen commentaar en de kopregel.

Daarmee ziet de stapel er zo uit:

| Laag | Waar | Bestanden |
|---|---|---|
| classificatie (`ovpKeur`) | gedeeld blok | 6 |
| transport (`overpassFetch`) | gedeeld blok | 2 (telrapport, telreconstructie) |
| fetch-discipline veld (`startRoadFetch`) | gedeeld blok | 3 parkeer-apps |
| fetch-discipline pocket (`snapStartFetch`) | eigen, wel zelfde model | 1 |
| query + verwerking | per tool | — |

Pocket houdt bewust zijn eigen ingang: zijn discipline is verweven met de
fid-volgordeguard, de trace-events en het onderscheid tussen een fatale en een
verversende mislukking. Dat hoort daar te blijven; het model eronder is wel
hetzelfde.

---

## 3. `haalWayGeometrie()`

```
haalWayGeometrie(wayIds, onOk, onFail)
  onOk(geomMap)    geomMap: wayId (string) -> [[lat,lon], ...]
  onFail(reden)    optioneel; wie ook bij mislukking iets moet tekenen geeft 'm mee
```

Drie dingen die de oude plekken niet deden:

- **Mirror-fallback op alle drie de plekken.** Was er op twee helemaal niet.
- **IDs worden ontdubbeld.** Eén van de drie deed dat, de andere twee niet. Bij
  een pocket-ZIP met veel segmenten op dezelfde way scheelt dat flink in de
  querylengte, en daarmee in het werk dat Overpass moet doen.
- **Lege lijst kost geen verzoek.** `onOk({})` en klaar.

De derde plek (capaciteitsgroepen) tekende bij mislukking de groepen alsnog
zonder geometrie; dat blijft zo via `onFail`. De eerste twee deden bij mislukking
niets, ook dat blijft zo.

---

## 4. Validatie

```
JS-syntax (node --check)                                  15/15 OK
HTML-tagbalans, vergeleken met v2.49                      geen afwijking
byte-identiteit                                           precies 2 bestanden gewijzigd
gedeelde blokken byte-identiek:
  HIGHWAY_RE          6 bestanden   5f8ce229
  OVP-blok            6 bestanden   43924522
  overpassFetch       2 bestanden   0ac3b21d
  leesTegels          4 bestanden   034ba82b
  fetch-discipline    3 bestanden   73890360
  cacheWaysInTiles    4 bestanden   098dfcc5
functionele test telrapport (node vm, nagebootste Overpass)   16/16 OK
functionele test parkeertelling                               34/34 OK
functionele test pocket_count                                 18/18 OK
```

Het endpoint-adres komt in `telrapport.html` nog precies één keer voor, in
`SNAP_OVERPASS`. Dat is met een assertie afgedwongen in de patch.

Nieuw in de rig: `_archief/overpass_rig/functest_telrapport.js`.

---

## 5. Wat dit níét oplost

`zoekTerreinen` in `capaciteitstelling.html` vuurt nog steeds één Overpass-
verzoek per kaartpan (600ms debounce, geen dedup, geen cache). Dat is een andere
querysoort (`amenity=parking`) en vraagt een eigen cache-afweging, dus het blijft
apart staan. Het is nu wel de laatste plek in de suite die zonder rem vraagt.

---

## 6. Backlog na deze release

**Klein / afgebakend**
- `zoekTerreinen` ontdubbelen op afstand tot het vorige zoekcentrum.
- Veiligheidsblok-kop in de handleiding: `<h1>` → `<h4>`.
- Engelse variant van `over.html`.

**Meetkunde (vraagt veldtest)**
- Fetch-radius en verversafstand losser zetten (nu 69% overlap per fetch).
- Gebied vooraf ophalen vanuit `telplanning.html`.

**Uitrollen als het bevalt**
- Audio-feedback en dekkingskaart naar de andere tel-modi.

**Groter / vraagt ontwerp**
- Parkeren uit pocket halen naar een eigen modus/tool.
- Plakkerigheid-kernel als winkelstraat-gegate punt-laag naar telrapport.
- %bezet per dag×uur-cel.
- QGIS-loader: optionele join op `_straten.csv` / `_bezocht.csv`.
