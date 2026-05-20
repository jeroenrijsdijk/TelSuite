# Telapp suite v2.3 — Overdracht

Een release gewijd aan één conceptuele verschuiving in de pocket-app: **segmenten**. Tot v2.2 was `osm_way_id` de atomaire observatie-eenheid. Dat overstated de waarheid voor lange straten — als je een 350m residential alleen aan de eerste 80m hebt belopen, kreeg de hele way de status "bezocht" in de telplanning, en kreeg ze één uniforme heat-kleur in telrapport. Vanaf v2.3 is de eenheid `(osm_way_id, segment_index)`. Wegen worden opgeknipt in stukken van ongeveer 40 meter.

## Wat is er veranderd

### Datamodel
- **`_netwerk.csv`** is gedenormaliseerd: één rij per segment, met een eigen sub-LINESTRING. Nieuwe kolommen: `segment_index` (0-gebaseerd) en `segment_count` (per rij, voor zelfstandige interpretatie).
- **`_gps.csv`** en **`_telregels.csv`** krijgen elk een extra kolom `segment_index`. Deze wordt door de snap-engine ingevuld op basis van de exacte snap-positie langs de way.
- **`_bezocht.csv`** is volledig segment-gebaseerd. Eén visit per `(osm_way_id, segment_index)`. Kolommen: `sessie_id;datum;osm_way_id;segment_index;segment_count;straat;start_tijd;eind_tijd;duur_sec;n_gps;n_tellingen`.
- KNIME-koppelsleutel pocket: `(sessie_id, osm_way_id, segment_index)`. Twee aparte numerieke kolommen, geen samengestelde string — kuiser voor joins.

### Segmentatie-algoritme
Identiek in JavaScript (pocket_count.html) en Python (build_bezocht.py). Deterministisch, niet stochastisch:

```
totaal_lengte = lengte polyline in meters (Cartesische projectie)
if totaal_lengte < 60m:  → 1 segment (niet splitsen)
else:                    → N = round(totaal / 40); segLen = totaal / N
                         → parametrisch knippen langs cumulatieve afstand
```

Drempels (`SEGMENT_TARGET_M = 40`, `SEGMENT_MIN_M = 60`) staan als constanten bovenaan beide implementaties.

**Snap → segment_index toewijzing**: per OSM-edge slaat de snap-engine `cumStart` (cumulatieve meters tot het begin van de edge) en `edgeLen` op. Bij snap wordt de positie langs de way berekend als `cumStart + t·edgeLen` waarbij `t` ∈ [0,1] de Cartesische projectie-parameter is. Segment-index volgt uit `floor(snap_m / segLen)`. Deze aanpak werkt correct voor ways met willekeurig aantal OSM-knopen, inclusief 2-knoop residentials waar een midpoint-toewijzing zou falen.

### Scope
Alleen pocket en telrapport zijn aangepast:
- **In scope**: `pocket_count.html` (exporteert segment-aware), `build_bezocht.py` (upgradet oude ZIPs), `telrapport.html` (rendert per segment), docs.
- **Buiten scope**: telplanning blijft op way-niveau werken. Andere apps (parkeertelling, fietsparkeren, capaciteit, transect, traffic_counter) zijn ongewijzigd — voor hen is `segment_index` semantisch altijd 0.

## Per bestand

### pocket_count.html
- `SEGMENT_TARGET_M=40`, `SEGMENT_MIN_M=60` als constanten boven de SNAP-module.
- `snapBuildSegs(elements, refLat, refLon)` herschreven: per mini-edge opslaan we `cumStart`, `edgeLen`, `segLen`, `nSeg`. Geen edge-midpoint berekening meer.
- `snapNearestWay(lat, lon)` returnt nu ook `segIdx`, afgeleid uit de snap-positie via `t`.
- `routeLog.push` (in startGps en retro-snap callback) inclusief `segIdx`.
- `doTap` registreert `segIdx` in elke telregel.
- Helper `splitWayIntoSegments(geom)` + `_normPt(p)` voor [{lat,lon}]→[[lat,lon]] normalisatie.
- `buildNetwerkCsv` denormaliseert: één rij per segment met sub-LINESTRING en `segment_count`.
- `buildBezochtCsv` keyent visits op composite `wid + ':' + segIdx`. Zelfde drempels als v2.2: `MAX_GAP_SEC=30`, `MIN_VISIT_SEC=5`, `MIN_VISIT_PTS=3`.
- `_telregels.csv` header: `sessie_id;nr;tijdstip;type;lat;lon;osm_way_id;segment_index;straat`.
- `_gps.csv` header: `sessie_id;tijdstip;lat;lon;nauwkeurigheid;osm_way_id;segment_index;straat`.

### build_bezocht.py
In-place upgrade van v2.2 ZIPs naar v2.3-formaat. Overschrijft `_netwerk.csv`, `_gps.csv`, `_telregels.csv`, en voegt of vervangt `_bezocht.csv`.

CLI:
```
python build_bezocht.py FILE_OR_DIR [...]           # in-place (default)
python build_bezocht.py FILE_OR_DIR [...] --side    # los _bezocht.csv ernaast
python build_bezocht.py FILE_OR_DIR [...] --force   # forceer her-upgrade
```

Drempels: `SEGMENT_TARGET_M=40`, `SEGMENT_MIN_M=60`, `GPS_SNAP_M=15`, `TAP_SNAP_M=50`. Identiek aan v2.2 voor visit-detectie.

**Idempotentie**: detectie via `segment_index` in `_netwerk.csv` header. Tweede run op een v2.3-ZIP wordt overgeslagen tenzij `--force`.

**Tap-resnap beleid**: bestaande `osm_way_id` wordt geprefereerd (snap binnen die way's mini-segments met 50m radius). Bij geen match → globaal snappen binnen 50m. WayId mag veranderen door betere snap.

**rewrite_zip(path, replacements, additions, deletions)**: schrijft een tmp-ZIP via `ZIP_DEFLATED` en doet daarna een atomaire `shutil.move`. Bestaande items in `replacements`/`additions`/`deletions` worden overgeslagen bij het kopiëren van de bron.

### telrapport.html
Composite-key refactor — `wayData` en `wayLayers` keyen op `"wid:segIdx"` in plaats van alleen `wid`.

Helpers bovenaan de state-sectie:
```js
function wkey(wid, segIdx) { return wid + ':' + (segIdx || 0); }
function parseKey(k) {
  const i = k.lastIndexOf(':');
  return { wid: k.slice(0, i), segIdx: +k.slice(i+1) || 0 };
}
```

Loaders aangepast:
- **Pocket loader**: leest `segment_index` en `segment_count` uit `_netwerk.csv` en bouwt per segment een entry in `wayData` met eigen sub-geometrie. Telregels worden gekeyd op `wkey(wid, segIdx)`. Backward compat: v2.2 ZIPs zonder `segment_index` kolom → alles op segIdx=0, semantisch identiek aan v2.2.
- **Transect/fiets/auto/capaciteit loaders**: gebruiken `wkey(wid, 0)` overal. Geen segmenten, semantisch ongewijzigd.

Renderers aangepast:
- `wayHeat(key)`, `recolorOne(key)`: nemen composite key.
- `showWegvakDetail(key)`: toont `seg X/Y` in subtitel wanneer `segCount > 1`.
- `detectZeroVisited(gpsCSV, netKeys, countedSet)`: werkt op composite keys. Zero-visit "0"-badges worden per segment getoond op het segment-centroïd.
- `drawClusters(sid)`: cluster-grouping key wordt `${wkey(wid, segIdx)}|${zijde}` — clusters per segment dus.
- Bbox-check in timefilter, recolorAll, resetAll: itereren over `Object.keys(wayData)` werkt zonder semantische verandering — itereren over de juiste atomaire eenheid.

## Smoke-test resultaat (synthetisch)

Test-ZIP: 3 wegen (Korte Straat ~40m / Middel Laan ~120m / Lange Weg ~400m), 167 GPS-punten, 10 tellingen.

Na upgrade:
- 3 wegen → 14 segmenten (1 + 3 + 10).
- `_telregels.csv`: 10/10 telregels matchen op `(wayId, segIdx)` in netwerk.
- `_bezocht.csv`: 8 visits, met correcte segment-toewijzing per visit. Tellingen toegewezen aan het segment waar ze vielen ten tijde van de tap.
- Zero-visit detectie: 4 segmenten bezocht zonder tellingen (zichtbaar als dashed "0"-badge in telrapport).
- Idempotentie: tweede run skipt met "al v2.3".
- Telrapport-loader simulatie: alle 14 segmenten correct geladen, alle telregels koppelen, GPS heeft `segment_index` kolom.

## Edge cases & beslissingen

**1. 2-knoop ways**. Veel residential ways in OSM hebben alleen begin- en eindknoop. Eerste implementatie wees segIdx toe via edge-midpoint — dat faalde voor 2-knoop ways (één edge → één segIdx voor de hele way ongeacht snap-positie). Definitieve oplossing: segIdx afleiden uit snap-positie zelf via `cumStart + t·edgeLen`.

**2. Way-ids die door resnap veranderen**. Bij `build_bezocht.py` kan een tap-punt in een oude ZIP gesnapt zijn op een suboptimale way. We prefereren die `osm_way_id` (snap binnen die way's mini-segments), maar vallen terug op globaal snappen als geen match binnen 50m. Geaccepteerd: zeldzame way-id wisselingen door betere snap.

**3. Tap exact op segment-grens**. Een tap die precies op de grens tussen twee segmenten valt krijgt deterministisch de hogere segIdx (`floor` semantiek). Bij visit-detectie kan een tap op grens-tijdstip net in een ander visit-segment vallen dan zijn segIdx aangeeft — die tap wordt conservatief niet meegeteld. In smoke-test 1× geobserveerd, geaccepteerd.

**4. Pocket-ZIPs zonder `_netwerk.csv`**. Backwards compat met heel oude pocket-versies: als er geen netwerk is, blijft segmentatie niet werken (geen geometrie om te splitsen). Telrapport valt terug op Overpass-fetch op wayId-niveau en mapt alleen op segIdx=0. Visueel identiek aan v2.2.

**5. Visuele dichtheid**. Een lange straat krijgt nu meerdere cluster-badges (één per segment met tellingen) in plaats van één. Op echt lange wegen kunnen badges dicht op elkaar staan. Geaccepteerd als informatieve dichtheid; niet als bug.

## Constanten

| Constante | Waarde | Plaats |
|---|---|---|
| `SEGMENT_TARGET_M` | 40 m | pocket_count.html, build_bezocht.py |
| `SEGMENT_MIN_M` | 60 m | pocket_count.html, build_bezocht.py |
| `GPS_SNAP_M` | 15 m | build_bezocht.py |
| `TAP_SNAP_M` | 50 m | build_bezocht.py |
| `SNAP_MAX_M` | 50 m | pocket_count.html |
| `ROUTE_MIN_DIST` | 5 m | pocket_count.html |
| `MAX_GAP_SEC` | 30 s | beide |
| `MIN_VISIT_SEC` | 5 s | beide |
| `MIN_VISIT_PTS` | 3 pt | beide |
| `POCKET_SNAP_M` | 15 m | telrapport.html (zero-visit detectie) |
| `POCKET_MIN_HITS` | 3 | telrapport.html (zero-visit detectie) |

## Vervolgstappen (niet in v2.3)

- **Telplanning op segment-niveau**. Het hoofdwerk dat we expliciet hebben uitgesloten: telplanning telt nu segmenten als visits binnen de way, wat dekking nog steeds licht overstated. Bij v2.4 zou telplanning per segment moeten redeneren, met dezelfde `wkey`-helpers.
- **Adaptieve segmentlengte**. Voor hele lange highways (>1km tertiary) zou een groter `SEGMENT_TARGET_M` aangenamer kunnen zijn. Voor smalle binnenstraten kleiner. Voorlopig één globale waarde houden — eenvoud wint.
- **Segment-koppeling met capaciteit**. Capaciteitstellingen werken nog steeds per straat (parkeervakken op terrein/straat-niveau). Mogelijk in de toekomst een segment-aware capaciteitsbenadering, maar capaciteits-datamodel is fundamenteel anders dan pocket-flux dus dit vereist eigen ontwerp.

## Verifieerbaar via

- `python build_bezocht.py FILE_OR_DIR` op een v2.2 ZIP → ZIP wordt geüpgraded.
- Drop diezelfde ZIP in telrapport.html → wegvakken kleuren per segment.
- KNIME-join op `(sessie_id, osm_way_id, segment_index)` werkt direct op `_bezocht.csv` en `_netwerk.csv`.
- Tweede run van build_bezocht.py op dezelfde ZIP → skip met "al v2.3".
