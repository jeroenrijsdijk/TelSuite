# TrafficCounterSuite v2.14 — Overdracht

Eén nieuwe feature en een reeks veld-fixes, twee bestanden. **(1) Telplanning** krijgt een echte uitbreiding — een planning reconstrueren uit een eerder gelopen ZIP ("hertelling") — plus de layout-bug die de linkerkolom afkapte, de status-regel die van het scherm liep, en vier kleinere correctheids-/UX-fixes. **(2) Telrapport** wordt weer bruikbaar bij veel tellingen: straatsegmenten zijn weer aanklikbaar dóór de dot-wolk heen.

Waar v2.12–v2.13 draaiden om *drift weghalen*, voegt v2.14 bewust iets toe — maar in dezelfde geest: de hertelling is geen nieuw subsysteem maar een **tweede invoerkanaal naar de bestaande `processWays()`-pijplijn**, en de telrapport-fix bundelt vijf losse straatlijn-aanmaakplekken tot één helper. Additief, maar de-drift waar het kan.

---

## Gewijzigde bestanden

| Bestand | Status | Kern van de wijziging |
|---|---|---|
| `telplanning.html` | ✦✦ uitgebreid | **Hertelling uit ZIP** (nieuw); zijbalk scrollbaar + vaste export-voet; wegtype-deselectie kleurt de kaart nu mee; status-regel kort in i.p.v. overlopen; Safari-datumparser; export-disable gelijkgetrokken; lege-staat-hint in Dekking |
| `telrapport.html` | ✦ bijgewerkt | Straatsegmenten aanklikbaar dóór de dots heen: nieuwe `wayhit`-pane (z-index 560) met `makeWayLine`-helper (zichtbare lijn + onzichtbare brede kliklijn per straat); vijf aanmaakplekken gebundeld; hover-highlight uit de dot-wolk gelift |
| `README.md` | ✦ bijgewerkt | Versie → v2.14; hertelling toegevoegd aan telplanning-features |

Ongewijzigd: `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html`, `pocket_count.html`, `traffic_counter.html`, `traffic_counter_help.html`, `snaptrace.html`, `snap_methodology.html`, `zip_format_reference.html`, `index.html`, `build_bezocht.py`, `planningen/*`, `_archief/*`.

---

## Deel 1 — Telplanning: hertelling uit ZIP

**Het idee.** Een planning aanmaken zonder opnieuw een contour te tekenen en wegen te selecteren — door een eerder gelopen parkeer- of fietsZIP in te laden en de wegenset eruit te reconstrueren. Voor een herhaalmeting wil je per definitie *exact dezelfde scope*; vergelijkbaarheid is het hele punt.

**Harde randvoorwaarde.** De planning-JSON reist *niet* mee in de export-ZIP — `parkeertelling.html` leest `?plan=` wel in maar schrijft 'm niet terug; de ZIP bevat alleen de zeven standaardbestanden. De hertelling kan dus geen ingebedde planning uitpakken; ze **reconstrueert** de wegenset uit de CSV's. Dat is meteen het nette deel: geen snapping, geen map-matching, geen aanraking van de v2.13-"irreducible remainder".

**Wegenset = set B (straten ∩ netwerk).** `_straten.csv` zegt *welke* wegen in de telling zaten (`osm_way_ids`, pipe-gescheiden per straatnaam); `_netwerk.csv` levert de geometrie per `osm_way_id` (`geometrie_wkt`). De doorsnede is precies de gelopen scope. Wegen die wél in netwerk maar niet in straten zitten (doorgaande wegen die je passeerde maar niet telde) vallen er bewust buiten.

**Door de bestaande pijplijn.** De gejoinde wegen worden omgezet naar **pseudo-Overpass-elementen** (`{type:'way', id, tags:{highway,name}, geometry}`) en door de bestaande `processWays(elements, null)` gehaald. `null`-polygoon → alles `inPoly` → alles geselecteerd. Daarmee erven we way-objecten, lagen, deselectie, fit-bounds en stats zonder duplicatie. De segment-variant van `_netwerk.csv` (pocket-stijl, `segment_index`) wordt defensief gestitcht op volgorde met dedup van de grens-node; de hoofdroute (auto/fiets, volle-way-geometrie) is één rij per way.

**Metadata-prefill:**
- **Naam** — *het gebiedsnaam-veld (`sessie_naam`) staat niet in de ZIP*; dat leefde alleen in de planning-JSON. De ZIP biedt geen herbruikbare gebiedsnaam, dus de naam wordt voorgevuld als `hertelling <DD-MM-YYYY>` (brondatum als anker) en staat meteen geselecteerd om over te typen. *Wens voor v2.15: parkeertelling/fietsparkeren de gebiedsnaam in `_sessie.csv` laten bewaren, zodat een hertelling de oorspronkelijke naam kan terughalen — schemawijziging, vereist KNIME-sign-off.*
- **Teller / teltype** — uit `_sessie.csv` (`teller`, `app_type` → auto/fiets).
- **Datum + tijd** — het **eerstvolgende vergelijkbare moment**: zelfde weekdag én klokstijd, strikt in de toekomst. Bron dinsdag 15:00 → komende dinsdag 15:00 (vandaag mag, als die tijd nog komt; net voorbij → volgende week).

**Nieuwe helpers:** `parseWktLine` (WKT→Leaflet, lon-lat→lat-lon), `nextComparableMoment` (weekdag-tijd-berekening), `parseCsvSimple` (header-geïndexeerde puntkomma-parser), `parseDatumTijd` (Safari-veilige Date uit losse componenten), plus `makenUitZip` en `prefillUitSessie`. UI: een tweede dropzone (`dz-hertelling`) in een `maken-only`-sectie naast Gebied; de dropzone-CSS is gegeneraliseerd van `#id` naar een gedeelde `.dropzone`-klasse.

---

## Deel 2 — Telplanning: layout (scroll + sticky export)

De gemelde bug: *"de linkerkolom is soms deels niet zichtbaar."* Oorzaak: `#sidebar` was een flex-kolom met `overflow:hidden` in een body van `100vh`, zonder interne scroll. Bij genoeg secties (Maken-modus telt er nu acht, inclusief de nieuwe hertelling-sectie) liep de inhoud onder de schermrand — en `margin-top:auto` op de export-sectie duwde juist de Maak Telling-knop als eerste weg.

**Fix.** De inhoud zit nu in `#sidebar-scroll` (`flex:1; min-height:0; overflow-y:auto` — de `min-height:0` is de kern: zonder dat rekt een flex-kind de container op i.p.v. te scrollen). De export-CTA (Opdrachten + Maak Telling) staat in een vaste voet `#sidebar-foot` (`flex:0 0 auto`), altijd bereikbaar. `margin-top:auto` is verwijderd. Achtergrond-keuze scrollt mee in de inhoud.

---

## Deel 3 — Telplanning: kleinere fixes

**3a — Wegtype-deselectie kleurt de kaart nu mee.** De Maken-tak van `applyWayStyle` had alleen een *toon*-pad (`if (way.visible) addTo`), geen *verberg*-pad. Een uitgezet wegtype bleef daardoor op de kaart staan. Nu wordt de laag (incl. `_hitLayer`) van de kaart gehaald zodra `way.visible` false is.

**3b — Status-regel loopt niet meer van het scherm.** `#status-bar` had `white-space:nowrap` zonder shrink of clip; een lange melding ("Overpass ophalen via endpoint 1…") spilde rechts buiten beeld. Nu `flex:0 1 auto; min-width:0; overflow:hidden; text-overflow:ellipsis`, en `setStatus` zet de volledige tekst in `title` (bereikbaar via long-press).

**3c — Safari-datumparser.** `ingestBezochtCsv` bouwde `new Date(datum + 'T' + tijd)` — Safari's Date-parser is strenger en faalde stil bij een tijd zonder seconden, waarna het bezoek geruisloos uit de telling viel. `parseDatumTijd` bouwt de Date nu uit losse componenten (geen string-parsing), identiek op Safari en Chrome.

**3d — Export-disable gelijkgetrokken.** `processWays` gebruikte `w.selected`; `updateStats` gebruikte `w.visible && w.selected`. De export-knop volgt nu in beide gevallen `visible && selected` — geen latente drift meer.

**3e — Lege-staat-hint in Dekking.** Geladen ZIPs zonder getekende contour: een cel selecteren toonde bezoeken in de matrix maar kleurde niets op de kaart. `updateCoverageStats` geeft nu de hint *"Teken een contour om de dekking op de kaart te kleuren."*

---

## Deel 4 — Telrapport: straten aanklikbaar dóór de dots

Bij veel geladen tellingen werd het onmogelijk een straatsegment aan te klikken om het weekprofiel te openen: de telklikken (`circleMarker`s in de `clusters`-pane, z-index 550) liggen boven de straatlijnen (standaard `overlayPane`, z-index 400), en in Leaflet vangt de hoogste pane de klik zónder die door te geven. Méér tellingen inladen — precies wat gewenst is voor de weekverdeling — verergerde het. Een pane-conflict, geen aantal-probleem.

**Aanpak — straten op een eigen kliklaag bóven de dots.** Nieuwe pane `wayhit` op z-index **560**: boven de dots (550), onder de cluster-badges (620), zodat de klikbare totaal-badges sowieso blijven winnen. Per straat tekent `makeWayLine(k, geometry, style)` nu twee lijnen in die pane:
1. de **zichtbare** lijn (`interactive:false`) — je ziet het stratennet door de dot-wolk lopen;
2. een **onzichtbare brede kliklijn** (`weight:16, opacity:0`) — een royaal tikdoel voor de telefoon in het veld.

De klik/hover hangt aan de kliklijn (`wayHitLayers[k]`), de styling op de zichtbare lijn (`wayLayers[k]`) — zo blijven `recolorOne`, de hover-verdikking en de cleanup ongewijzigd werken. De twee tooltip-smaken zijn behouden als benoemde functies: `attachPocketSegmentInteraction` (p/m·u-intensiteit) en `attachSessionSegmentInteraction` (sessie-lijst), uit het inline-blok gelicht. Vijf losse aanmaakplekken (`L.polyline(...).addTo(map)`) zijn naar `makeWayLine` gebundeld; `resetAll` ruimt nu ook `wayHitLayers` op. De zijlijst-hover-highlight (`_hoverHL`) zat eveneens onder de dots verstopt en is naar dezelfde pane gelift.

**Eén veld-verificatiepunt:** de kliklijn gebruikt `opacity:0` — het standaard-Leaflet-patroon waarbij een geverfde, niet-verborgen SVG-stroke klikbaar blijft. Code-logica is groen getest; het pointer-events-gedrag zelf is browser-runtime en niet headless te toetsen. Mocht iOS Safari onverwacht anders reageren, dan is de fix triviaal (minimale niet-nul opacity).

---

## Schema & ZIP

**Geen wijzigingen.** v2.14 raakt UI, kaartinteractie en een nieuwe *lezer* van bestaande ZIP-CSV's — niet de ZIP-structuur, niet de CSV-schema's. De hertelling **leest** `_straten.csv`, `_netwerk.csv` en `_sessie.csv` in hun bestaande vorm en **schrijft** een gewone planning-JSON via de ongewijzigde `exportPlanning()`. KNIME-readers en de downstream-pipeline blijven ongemoeid.

---

## Validatie-discipline (deze release)

- Per gewijzigd bestand JS geëxtraheerd + `node --check`: groen (telplanning; telrapport — grootste inline-blok).
- Tag-balans geverifieerd: telplanning `div` 100/100 na de scroll/sticky-herstructurering; telrapport `div` 99/99, `script` 4/4.
- **Hertelling-algoritmiek** apart unit-getest: `nextComparableMoment` over de randgevallen (zelfde dag vóór de tijd → vandaag; zelfde dag ná de tijd → +7; midweek → eerstvolgende; dag ervóór → morgen) en `parseWktLine` (lon-lat→lat-lon, lege invoer).
- **Hertelling end-to-end** getest met synthetische ZIPs (vm-sandbox, echte scriptbytes): set B correct (way buiten straten uitgesloten), straatnamen + highways gejoind, coords in `[lat,lon]`, prefill (naam/teller/teltype/datum/tijd), én robuustheid: ontbrekende `_straten.csv` → duidelijke melding, way zonder geometrie → `gemist`-teller, segmented-netwerk → correcte stitch op volgorde met grens-dedup.
- **Telrapport-refactor** getest op de échte geëxtraheerde functies: `makeWayLine` maakt 2 lijnen (zichtbaar `interactive:false` / hit `weight16 opacity0`, beide pane `wayhit`), klik gebonden op de kliklijn (niet de zichtbare), hover stylet de zichtbare lijn, `mouseout`→`recolorOne`, idempotent bij her-aanroep.
- Nul resterende `wayLayers[k] = L.polyline`-directe aanmaakplekken; `makeWayLine` 5× aangeroepen; `wayHitLayers`-lifecycle (decl → set → cleanup) gecontroleerd.

---

## Backlog (bijgewerkt)

### Afgerond deze release
- ~~telplanning: layout-bug — linkerkolom deels onzichtbaar~~ → **scrollbare zijbalk + vaste export-voet**.
- ~~telplanning: status-regel valt van het scherm~~ → **ellipsis + `title`**.
- ~~telplanning: "Nu"-knop / vergelijkbaar moment~~ → **opgegaan in hertelling** (`nextComparableMoment` vult het eerstvolgende vergelijkbare moment).
- ~~telplanning: wegtype-deselectie kleurt de kaart niet mee~~ → **verberg-pad toegevoegd**.
- ~~telrapport: straat onklikbaar onder de telklikken~~ → **`wayhit`-pane + brede kliklijnen**.
- **Nieuw geleverd:** hertelling uit ZIP (telplanning).

### Beslissing nog open
- **Planning/Opdrachten-workflow** (telplanning). De Opdrachten-lijst leest van de server (`planning_list.php`); de altijd-download van de planning-JSON voedt die lijst *niet*. Bij een mislukte server-save staat de planning alleen lokaal en is er geen weg de lijst in. Twee opties besproken, nog te kiezen: **A** download-als-vangnet (server eerst, alleen lokaal downloaden als de save faalt) — **B** "laad lokale planning" die een JSON terug naar de server schrijft. *Aanbeveling: A, eventueel met B voor offline-veerkracht.*

### Wens voor v2.15 (schema — vereist KNIME-sign-off)
- Gebiedsnaam (`sessie_naam`) in `_sessie.csv` bewaren bij parkeer-/fietsexport, zodat een hertelling de oorspronkelijke naam i.p.v. de brondatum-proxy kan terughalen.

### Geparkeerd / carry-over (ongewijzigd)
- **Viterbi-merge** → in `_archief/viterbi_rig/`; ont-parkeren = simpel-only opt-in in `telrapport.html`.
- Capaciteit: vólledige cumulatieve-snap-port (`elementsNear` + `SNAP_SEGS_RADIUS` + highway-filter in `buildSegments`) — feature-werk, veldvalidatie vereist.
- telrapport: per-richting detailtabel (transect); winkelstraat-decompositie-view (Wardrop-Charlesworth).
- Pocket/telplanning: adaptieve segmentlengte, IndexedDB-relay pocket→telrapport, weekprofiel-popup auto-refresh, afwijkende-waarden-filter.
- Hoogtesignaal (`altitude`) voor roltrap/trap-detectie — eerst een meet-probe.
- Stand-still-locatie-aggregatie voor herhaalde tellingen op dezelfde plek.
- Off-netwerk/area-snapping; `snapSegs`-vervanging-bij-refetch (structureel).
- `traffic_counter_help.html`: optionele inline→class-refactor (~108 inline-styles).
