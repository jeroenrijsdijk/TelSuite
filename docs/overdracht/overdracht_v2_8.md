# TrafficCounterSuite v2.8 — Overdracht

Release rond twee samenhangende thema's: **map-matching van GPS-traces** en **begrijpbare drukte-weergave**. De snap-bug die tikken aan verkeerde links toekende is bij de bron gerepareerd. Telrapport toont drukte nu in vijf leesbare klassen.

---

## Gewijzigde bestanden

| Bestand | Status | Kern van de wijziging |
|---|---|---|
| `pocket_count.html` | ✦ bijgewerkt | snapSegs-merge, platform-robuuste download, trajectorie-hertoekenning, volledig tweetalig (NL/EN) |
| `telrapport.html` | ✦ bijgewerkt | drukteklassen blauw→geel→rood, p/m·u consistent over kaart + weekprofiel + tabel |
| `telrapport_viterbi.html` | ✦ bijgewerkt | exacte shared-node adjacency, junction-aware penalty, tik-hertoekenning (Optie A) |
| `snaptrace.html` | ✦ bijgewerkt | junction-aware penalty, node-ID adjacency vanuit Overpass |
| `_archief/pocket_debug.html` | ✗ vervallen | verouderde kopie, alles zit in pocket_count |
| `_archief/overdracht_v2_5/6/7.md` | ✗ gearchiveerd | voorgaande overdrachten |

Ongewijzigd: `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html`, `telplanning.html`, `traffic_counter*.html`, `snap_methodology.html`, `zip_format_reference.html`, `build_bezocht.py`, `index.html`.

---

## pocket_count.html

### 1 · snapSegs-merge
Ways die net buiten de verse Overpass-cirkel vallen verloren hun snap-kandidatuur bij elke re-fetch. Opgelost via een cumulatieve kandidatenset.

- `SNAP_SEGS_RADIUS = Math.round(SNAP_ROAD_FETCH_RADIUS * 1.6)` (= 400 m). Afgeleid: fetch-radius + max drift vóór re-fetch.
- `snapElementsNear(lat, lon)` — bouwt de seg-input uit het cumulatieve `snapElements`, gefilterd op nabijheid. Het huidige anker altijd meegenomen ongeacht knoopafstand.
- Fetch-volgorde omgedraaid: eerst accumuleren in `snapElements` + `snapAdjacency`, dán `snapBuildSegs` aanroepen. `snapBuildSegs` herprojecteert alles tegen het actuele origin → geen frame-menging.
- Fetch-event in `_snap_trace.csv` logt nu `n_el:X|n_kept:Y|n_segs:Z`.

### 2 · Platform-robuuste download
`<a download>` + `.click()` faalde op iOS Safari (user-gesture verlopen na de async zip-generatie).

- `saveBlob(blob, filename, mime)` — probeert `navigator.canShare({files})` → `navigator.share` (iOS-pad: deelblad → "Bewaar in Bestanden"), valt terug op `<a download>` (desktop/Android).
- Preview-overlay heeft een expliciete **"ZIP opslaan"**-knop (`#preview-save` → `savePreviewZip()`) als vangnet — elke tik is een verse user-gesture.
- Preview verschijnt nu bij blob-afronding i.p.v. via een blinde `setTimeout`.
- Generiek geschreven voor hergebruik in de andere apps (zie backlog).

### 3 · Trajectorie-hertoekenning (`reassignTrajectory`)
De live snap is plakkerig (anchoring tempert jitter maar kan tikken aan een verre anker-way toekennen) en kent de toekomst niet. Vlak vóór de ZIP-bouw, als de hele trajectorie bekend is, worden tikken én aanwezigheid gecorrigeerd.

**Mechanisme:**
1. Topologie-eerste Viterbi over de volledige `routeLog`. Emissie: `½(d/σ)²`, σ = `max(5, fix.acc)`, zoekradius 40 m. Transitie via de bestaande `snapAdjacency` (exacte node-ID's). Hop 0 = gratis, hop 1 (gedeelde knoop) = 4, hop 2 = 12, verder = verboden.
2. Per fix wordt via `splitWayIntoSegments` het juiste segment bepaald (zelfde segmentatie als de export).
3. `routeLog[i].wayId/segIdx` en `telHistory[i].wayId/segIdx` worden in place gecorrigeerd. Ruwe lat/lon ongemoeid.
4. Tik erft way + segIdx van de fix die qua tijd het dichtst ligt → tik en aanwezigheid landen gegarandeerd op hetzelfde (way, segment) → geen lege weekprofiel-cellen.

**Gevolg:** `_telregels.csv`, `_gps.csv` én `_bezocht.csv` zijn meteen bij de bron consistent; alle CSV-builders lezen de gecorrigeerde velden.

**Geverifieerd op veldsessie `20260529_162037_xax_pkt`:** 33 tikken die op service-ways hingen → voetgangers-ways. Kopspijker (OSM: Nieuwstraat, way 305567874) krijgt 24 tikken. Alle 99 tikken behouden. 0 orphan-segmenten.

### 4 · Volledig tweetalig (NL/EN)
De VS Code-versie had al een taalschakelaar (`toggleLang`, `TRANSLATIONS`, `t()`, `applyLang()`). Aangevuld en gesloten:

- Ontbrekende keys toegevoegd: `btnStop`, `btnStart`, `undo`, `statMax` (Max p/m).
- `#lbl-max` id toegevoegd aan de Max p/m-stat zodat `applyLang` 'm kan bereiken.
- `applyLang()` wordt nu bij het laden aangeroepen (niet alleen bij de toggle) — het vertaalsysteem is de enige bron van waarheid.
- Beide talen hebben exact dezelfde 23 keys. Alle 22 element-id's die `applyLang` raakt zijn gecontroleerd aanwezig in de DOM.

---

## telrapport.html

### Drukteklassen — centrale `INTENSITEIT`-definitie
`p/m·u` was voor opdrachtgevers onleesbaar en was bovendien inconsistent (kaart kleurde op p/m, weekprofiel op p/m·u).

**Eén centrale definitie** stuurt nu alle kleuringen en labels:

```
const INTENSITEIT = [
  { max:  10, label: 'Rustig',       kleur: '#4575b4' },  // blauw
  { max:  30, label: 'Matig',        kleur: '#74add1' },  // lichtblauw
  { max:  60, label: 'Druk',         kleur: '#fee090' },  // geel
  { max: 100, label: 'Zeer druk',    kleur: '#f46d43' },  // oranje
  { max: Inf, label: 'Extreem druk', kleur: '#d73027' }   // rood
];
```

Blauw→geel→rood is kleurenblind-veilig (de oude rood-groen was dat niet voor ~8% van de mannen).

- `intensityClass(pmu)` — de enige plek waar kleur + label wordt bepaald.
- `pmuForKey(key)` — berekent p/m·u voor een segment via `visitData` (zelfde formule als weekprofiel).
- **Kaart:** pocket-segmenten kleuren nu op p/m·u via `pmuForKey`, niet meer op p/m. Hover-tooltip toont naam + tikken + klasse + getal.
- **Weekprofiel:** `cellStyle` en legenda via `intensityClass`. Cel-tooltips tonen de klassenaam.
- **Sessietabel:** nieuwe kolom "klasse" naast p/m·u, in klassekleur.
- **Sidebar-legenda:** nieuwe `#legend-pocket` block met de vijf klassen, zichtbaar zodra er een pocket-sessie geladen is.
- Tikken blijven overal zichtbaar — kleur is de interpretatie-laag, het getal het ruwe feit.

---

## telrapport_viterbi.html (testversie)

- `buildWayAdjacency` gebruikt nu exacte gedeelde-vertex-matching (6 decimalen = functioneel gelijk aan node-ID matching). Geeft 537 exacte junctions vs 555 met 2 m-tolerantie — de 18 extra waren false merges.
- Junction-aware penalty: bij een hop-1-overstap straf proportioneel aan afstand tot de gedeelde knoop (`junctionWeight = 0.08`).
- **Tik-hertoekenning (Optie A):** knop "tikken hertoekennen" muteert `wayData.sessions` + herbouwt `visitData` uit de trajectorie. `fixSegKey` gedeeld tussen tikken en aanwezigheid → gegarandeerd zelfde segment → weekprofiel consistent. `recolorAll()` + `drawClusters()` tekenen bij. "wissen" herstelt origineel uit `reassignBackup`.

---

## snaptrace.html (standalone)

- `buildAdjacency` registreert nu ook junction-coördinaten per way-paar.
- Junction-aware penalty in `matchTopo` identiek aan telrapport_viterbi.
- Overige architectuur ongewijzigd.

---

## Bekende grenzen (vastgesteld deze sessie)

**Open voetgangersvlakken.** Aangrenzende pedestrian-ways delen knopen (ze trianguleren een vlak) — "welke lijn" is daar geen scherpe vraag. De matcher geeft 0 foute wisselingen op echte straten, maar ~11 op het plein; dat is de irreducibele rest.

**Roltrappen.** `highway=steps` valt in 2D samen met de loopruimte ernaast. Geen afstandsmaat onderscheidt dit. Echte oplossing vereist hoogtesignaal (barometer) of handmatige markering.

**Tweetaligheid in andere apps.** `parkeertelling`, `fietsparkeren`, `capaciteitstelling` en `traffic_counter` zijn nog eentalig Nederlands.

---

## Backlog / vervolgstappen

- **`saveBlob`-migratie** naar parkeertelling, fietsparkeren, capaciteitstelling, traffic_counter. Zelfde fragiele `<a download>`-patroon als pocket had. Per app apart aanpakken — elke app heeft eigen export-knoppen.
- **snapSegs-fix migreren** naar parkeertelling/fietsparkeren/capaciteitstelling. Migratieplan in `snap_methodology.html` §9.
- **Tweetaligheid overige apps.** Pocket als sjabloon.
- **capaciteitstelling header** leest nog 'PARKEERTELLING' → 'CAPACITEITSTELLING'.
- **Hoogte-signaal** voor roltrap/trap-detectie. `altitude`/`altitudeAccuracy` uit Geolocation API toevoegen aan `routeLog` — roltrap herkenbaar aan hoogteverandering, los van horizontale positie.
- **Vlak-snappen voor pleinen.** `area`/`pedestrian`-polygon als snap-doel i.p.v. lijn.
- **`snap_methodology.html`** bijwerken: nieuwe snap-paden, `reassignTrajectory`, SNAP_SEGS_RADIUS.
- **`zip_format_reference.html`** bijwerken: notitie dat `_telregels.csv`/`_bezocht.csv` vanaf 2.8 trajectorie-gecorrigeerd zijn.
- **Naamgeving opruimen:** `wid` (lokale var) naast `wayId` (property) — consistent in gebruik, rommelig in stijl. Geen bug.
- **Dagboek-updates** (stonden al op de lijst): tijdlijn tag-klik toont direct volledige tekst; Verkennen-dropdown → drie losse knoppen; projecten.php opschonen; projectnotities per code.

---

## Verificatie

Alle JS gevalideerd met `node --check`. `reassignTrajectory` end-to-end getest op `20260529_162037_xax_pkt`: 99/99 tikken behouden, 0 orphan-segmenten, Nieuwstraat 24 tikken, service-ways 0. Tweetaligheid: 23 keys NL = 23 keys EN, alle 22 DOM-id's aanwezig. `intensityClass` op alle 10 grenswaarden correct geverifieerd. Overpass-fetch sandbox-geblokkeerd maar hergebruikt pocket's bewezen patroon.
