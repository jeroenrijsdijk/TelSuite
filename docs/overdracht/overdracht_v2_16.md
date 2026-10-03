# TrafficCounterSuite v2.16 — Overdracht

Zes wijzigingen, geen enkele raakt een schema. **(1) Telrapport — bbox-filter:** een opt-in vinkje dat bij het laden van meerdere bestanden/een map de tellingen buiten het huidige kaartbeeld overslaat, gemeten op de netwerk-bbox met 12% marge. **(2) Telrapport — weer per telling:** lazy Open-Meteo-verrijking in de sessie-details (temperatuur, neerslag, wind + vlaag + richting, WMO-icoon), duur-gewogen over de teluren. **(3) Helpfile:** inline-styles → semantische classes (116 → 39), plus een `flex-wrap`-fix voor de knoppenrij die de intro-kaart uitliep. **(4) Telrapport — wegvak-keuze:** de correctie-popup toont nu 5 kandidaten i.p.v. 3, via één benoemde constante. **(5) Telrapport — telefoon-lade:** op een smal scherm wordt de zijbalk een inschuif-lade over de kaart, met ☰-knop. **(6) Richting-fix in de drie loop-tel-apps** (parkeren, fietsparkeren, capaciteit): de zijde wordt bepaald t.o.v. je werkelijke looprichting (netto over ~12 m pad) i.p.v. de fragiele momentane koers — veldgetest, met de fietspad-rijbaan-correctie intact.

In de geest van v2.12–v2.15: additief, **de-drift waar het kan**, en zwakke schakels vervangen zonder de omliggende, hard-bevochten logica aan te raken. De richting-fix vervangt precies één referentie in `bestOsmBearing` en laat de snap (incl. `FORCE_CYCLE_TO_ROAD`) volledig staan; de gedeelde blokken zijn byte-identiek over de drie apps.

---

## Gewijzigde bestanden

| Bestand | Status | Kern van de wijziging |
|---|---|---|
| `telrapport.html` | ✦ bijgewerkt | (1) **Bbox-filter** bij het laden (opt-in `#bbox-filter-cb`): `probeBbox()` leest de bbox uit `_netwerk.csv` (WKT, terugval `_gps.csv`, punt voor stilstaand-CSV) zónder volledige laadbeurt; alleen treffers binnen het bevroren, 12% gepadde kaartvenster gaan door `loadFile`. (2) **Weer** per telling: lazy Open-Meteo-verrijking in de vier per-sessie detail-views. (4) **Wegvak-keuze** 3 → 5 via `WAY_CHOICE_N`. (5) **Inschuif-lade** op smal scherm (≤720px) met ☰/✕-knop, backdrop, auto-dicht bij sessie-tik, auto-open bij detail-paneel |
| `traffic_counter_help.html` | ✦ bijgewerkt | (3) **Inline→class-refactor**: 102 structurele inline-styles over 51 patronen omgezet naar semantische + utility-classes (116 → 39 resterend, alle enkel-property accentkleuren). Plus `flex-wrap: wrap` op `.back-links` (de zeven modus-knoppen liepen de intro-kaart uit) |
| `parkeertelling.html` · `fietsparkeren.html` · `capaciteitstelling.html` | ✦ bijgewerkt | (6) **Richting-fix**: `bestOsmBearing` gebruikt nu `travelRefBearing` (netto looprichting over de laatste ~12 m pad, opgebouwd in `onPosition` via `trail`) als referentie voor θ-vs-θ+180, met terugval op `currentBearing`/kompas. Constanten `TRAVEL_WINDOW_M`/`TRAVEL_MIN_M`. De 4 m-offset, de kantel-zijde en de fietspad-rijbaan-correctie zijn ongewijzigd |
| `README.md` | ✦ bijgewerkt | Versie → v2.16; release-noot |

Ongewijzigd: alle overige bestanden (`pocket_count.html`, `telplanning.html`, `traffic_counter.html`, `snaptrace.html`, `snap_methodology.html`, `zip_format_reference.html`, `index.html`, `planningen/*`, `_archief/*`). **Geen schema- of ZIP-structuurwijziging** — bbox-filter en weer zijn puur telrapport-view-laag (weer wordt live opgehaald, niet weggeschreven), en de richting-fix verandert alleen de kant waarheen de bestaande 4 m-offset gaat, niet de CSV-velden. KNIME en de downstream-pipeline blijven ongemoeid.

---

## Deel 1 — Bbox-filter in telrapport

**Aanleiding.** Sleep je een map met tellingen uit meerdere gemeenten in telrapport, dan wil je vaak alleen het gebied zien waar je op ingezoomd bent. Telrapport kende geen ruimtelijke voorfilter.

**Het addertje — een bbox is niet gratis.** De coördinaten zitten alleen in `_netwerk.csv` (`geometrie_wkt`) en `_gps.csv`, niet in de bestandsnaam. Je kunt een bestand dus niet ongezien overslaan. Maar het openen is veel lichter dan een volle laadbeurt: de **probe** doet alleen `JSZip.loadAsync` + één CSV inflaten + min/max, geen wayData-bouw of teken.

**Aanpak (in `ingestFiles`, één plek — alle invoerkanalen lopen erdoor).** Staat het vinkje aan, dan:
1. Bevries het huidige beeld (`map.getCenter/getZoom`) vóór de eerste per-telling `fitBounds` het verspringt; neem `map.getBounds().pad(0.12)` als filtervenster.
2. `probeBbox(file)` per bestand → `{minLat,maxLat,minLon,maxLon}` of `null`. WKT-scan pakt LINESTRING én POLYGON via een coördinaten-paar-regex, dus ook parkeer-vlakken krijgen een bbox.
3. `bboxesOverlap` (rechthoek-overlap, **deel-overlap telt mee**) bepaalt de treffers; alleen die gaan door de normale `loadFile`.
4. Achteraf terug naar het bevroren kader (`setView`) en een statusregel: "✓ N/M binnen beeld geladen · K overgeslagen".

**Fail-open.** Een bestand waarvan de bbox niet te lezen is (geen geometrie, corrupte ZIP) wordt tóch geladen — het filter sluit alleen uit wat het positief búíten beeld kan leggen. Geen stille dataverlies.

---

## Deel 2 — Weer per telling (Open-Meteo)

**Idee.** Het weer van het moment (regen, temperatuur, wind) is relevante context bij een telling. Open-Meteo levert dat gratis, zonder API-key, CORS-enabled (dus rechtstreeks uit de browser), op uur-resolutie per coördinaat + datum.

**Scope.** Puur telrapport-view-laag: **live ophalen bij het openen** van een sessie-detail, niet wegschrijven in de CSV. Werkt dus met terugwerkende kracht op alle bestaande ZIPs; geen KNIME-sign-off. Ingehaakt in de vier per-sessie detail-views die een `sid` hebben (stilstaand-popup, transect-cluster, parkeer-cluster, capaciteit) via `weatherBlock(sid)`.

**Slimme randjes.**
- **Endpoint-keuze op leeftijd** (`wxEndpoint`): ≤90 dagen → live forecast met `past_days`; 2022→ → historical-forecast-API; ouder → ERA5-archive. Zelfde parameters, andere hostname.
- **Dedup-cache** (`WX_CACHE`) op afgerond coördinaat (~0,1°) + datum → een hele stad-dag aan tellingen valt samen op één call.
- **Duur-gewogen aggregatie** (`wxAggregate`) over de overlapte teluren, elk getal op z'n eerlijke manier: temperatuur = gewogen gemiddelde (met bereik bij >2°C spreiding), neerslag = som, wind = gemiddelde + **max vlaag**, richting/WMO-code = dominant uur (codes kun je niet middelen). Coördinaat = zwaartepunt van de telling (weer-grid 1–25 km, dus centroïde volstaat); tijd = sessievenster in `Europe/Amsterdam`.
- **Fail-open**: geen net / API plat / telling op zee → "weer onbekend", nooit blokkerend. Klein bronregeltje "weer: Open-Meteo" (CC BY 4.0).

---

## Deel 3 — Helpfile: inline-styles → classes (+ wrap-fix)

De helpfile had 116 inline-styles. **Lijn:** structuur → class, per-instantie accentkleur → inline. 102 structurele styles (de 8-property sectie-dividers, herhaalde marges, callout-randen, legenda-stip-geometrie) zijn omgezet naar een klein systeem: spacing-utilities (`.mt-*`, `.nowrap`, `.mr-6`), semantische blokken (`.note`, `.subhead`, `.divider`/`-line`/`-label`/`-back`, `.list-tight`), callout-accenten in lijn met het bestaande `.card.mode-*` (`.card.bl-*`), en `.dot`/`.dot-fill`/`.dot-ring` + `.swatch`. De 39 resterende inline-styles zijn bewust enkel-property accentkleuren (die als class alleen bijna-dubbele kleurklassen zouden opleveren).

Kleuren zijn **exact** behouden (de inline `#27ae60` is níét stilletjes `var(--green)` geworden — dat zijn verschillende groenen), classes zijn gemerged waar al een `class` stond (geen dubbele attributen).

**Wrap-fix.** Bij nader inzien liep de intro-kaart ("TELLEN") uit beeld: `.back-links` (`display:flex`, ooit voor een paar header-links) draagt daar zeven modus-knoppen zonder wrap. `flex-wrap: wrap` toegevoegd — de class wordt maar op die ene plek gebruikt, dus veilig. (Kwam níét uit de refactor; dat blok had geen inline-styles.)

---

## Deel 4 — Wegvak-keuze 3 → 5

In de sleep-/klik-correctiepopup toonde telrapport de huidige link plus twee alternatieven — in de praktijk te weinig. Er zat een hardgecodeerde `3` op drie plekken (`handleDragEnd`, de klik-modus-lookup, en de `slice` na de huidige-link-injectie). Alle drie vervangen door één benoemde constante **`WAY_CHOICE_N = 5`** (tegen drift, zoals bij `HIGHWAY_RE`). De 100 m-straal blijft; op een rustige plek toont-ie er gewoon minder (nette terugval).

---

## Deel 5 — Inschuif-lade op smal scherm

Telrapport is primair een desktop-tool, maar doet het verrassend goed op de telefoon — behalve dat de vaste zijbalk van 300px de kaart onbruikbaar smal maakte. Op een scherm ≤720px wordt de zijbalk nu een **inschuif-lade**: `position:fixed` en uit de flex-flow (waardoor `#map`, `flex:1`, automatisch de volle breedte pakt), standaard uit beeld via `transform`, terug te halen met een ☰-knop (die ✕ wordt). Alles in één `@media`-query — desktop verandert niet.

**Gedrag.** Tik op een sessie of het oog → lade dicht (dan zie je het resultaat). Tik-naast of de ☰/✕ → dicht (de knop staat boven de lade, dus opent én sluit). Tik op een marker/cluster → het detailpaneel zit ín de zijbalk, dus een `MutationObserver` op `#detail-panel` schuift de lade juist open zodat je het (incl. weer) leest. Bij het kruisen van het breekpunt één `map.invalidateSize()`; Leaflet's zoom-knoppen worden op smal scherm onder de ☰ geduwd.

---

## Deel 6 — Richting-fix in de drie loop-tel-apps

**Symptoom (uit een veld-ZIP).** Auto's kwamen aan de verkeerde kant van de link te staan.

**Diagnose.** Telrapport is hier een trouwe renderer (tekent op `lat_marker/lon_marker`, groepeert alleen op `zijde`). De telefoon zet de marker op een vaste **4 m-offset** naar de kant die uit `zijde` volgt, en `zijde` werd bepaald t.o.v. `hdgGebruikt` = `bestOsmBearing(...)` — dat de wegas oriënteert naar `currentBearing`, een over 5 fixes gladgestreken GPS/kompas-fusie. Die fusie loopt achter bij ommekeren en zakt weg bij stilstaan (juist de condities van een parkeertelling). In de veld-ZIP week de opgeslagen richting in **103/140** regels af van de werkelijke looprichting.

**De waarheid is binair.** De OSM-link legt maar twee mogelijkheden vast: θ of θ+180. Je hoeft dus geen betrouwbare absolute koers te schatten (GPS én kompas falen daar), alleen het teken van je **voortgang langs de link** — en dat is robuust: jitter middelt uit, zijwaartse ruis telt niet mee.

**Fix (één referentie vervangen).** In `onPosition` wordt een `trail` van recente posities bijgehouden met cumulatieve padlengte; `travelRefBearing` = de netto looprichting over de laatste ~12 m (`TRAVEL_WINDOW_M`), pas vertrouwd na ~6 m netto pad (`TRAVEL_MIN_M`), met een GPS-sprong-reset (>50 m). `bestOsmBearing` gebruikt `travelRefBearing` als primaire referentie (terugval `currentBearing` → kompas → geen flip). De hysterese zit in de vensterlengte: een ommekeer telt pas mee na ~6–9 m écht teruglopen — en precies dan loop je toch even zonder te tellen. De 4 m-offset en de kantel-zijde zijn ongewijzigd; alleen de kant waarheen die 4 m gaat, klopt nu.

**Fietspad-rijbaan-correctie bewust ongemoeid.** `SNAP_ROAD_TYPES`/`SNAP_CYCLE_TYPES`, `snapWeight`, `SNAP_FORCE_DIST=8` en `FORCE_CYCLE_TO_ROAD` (auto-only) blijven exact staan — die werkten al (in de veld-ZIP hingen alle auto's aan rijbanen, nul aan fietspad). Rijbaan ∥ fietspad, dus de vergelijking θ-vs-θ+180 kiest ook de goede kant als je op het fietspad loopt.

**Harmonisatie.** Parkeren, fietsparkeren en capaciteit delen deze code. De globals en de `bestOsmBearing`-referentieketen zijn **byte-identiek** over de drie (zelfde md5); de enige bewuste afwijking is de trail-inhaak — capaciteit zet `currentLat` bovenaan `onPosition` en houdt de vorige fix in `prevLat/prevLon`, dus dáár is de trail op `prevLat/prevLon` gehaakt.

**Bron-fix.** Geldt voor nieuwe tellingen; bestaande ZIPs hebben de verkeerde kant al ingebakken (de 4 m-offset verving de echte plek) en zijn niet betrouwbaar achteraf te herstellen.

---

## Validatie

- **Alle gewijzigde HTML**: inline JS geëxtraheerd + `node --check` groen; tag-balans gecontroleerd (telrapport `div` 102/102 na de toevoegingen; helpfile `div` 156/156 · `p` 137/137 · `span` 65/65 · `a` 52/52; auto/fiets/capaciteit `script`/`style`/`div` sluitend).
- **Bbox-filter**: 22 unit-asserts op de bbox-logica (LINESTRING/POLYGON-scan, overlap-randgevallen incl. rand-raking en punt-bbox, accumulatie, fail-open) + 10 end-to-end probe-tests op echte JSZip/PapaParse-paden (netwerk wint van gps, POLYGON, gps-terugval, geen-geometrie → null, corrupte ZIP → null).
- **Weer**: 21 unit-asserts op de aggregatie (duur-weging + bereik, neerslag-som-naar-rato, wind-gemiddelde + max-vlaag, dominant-uur richting/code, geen-overlap → null, binnen-één-uur, kompas-mapping, lokale datum zonder UTC-rollback, endpoint-keuze). Live endpoint niet vanuit de sandbox pingbaar; params/respons-vorm tegen de Open-Meteo-docs gelegd.
- **Helpfile**: 102 omzettingen met een assert op het exacte aantal per patroon (51 patronen); elke gebruikte class gedefinieerd; geen dubbele `class`-attributen; tag-balans gelijk.
- **Wegvak-keuze**: `WAY_CHOICE_N` 1× gedefinieerd, 3× gebruikt; geen verdwaalde `3` meer in het kandidaat-pad.
- **Richting-fix**: veld-replay op de auto-ZIP — de door de telefoon opgeslagen richting week in 103/140 regels af van de werkelijke netto looprichting; de nieuwe referentie ís die looprichting. Byte-identiteit van de gedeelde blokken over de drie apps geverifieerd (md5). **Door de gebruiker in het veld getest (heen-en-terug over één straat): werkt.**

---

## Backlog (bijgewerkt)

### Afgerond deze release
- ~~telrapport: bij het laden van een map alleen de tellingen binnen het huidige kaartbeeld~~ → **bbox-filter (opt-in, netwerk-bbox, 12% marge, deel-overlap, fail-open)**.
- ~~telrapport: weer van het moment bij een telling~~ → **lazy Open-Meteo-verrijking in de sessie-details (duur-gewogen, dedup-cache, endpoint-keuze)**.
- ~~helpfile: inline→class-refactor (~108 inline-styles)~~ → **gedaan (102 omgezet); + `.back-links` wrap-fix**.
- ~~wegvak-correctiepopup: te weinig alternatieven~~ → **5 keuzes via `WAY_CHOICE_N`**.
- ~~telrapport onbruikbaar op de telefoon (vaste zijbalk)~~ → **inschuif-lade op ≤720px**.
- ~~auto's/fietsen aan de verkeerde kant van de link~~ → **richting-fix (`travelRefBearing`, voortgang langs de link + hysterese) in parkeren/fietsparkeren/capaciteit; fietspad-rijbaan-correctie intact; veldgetest**.

### Volgende voor de hand liggende stap (gebrainstormd)
- **Winkelstraat → passanten/uur (Moving Observer / Wardrop-Charlesworth).** Een **standalone `passanten.html`-prototype bestaat al** (per-segment `q = 3600·M·v_p / (n·L + v_p·t)`, `tegemoet`-tik als meeting-count, `stilstaand` als verblijf, v_p-slider, YlOrRd-heat op Leaflet, multi-zip dedup). Rest: het de suite in tillen (index/README/versie, basemap-harmonisatie) én de **heen-en-terug-decompositie** — de echte tweerichtings-footfall zonder ×2-aanname. Elegantste vorm: per tegemoet-tik de observer-richting uit de gps-track interpoleren en de tik in de fysieke richtingsbucket plaatsen — dan wordt q→ + q← *gemeten*, en de ×2-knop overbodig. Analyse-view, geen schemawijziging.

### Beslissing nog open (carry-over)
- **Planning/Opdrachten-workflow** (telplanning): A (download-als-vangnet) vs B (lokale planning terugschrijven naar server). Aanbeveling: A.

### Wens voor latere release (schema — vereist KNIME-sign-off)
- Gebiedsnaam (`sessie_naam`) in `_sessie.csv` bewaren bij parkeer-/fietsexport, zodat een hertelling de oorspronkelijke naam i.p.v. de brondatum-proxy terughaalt.

### Geparkeerd / carry-over (ongewijzigd)
- **Sleep-correctie voor pocket-tellingen** — één-regel-guard, maar échte feature-werk eronder: pocket gebruikt het `snap_trace`/segment-model i.p.v. de auto/fiets-telregels. Veldvalidatie vereist.
- Viterbi-merge → `_archief/viterbi_rig/`; ont-parkeren = simpel-only opt-in.
- Capaciteit: volledige cumulatieve-snap-port (`elementsNear` + `SNAP_SEGS_RADIUS` + highway-filter).
- telrapport: per-richting detailtabel (transect); winkelstraat-decompositie-view (zie Moving Observer).
- Pocket/telplanning: adaptieve segmentlengte, IndexedDB-relay pocket→telrapport, weekprofiel-popup auto-refresh, afwijkende-waarden-filter.
- Hoogtesignaal (`altitude`) voor roltrap/trap-detectie — eerst een meet-probe.
- Stand-still-locatie-aggregatie voor herhaalde tellingen op dezelfde plek.
- Off-netwerk/area-snapping; `snapSegs`-vervanging-bij-refetch (structureel).
- Helpfile: de ~39 resterende enkel-property kleur-inlines (alleen als je écht naar nul wilt; ~25 bijna-dubbele kleurklassen — lage waarde).
