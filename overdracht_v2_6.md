# TrafficCounterSuite v2.6 — Overdracht

Een release waarin het GPS-snap-algoritme van pocket_count fundamenteel is herzien (van stateless nearest-edge naar topologie-bewuste adjacency-snap met hysterese) en waarin telrapport een handmatige correctie-tool heeft gekregen voor verkeerd gesnapte auto-/fietsparkeertellingen. Ondersteunend: nieuwe technische documentatie, opgeschoonde voorpagina met SEO-pakket, debug-variant van pocket en kleine UX-fixes. Geen breaking changes; bestaande ZIP- en CSV-formaten blijven compatibel.

## Hoogtepunten

- **Adjacency-aware snap in pocket_count**. Topologie-bewuste GPS-snap: een fix wordt bij voorkeur op een wegvak gesnapt dat is verbonden met het wegvak waar de teller net was. Voorkomt het "Centrumpassage/Nieuwstraat-west"-probleem in dichte voetgangerszones.
- **Hysterese tegen anker-zwerving bij stilstand**. Het anker krijgt voorrang tot een buur substantieel dichterbij ligt (glijdende drempel: `max(5m, 30% × d_anchor)`).
- **Pre-reset op SNAP_MAX_M**. Anker buiten de snap-grens wordt direct als irrelevant beschouwd; ladder herijkt schoon.
- **Steps + corridor in Overpass-filter**. Trappen en interne corridors worden meegehaald zodat layer-overgangen (parkeerdak boven Centrumpassage, winkelcentrum-passages) correct in de adjacency-graaf verschijnen.
- **Correctie-tool in telrapport**. Sleep-modus voor auto/fiets sessies: verkeerd gesnapte waarnemingen handmatig naar de juiste way slepen, of zijde-flip. Export herbouwt `_telregels.csv` + `_straten.csv` in een `*_corrected.zip`.
- **pocket_debug.html**. Variant van pocket_count die per GPS-fix en per tap een `_snap_trace.csv` schrijft (anker, snap-pad, alternatieven, afstanden). Voor diagnostieke veldsessies.
- **Technische documentatie**. Nieuwe `snap_methodology.html` (Engelstalig); `zip_format_reference.html` volledig vertaald naar Engels en uitgebreid met stand-still; `traffic_counter_help.html` bijgewerkt voor stand-still pin, snap-koppeling en tech-doc-verwijzing.
- **Voorpagina opgeschoond + SEO**. Consistente kaart-stijlen (inline `<style>` blokken naar één hoofdstijl), keyword "online traffic counting" (niet "counter"), Open Graph + JSON-LD WebApplication-schema. Geen Twitter Card.

## Per bestand

### pocket_count.html

**Overpass-query verbreed**. `out tags geom` → `out body geom` (node-IDs erbij voor adjacency-detectie). Highway-filter uitgebreid met `steps|corridor` zodat trappen en interne passage-verbindingen mee worden ingeladen — kritisch voor correcte adjacency bij layer-overgangen (parkeerdak ↔ pedestrian) en voor winkelcentra.

**Adjacency-graaf**. Twee globals `snapNodeToWays` en `snapAdjacency` worden cumulatief bijgewerkt vanuit elke Overpass-fetch via nieuwe helper `snapRegisterWay(el)`. Idempotent: overlappende fetches voegen geen dubbele edges toe. Ways zijn buren als ze ten minste één OSM-node delen (op node-ID, niet op coördinaat-proximity — dat vangt T-kruisingen via interne nodes ook correct af).

**snapNearestWay() — vijf-staps decision ladder**:
1. **Bootstrap**: geen anker → globaal dichtstbijzijnde way binnen `SNAP_MAX_M`.
2. **Pre-reset**: anker bestaat maar ligt nu verder dan `SNAP_RESET_M` weg → anker breekt, bootstrap-pad opnieuw doorlopen.
3. **Depth-1 met hysterese**: kandidaten beperkt tot anker + directe buren. Het anker krijgt voorrang via een glijdende drempel — een buur wint pas als de afstand-tot-buur minstens `max(HYSTERESIS_M, d_anchor × HYSTERESIS_RATIO)` minder is dan de afstand-tot-anker, mits `d_anchor ≤ ANCHOR_PREFER_M`.
4. **Depth-2**: depth-1 leeg → ook buren-van-buren overwegen (voor hoge snelheid / gemiste tussen-fix).
5. **Glitch-hold**: geen verbonden kandidaat en anker nog binnen `SNAP_RESET_M` → `null` returnen, anker behouden.

**Constanten**:
- `SNAP_MAX_M = 50` — max snap-afstand
- `SNAP_RESET_M = 50` — gelijk aan SNAP_MAX_M, conceptueel: een anker buiten snap-bereik bestaat niet meer
- `ANCHOR_PREFER_M = 50` — boven deze afstand vervalt anker-voorkeur (= SNAP_MAX_M, voorkeur geldt over hele kandidatenbereik)
- `HYSTERESIS_M = 5` — minimum-meterdrempel voor anker-wissel
- `HYSTERESIS_RATIO = 0.3` — bovendien moet het verschil ≥30% van d_anchor zijn

**Tap-anker-erfenis**. Bij `null`-snap (glitch_hold) wordt het tap-event niet als wayId-loos opgeslagen maar erft het anker (`snapAnchorWayId` + `snapAnchorSegIdx` + cached `osmName`). Vermijdt data-gaten bij korte GPS-glitches (overdekte stukken, doorgangen).

**Pad-iteratie**. Vier rondes algoritmische verfijning in deze release, gedreven door veldtesten:
1. *Stateless nearest → adjacency-aware* (initiële fix voor Centrumpassage-bug)
2. *Anker-zwerving bij stilstaan* → eerst ratio-hysterese (0.7), daarna omgezet naar absolute-meter-drempel (5m) na door-rekening
3. *Anker-zwerving in OSM-armoede + verre-anker-bug* → glijdende drempel `max(5m, 30% × d_anchor)` + pre-reset op 100m
4. *Glitch-blok met verre kandidaten* → pre-reset omlaag naar 50m (= SNAP_MAX_M); ontbrekende `highway=steps` opgespoord en toegevoegd

**Niet aangeraakt**: tap-flow, GPS-handler, pending-queue, segmentering, `_netwerk.csv`-output, `_bezocht.csv`-output, `_telregels.csv`-schema. Sessies blijven byte-compatibel met v2.5-formaat.

### pocket_debug.html (nieuw)

Identieke kopie van pocket_count.html, met titel "Pocket Count — Debug" en één extra functionaliteit: per GPS-fix en per tap één regel in `<sessieID>_snap_trace.csv` (toegevoegd aan de gewone ZIP). Niet in het hoofdmenu van index.html — direct via URL benaderbaar.

**snap_trace.csv schema**:
| Kolom | Inhoud |
|---|---|
| sessie_id | sessie-ID |
| seq | volgnummer over alle events |
| tijdstip | ISO-timestamp |
| event | `gps` / `tap` / `tap_retro` |
| lat, lon | ruwe positie |
| accuracy | GPS-accuracy (leeg bij tap-zonder-fix) |
| anchor_before | wayId vóór dit event |
| snap_path | `bootstrap` / `d1` / `d1_hold` / `d2` / `reset` / `reset_no_candidate` / `glitch_hold` / `null_no_candidate` / `no_network` |
| chosen_way | gekozen wayId (leeg bij null) |
| d_anchor | afstand fix tot anker-way (m, 1 dec) |
| d_chosen | afstand fix tot gekozen way (m, 1 dec) |
| alternatives | top-3 alternatieven, format `wayId:afstand|...` |
| anchor_after | wayId ná dit event |
| tap_nr | volgnummer in `_telregels.csv` (alleen bij taps) |

**snapNearestWay() omslag**: signatuur kreeg optionele `eventInfo` parameter `{type, tijdstip, accuracy, tap_nr}`. Zonder `eventInfo` wordt niet getraced — zo blijft de functie aanroepbaar vanuit interne debug-paden waar tracing niet gewenst is. Drie aanroepers (GPS-handler, tap-handler, retro-snap voor pending-queue) zijn allemaal aangepast.

**Workflow**: tijdelijke app voor analyse. Voornemen is om `_snap_trace.csv`-uitvoer eventueel op te nemen in pocket_count zelf zodra het algoritme stabiel is — paar bytes per event, voor reguliere tellers onzichtbaar, voor jou (debugger) altijd beschikbaar bij twijfel achteraf.

### telrapport.html — correctie-tool (nieuw, +747 regels)

Handmatige sleep-modus voor auto- en fietsparkeer-sessies. Werkt op snapped waarnemingen (`r.snapped === '1'`). Gebruiker zet "sleep-modus" aan, krijgt sleepbare iconen op alle snapped tellingen, en kan een marker naar een andere way slepen (drag) of de zijde-flip oproepen (click).

**Drie nieuwe state-globals**:
- `originalFile[sid]` — File-blob van de oorspronkelijke ZIP (nodig voor binair-behoud bij export)
- `allTelregels[sid]` — alle parsed rows inclusief unsnapped (vs `telData[sid]` die alleen snapped filtert)
- `editMarkers[sid]` — sleepbare Leaflet-markers per sessie

**Drag-flow**: `handleDragEnd` zoekt via `findNearestWays(lat, lon, n=5, maxDistM=100)` de N dichtstbijzijnde kandidaat-ways. Als er één duidelijke winnaar is wordt die direct toegepast; bij meerdere geldige kandidaten verschijnt een popup waarin de gebruiker kiest (Leaflet-popup met hover-doorkijk).

**Click-flow**: zonder drag opent dezelfde popup met de kandidaat-set rond de huidige marker-positie. Drag versus click wordt onderscheiden via een `_wasDragged` vlag die `dragstart` zet en de click-handler controleert.

**applyCorrection()**: snap-coördinaten loodrecht op de way-as, plus 4m offset naar de gekozen zijde (visueel matched met de niet-gecorrigeerde markers die ook al uit de as worden geplaatst). Update vijf velden: `lat_marker`, `lon_marker`, `osm_way_id`, `straat`, `zijde`, `hdg_osm`, `hdg_gebruikt`, plus `manually_corrected = '1'`.

**applySideSwap()**: zonder van way te wisselen. Flip zijde, hdg_osm blijft (way-eigenschap), update positie 4m aan de andere kant van de way-as. Voor het geval de snap de way wel goed had maar de zijde-detectie niet.

**Geometrie-helpers**: `bearingDeg(lat1, lon1, lat2, lon2)`, `movePoint(lat, lon, bearing, distM)` (haversine forward), `snapAndSideOnWay(dragLat, dragLon, geometry, travelBearingDeg)` met way-frame ↔ travel-frame conversie. Travel-bearing geprefereerd uit `r.hdg_gps`, valt terug op `hdg_kompas` / `hdg_gebruikt` / `hdg_osm` (eerste niet-nul wint).

**Export — `exportOneCorrectedZip(sid)`**:
1. `JSZip.loadAsync` op de oorspronkelijke File-blob
2. Lees `_straten.csv` als tekst voor delta-aggregatie
3. Herbouw `_telregels.csv` via `buildTelregelsCsv(sid)`: bewaar onbekende kolommen (`extraCols`), plaats `manually_corrected` als laatste
4. Herbouw `_straten.csv` via `buildStratenCsv(sid, origStratenText)`: aggregeer correcte tellingen in bestaande naam→way-mapping; volledig nieuwe ways (niet in een bestaande rij) krijgen een nieuwe rij gegroepeerd op `straat`
5. Selectief overschrijven in de zip-tree: alleen `_telregels.csv` en `_straten.csv`; PNG, GPX, `_gps.csv`, `_netwerk.csv`, `_sessie.csv` blijven binair intact
6. Output: `<originele_naam>_corrected.zip`

**Stratenaggregatie-detail**: de `straat`-veldwaarden in `_telregels.csv` matchen niet altijd de canonieke OSM `name=*` tag in `_straten.csv` (voorbeeld: "Havenplein" in telregels vs "Westkade" in straten voor way 131138996). Daarom wordt geaggregeerd door telregels-counts op te tellen ín bestaande straten-rijen (delta op het wayId-niveau), waarmee de oorspronkelijke naam→way mapping behouden blijft.

**Reset-flow**: alle drie nieuwe state-globals worden in de bestaande reset-code opgeruimd, edit-modus wordt automatisch uitgezet als die nog aanstond.

### snap_methodology.html (nieuw)

Engelstalige technische documentatie van het adjacency-aware snap-algoritme. 9 secties, ~500 regels, eigen rvmk-stijl (gespiegeld op `zip_format_reference.html`).

**Secties**:
1. Het probleem (Centrumpassage/Nieuwstraat-west)
2. Het kernidee (topologische continuïteit, GPS gedemoteerd van ground-truth naar evidence)
3. De adjacency-graaf (Overpass-query, incrementele opbouw)
4. Het algoritme (5-stappen decision ladder, pseudocode)
5. Tunable parameters
6. Tap anchor inheritance
7. Limitaties (first-fix lock-in, OSM-completeness, areas, geen persistentie, build_bezocht.py)
8. Code locatie
9. Migratieplan naar andere apps

**Twee scope-banners bovenaan**:
- *Scope* (oranje): algoritme leeft op moment van schrijven alleen in pocket_count.html; andere apps volgen later
- *Note on bearing* (groen): bearing/zijde-logica in parkeertelling-apps is onafhankelijk van snap; bij migratie wordt bearing-code niet aangeraakt; risico is mostly theoretical maar wordt apart gedocumenteerd als veldtesten dat nodig maken

### zip_format_reference.html

**Volledige vertaling naar Engels** — alle uitlegteksten, file-descriptions, csv-notes, intro, sectie-titels. Bulk-fix voor herhaalde labels (Verplicht/Optioneel/Aanbevolen → Required/Optional/Recommended), per-sectie vertaling voor unieke teksten. CSV-veldnamen (`bezettingsgraad_pct`, `richting`, `bezet`, etc.) blijven Nederlands — dat zijn de werkelijke kolomheaders in de echte ZIPs.

**Stand-still als zesde sectie**. Volledig uitgewerkt: het is een losse CSV, géén ZIP. Drie secties in het bestand (metadata key-value, summary tabel, timestamp log). Welke metadata-velden Telrapport nodig heeft en welke optioneel zijn. Sectie-tag `stand-still` met groene kleur (matching index.html static-card), suffix-hint `*.csv (loose file, no ZIP)`.

**Overzichtstabel**: stand-still als eerste rij met colspan over alle ZIP-kolommen.

### traffic_counter_help.html

**Header-knoppen wrap-fix**: `flex-wrap: wrap` + `justify-content: flex-end` op `.back-links`. De acht back-links liepen op desktop van het scherm af.

**Inhoudelijke updates**:
- *Sectie 13* (`#park-types`): titel "Auto vs. Fietsparkeren" → "Twee parkeertel-apps (auto / fiets)". Korte intro die duidelijk maakt dat het twee aparte apps zijn, niet modi binnen één tool.
- *Sectie 25* (`#pocket-overzicht`): pocket snap-beschrijving bijgewerkt — verwijst naar topologie-bewuste snap i.p.v. "dichtstbijzijnde wegvak". Link naar `snap_methodology.html` toegevoegd.
- *Sectie 30* (Telrapport-kaartvisualisatie): stand-still als eerste rij in de telsoorten-tabel toegevoegd. Nieuwe card eronder beschrijft tijdreeks-popup, dag-filter pills en weekprofiel-knop (gelabeld "nieuw v2.5"). Card-rij maakte van vijf naar zes types.
- *Sectie 38* (Bestanden): `zip_format_reference.html` en `snap_methodology.html` samen onder eigen kopje "Technische documentatie", visueel gescheiden van de gebruikersapps. `build_bezocht.py` schuift mee onder dat kopje.

### index.html

**Card-consistentie**. Pocket- en capaciteit-kaart hadden inline `<style>` blokken binnen `<a>`-elementen. Verhuisd naar de hoofdstijl als `.pocket-card` en `.capacity-card` klassen, conform de andere vier kaarten. Geen inline-styles meer op mode-cards.

**Brand-blok**. De kale `<h3>RVMK.NL</h3>` is vervangen door `.title-block .brand` (eigen typografie, mixed-case `rvmk.nl`).

**Tekst-fixes**:
- EN `pocketTitle` "Move and Count Most Simple" → "Move and Count Simple" (consistent met HTML-fallback en NL-positie)
- NL `sub` van full-uppercase naar mixed case ("Kies je verkeerstelling"); CSS doet de uppercase

**SEO-pakket**:
- Title: "Online Traffic Counting — Vehicle & Parking Surveys | rvmk.nl"
- Meta description (~155 tekens)
- Canonical: `https://rvmk.nl/`
- Open Graph (type, title, description, url, locale en_US + nl_NL alternate, site_name)
- JSON-LD WebApplication-schema (gratis, browser-only, EN+NL, offers=0 EUR)
- i18n `pageTitle` en `sub` met keyword in beide talen
- **Geen Twitter Card** — Twitter/X is verbannen voor rvmk.nl

**SEO-keuze**. Keyword is "traffic counting" (de activiteit), niet "traffic counter" (de tool). Reden: Google's SERP voor "traffic counter" wordt gedomineerd door web-analytics tools en hit-counters — irrelevant voor rvmk's doelgroep. Wisselen naar "counting" plaatst de site in een minder vervuilde SERP.

### overige

- `traffic_counter.html`, `traffic_counter_transect.html`, `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html`, `telplanning.html`: ongewijzigd in v2.6. Migratie van adjacency-snap naar deze tools staat gepland — zie Vervolgstappen.
- `build_bezocht.py`: ongewijzigd. Niet meegenomen in snap-vernieuwing — server-side pad blijft op de oude stateless nearest-edge snap (alleen voor v2.2-archief).
- `kruispunttelling.html`: bewust uit de TelSuite gehaald (niet meer in scope).
- `README.md`: versie-string bijwerken naar v2.6 met release-samenvatting.

## Datastructuren toegevoegd

| Variabele | Plaats | Doel |
|---|---|---|
| `snapNodeToWays` | pocket_count.html, pocket_debug.html | node_id → set van wayIds |
| `snapAdjacency` | pocket_count.html, pocket_debug.html | wayId → set van adjacent wayIds |
| `snapAnchorWayId` | pocket_count.html, pocket_debug.html | huidig anker (null bij bootstrap) |
| `snapAnchorSegIdx` | pocket_count.html, pocket_debug.html | segment-index binnen anker-way |
| `snapTrace` | pocket_debug.html | array van event-records voor `_snap_trace.csv` |
| `snapTraceSeq` | pocket_debug.html | monotoon volgnummer voor trace-events |
| `originalFile[sid]` | telrapport.html | File-blob origineel ZIP (voor correctie-export) |
| `allTelregels[sid]` | telrapport.html | alle parsed rows inclusief unsnapped |
| `editMarkers[sid]` | telrapport.html | sleepbare Leaflet-markers per sessie |
| `editModeActive` | telrapport.html | sleep-modus aan/uit |

## Helpers toegevoegd

| Functie | Plaats | Doel |
|---|---|---|
| `snapRegisterWay(el)` | pocket_count.html | Incrementele adjacency-graaf bouwer |
| `snapAdjacencySet(wayId, depth)` | pocket_count.html | Bereikbare wayIds binnen depth N |
| `snapDistanceToWay(p, wayId)` | pocket_count.html | Min-afstand van punt tot specifieke way (zonder cutoff) |
| `traceWrite(...)` | pocket_debug.html | Eén trace-record schrijven |
| `buildSnapTraceCsv(sid)` | pocket_debug.html | snap_trace.csv genereren |
| `bearingDeg(lat1, lon1, lat2, lon2)` | telrapport.html | Bearing in graden, 0=N met klok mee |
| `movePoint(lat, lon, bearing, distM)` | telrapport.html | Haversine forward |
| `offsetMarkerPos(snap)` | telrapport.html | 4m offset loodrecht op way-as |
| `snapAndSideOnWay(...)` | telrapport.html | Snap + zijde-bepaling in travel-frame |
| `findNearestWays(lat, lon, n, maxDistM)` | telrapport.html | N dichtstbijzijnde ways uit wayData |
| `travelBearingForRow(r)` | telrapport.html | Beste bearing-schatting uit telregel |
| `makeEditIcon(typeColor, isCorrected)` | telrapport.html | Sleepbaar marker-icon |
| `toggleEditMode()`, `enterEditMode()`, `exitEditMode()` | telrapport.html | Sleep-modus lifecycle |
| `showHoverHL(geometry)`, `clearHoverHL()` | telrapport.html | Hover-highlight op kandidaat-ways |
| `handleDragEnd(marker)` | telrapport.html | Drag-eind verwerking |
| `showWayChoicePopup(marker, anchorLL, candidates)` | telrapport.html | Kandidaat-keuze popup |
| `applyCorrection(marker, chosen, snap)` | telrapport.html | Way-wissel toepassen |
| `applySideSwap(marker)` | telrapport.html | Zijde-flip toepassen |
| `countCorrections(sid)` | telrapport.html | Aantal correcties per sessie |
| `updateCorrUi()` | telrapport.html | Export-knop opacity/enable |
| `buildTelregelsCsv(sid)` | telrapport.html | Telregels CSV herbouwen |
| `buildStratenCsv(sid, origText)` | telrapport.html | Straten CSV delta-aggregatie |
| `exportOneCorrectedZip(sid)`, `exportCorrectedZips()` | telrapport.html | Export herbouwen ZIPs |

## Constanten (toegevoegd)

| Constante | Waarde | Plaats | Doel |
|---|---|---|---|
| `SNAP_RESET_M` | 50 | pocket_count.html, pocket_debug.html | Anker buiten deze afstand breekt |
| `ANCHOR_PREFER_M` | 50 | pocket_count.html, pocket_debug.html | Boven deze afstand vervalt anker-voorkeur |
| `HYSTERESIS_M` | 5 | pocket_count.html, pocket_debug.html | Minimum-meterdrempel voor wissel |
| `HYSTERESIS_RATIO` | 0.3 | pocket_count.html, pocket_debug.html | Fractie van d_anchor als alternatieve drempel |

`SNAP_MAX_M` en `SNAP_ROAD_FETCH_RADIUS` ongewijzigd.

## Edge cases & beslissingen

**`SNAP_RESET_M = SNAP_MAX_M`**. Conceptueel scherp: een anker buiten het bereik waar we überhaupt snappen, bestaat niet meer. Voorheen op 100m — gaf een gat tussen "anker is niet meer dichtbij" en "anker is officieel weg" waar het algoritme verkeerd gedrag vertoonde. Drie veldtesten lieten verschillende symptomen zien voordat deze waarde uitkristalliseerde.

**Hysterese als glijdende drempel**. Eerste versie was een vaste 5m absolute drempel; tweede versie ratio 0.7 (buur moet ≥30% beter zijn); huidige versie `max(5m, 30% × d_anchor)`. Reden: bij stilstand met d_anchor=8m is 5m absoluut beschermend genoeg, maar bij d_anchor=30m moet de drempel mee groeien anders helpt 5m niet. Doorgerekend op 26 anker-wissels uit veldtrace 1 → 11 zouden geblokkeerd worden, 1 zou een reset worden, 14 zouden toegestaan zijn (de echte verplaatsingen).

**Steps en corridor in Overpass**. Spijkenisse Centrumpassage heeft een parkeerdak (`highway=service`) bovenop de voetgangerszone (`highway=pedestrian`). OSM-mappers hebben de verbindende trappen als `highway=steps` gemapt, maar de Overpass-query laadde die niet. Resultaat: in de adjacency-graaf waren beide niveaus niet verbonden, anker op het parkeerdak (na een eerdere keuze) hield de teller minutenlang in glitch_hold ondanks dat de juiste passage-way pal onder zijn voeten lag. Voor corridor geldt vergelijkbaar: winkelcentrum-passages worden vaak met `highway=corridor` gemapt en functioneren als verbindende ways.

**Tap-anker-erfenis bij null-snap**. Wanneer een tap valt op een moment dat verse GPS-snap `null` retourneert (glitch_hold), erft de tap het huidige anker plus segIdx plus cached osmName. Argument: een tap zonder wayId is een data-gat; een tap met de meest waarschijnlijke wayId (= waar we volgens de fix-keten net waren) is een vermoedelijk correcte toewijzing. Niet toegepast tijdens bootstrap (anker is dan nog `null`): tap belandt in `snapPendingQueue` zoals vóór de adjacency-fix.

**Drag-vs-click in editmode**. Eén DOM-element levert beide events. Oplossing: `dragstart` zet `marker._wasDragged = true`, `click`-handler checkt en negeert als de vlag staat (reset hem dan). Voorkomt dat na elke sleep ook nog de keuze-popup opent.

**`originalFile`-geheugen**. Bij sessie-load wordt het File-blob ongeacht appType opgeslagen, ook voor pocket/transect/capaciteit waar de export-feature nooit wordt aangeroepen. Acceptabel: een paar MB per sessie blijft in scope tot reset, maar er is geen andere goede plek om de bytes te bewaren en het maakt de code rechttoe-rechtaan.

**Stratenaggregatie via delta**. Originele `_straten.csv` heeft een naam→way mapping die niet altijd matcht met de `straat`-velden in telregels (telregels gebruiken vaak OSM `name`, straten gebruikt soms een gegroepeerde naam). Delta-aggregatie behoudt het mapping: per telregel zoek je de straten-rij via wayId, en increment je daar het type-veld. Nieuwe wayIds die in geen enkele bestaande rij voorkomen krijgen een nieuwe rij gegroepeerd op `straat`. Eindigt met `bezet + vrij === 0`-rijen verwijderd (correcties hebben alle observaties weggehaald).

**Manuele correctie + sessie-toggle**. Een correctie wordt direct in `allTelregels[sid][i]` (in-place) doorgevoerd. Dat is ook de array waarop `telData[sid]` wijst als reference. Dus drawClusters() op deze sessie ziet de wijziging meteen. Bij sessie-uit-toggle gebeurt niets met de correcties (ze blijven in memory); bij reset wordt alles opgeruimd.

**Pocket_debug naast pocket_count**. Bewust twee bestanden in plaats van een debug-modus binnen pocket_count. Reden: het algoritme is in actieve ontwikkeling. Voor veldtesten wil je *exact* weten welke versie je hebt gebruikt; één bestand maakt dat traceerbaarder. Voornemen is dat pocket_debug uiteindelijk opgaat in pocket_count zodra het algoritme stabiel is.

**Geen Twitter Card in SEO**. Twitter/X is voor rvmk.nl verbannen. Open Graph dekt LinkedIn/Slack/iMessage/Discord/Facebook/Mastodon previews. Notitie geheugen-opgeslagen voor toekomstige sessies.

## Vervolgstappen (niet in v2.6)

**Uit v2.5-overdracht doorgeschoven** — geen wijziging in scope, prioriteit, of stand van zaken:
- *Stand-still aggregatie over locaties* (spatial-merge met buffer + weekprofiel-achtige popup).
- *Stats-paneel uitbreiding voor stand-still* (totaal passages/u-pill).
- *Dag-filter + weekprofiel-popup inconsistentie* (heatmap-popup negeert dag-filter).
- *Weekprofiel-popup ververst niet automatisch* bij sessie-visibility-toggle.
- *Weekprofiel-knop verschijnt soms niet bij gemengde data*.
- *Adaptieve segmentlengte* en *segment-koppeling met capaciteit* (uit v2.4-overdracht).
- *Afwijkende-waarden filter in telplanning*.
- *"Nu"-knop in telplanning-matrix*.
- *IndexedDB-estafette pocket → telrapport*.

**Nieuw uit v2.6-overwegingen:**

- *Snap-fix migreren naar parkeertelling, fietsparkeren, capaciteitstelling, transect*. Mechanische port volgens 6-stappen migratieplan in `snap_methodology.html` sectie 9. Per app: Overpass-query verbreden (`out body geom`, `steps|corridor` toevoegen), adjacency-state toevoegen, helpers toevoegen, snapNearestWay vervangen, snapRegisterWay aanroepen in fetch-handler, tap-handler anker-erfenis toevoegen. Geen wijziging aan CSV-schemas.
- *Bearing/zijde-snap interactie bij parkeertelling*. Risico-paragraaf gedocumenteerd in `snap_methodology.html`. Eventueel apart documenteren als veldtesten na migratie issues laten zien. Mostly theoretical voor brave parkeer-omgevingen; nog niet acuut.
- *pocket_debug → pocket_count fuseren*. Zodra het snap-algoritme stabiel is na een veldtest-ronde, kan de tracing op een vlag (default uit) of structureel meegenomen worden. Eén app onderhouden is altijd beter dan twee.
- *Help-doc + zip_format_reference voor correctie-tool*. De `manually_corrected`-kolom in `_telregels.csv` is nog niet gedocumenteerd. Bij volgende help-opfris meenemen: `traffic_counter_help.html` sectie 30 (sleep-modus uitleg + export naar `*_corrected.zip`), `zip_format_reference.html` auto/fiets-`_telregels.csv`-blok (`manually_corrected` als optionele extra kolom met waarde `1`).
- *Snap_methodology.html opfris na migratie*. Scope-banner aanpassen, parameter-tabel bijwerken als waarden in praktijk zijn doorgevoerd, eventueel een stuk over de adjacency-graph-evolutie tijdens de v2.6-ontwikkelcyclus.
- *Layer-aware snap*. Voor gebieden waar `highway=steps` ontbreekt of layer-overgangen niet expliciet zijn gemapt zou layer-aware verbindings-logica nog steeds helpen. Niet acuut: OSM-mapping doet zijn werk hier.
- *Andere ontbrekende way-types*. Het patroon "OSM heeft het correct, mijn query laadt het niet" kan in meer gevallen optreden — `track`, `bridleway`, etc. Per veldtest evalueren.

## Verifieerbaar via

**Snap-algoritme (pocket_count.html)**:
- Wandel een dichte voetgangerszone met parallelle passages (bijv. Spijkenisse Centrumpassage / Nieuwstraat-west) → tikken landen op de way waar je daadwerkelijk loopt, niet op de parallel.
- Sta stil bij een T-kruising → anker blijft op dezelfde way ondanks GPS-jitter (hysterese werkt).
- Loop snel van A naar B met een onbedekte korte way tussen → anker maakt depth-2-sprong, niet stuck.
- Loop een trap af van een parkeerdak naar een passage → anker schakelt via de `highway=steps`-edge.

**Debug-trace (pocket_debug.html)**:
- Open een sessie ZIP en kijk in `_snap_trace.csv` → één regel per GPS-fix en per tap; `snap_path`-waarden geven inzicht in welke tak van de ladder won.
- Filter op `snap_path = "d1_hold"` → momenten waar hysterese het anker beschermde.
- Filter op `event = "tap"` → joinen met `_telregels.csv` op `tap_nr`.

**Correctie-tool (telrapport.html)**:
- Open een auto- of fietsparkeer-ZIP met een onjuiste snap → activeer "sleep-modus" → markers worden sleepbaar.
- Sleep marker naar juiste way → popup (bij meerdere kandidaten) of directe wissel (bij één duidelijke).
- Klik op marker zonder slepen → kandidaat-keuze-popup verschijnt.
- Voer correcties door → "Export gecorrigeerd"-knop wordt actief.
- Exporteer → `<originele_naam>_corrected.zip` download. Telregels en straten bijgewerkt, PNG/GPX/sessie/netwerk/gps binair intact.
- Open `*_corrected.zip` opnieuw in telrapport → kaart toont gecorrigeerde locaties.

**Index.html / SEO**:
- View source → meta description, canonical, Open Graph, JSON-LD WebApplication-schema aanwezig. Geen Twitter Card.
- Title in browser-tab: "Online Traffic Counting — ..." (NL: "Online Verkeersteller — ...").
- Google Rich Results Test op `https://rvmk.nl/` → WebApplication-data correct herkend.

## Bestanden gewijzigd t.o.v. v2.5

| Bestand | Type wijziging |
|---|---|
| pocket_count.html | Adjacency-snap, hysterese, pre-reset, steps+corridor in Overpass, tap-anker-erfenis |
| pocket_debug.html | **NIEUW** — pocket_count + snap_trace.csv |
| telrapport.html | Correctie-tool (sleep-modus + export gecorrigeerde ZIPs) |
| index.html | Card-consistentie, brand-block, SEO-pakket (geen Twitter), keyword "counting" |
| traffic_counter_help.html | Header-wrap fix, sectie 13/25/30/38 inhoudelijke updates |
| zip_format_reference.html | Volledige vertaling NL → EN, stand-still als zesde sectie |
| snap_methodology.html | **NIEUW** — Engelstalige snap-tech-doc met bearing-notitie |
| README.md | Versie-string |
| kruispunttelling.html | **VERWIJDERD** uit TelSuite-scope |
| overdracht_v2_6.md | **NIEUW** |

Geen wijzigingen aan `build_bezocht.py`, `traffic_counter.html`, `traffic_counter_transect.html`, `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html`, `telplanning.html`. v2.6 verbetert pocket en telrapport in plaats van een breed feature-pakket: de andere apps wachten op de snap-migratie in v2.7.
