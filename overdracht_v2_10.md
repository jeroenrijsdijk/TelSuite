# TrafficCounterSuite v2.10 — Overdracht

Een **fundering- en harmonisatierelease**. Geen nieuwe veldfeatures, maar het gelijktrekken van de drie GPS-snappende parkeer-apps op één gedeeld patroon, plus een stille inhaalslag op `capaciteitstelling` (die alle v2.9-parkeerfixes miste en daardoor veldgegevens kon verliezen). Daarnaast een paar opschoonpunten in pocket/README, en een onderzoeksbevinding over de transect-teller die als bewust beslispunt is vastgelegd.

De leidende gedachte: vóórdat er weer iets ambitieus aan de snap-engine gebeurt, moeten de apps niet meer in vier licht-verschillende dialecten praten. Na deze release is de `snap`-namespace én de `saveBlob`-helper **byte-identiek** over `parkeertelling`, `fietsparkeren` en `capaciteitstelling`.

---

## Gewijzigde bestanden

| Bestand | Status | Kern van de wijziging |
|---|---|---|
| `pocket_count.html` | ✦ bijgewerkt | `wid`→`wayId` consistent gemaakt (interne JS); `osm_way_id`-contract ongemoeid |
| `README.md` | ✦ bijgewerkt | `kruispunttelling.html` uit de tooltabel (app is uit de suite) |
| `parkeertelling.html` | ✦ bijgewerkt | **referentie-migratie**: `snap`-namespace, `saveBlob`, kompas-in-Start, planning-duplicaat weg |
| `fietsparkeren.html` | ✦ bijgewerkt | gerepliceerd van parkeertelling (snap-literal + saveBlob byte-identiek) |
| `capaciteitstelling.html` | ✦ bijgewerkt | harmonisatie **+ volledige v2.9-datasafety-inhaalslag** |

Ongewijzigd: `traffic_counter.html`, `traffic_counter_transect.html`, `traffic_counter_help.html`, `telplanning.html`, `telrapport.html`, `telrapport_viterbi.html`, `snaptrace.html`, `snap_methodology.html`, `zip_format_reference.html`, `build_bezocht.py`, `index.html`, `planningen/*`.

---

## Het geharmoniseerde patroon

Drie zaken zijn nu identiek geïmplementeerd over de drie parkeer-apps:

1. **`snap`-namespace** — alle losse road-snap-state in één benoemd object met schone veldnamen:
   `snap.networkElements`, `snap.segs`, `snap.cacheLat`, `snap.cacheLon`, `snap.status`, `snap.fetchTimer`, `snap.visitedSegs`, `snap.history`, `snap.stable`. De veldnamen verschillen bewust van de oude globals, zodat een latere zoek-vervang nooit per ongeluk de literal-keys raakt. Geen closures/getters — net als pocket bewust een platte namespace (verbergen levert voor een veldtool weinig op).
2. **`saveBlob(blob, filename, mime)`** — deel-of-download-helper, signatuur identiek aan pocket. iOS: systeem-deelvenster wanneer mogelijk; desktop/Android: download-link. De drie tussentijdse exports (`exportCSV`/`exportGPX`/`exportMapCanvas`) lopen er nu doorheen → óók die krijgen op iOS het deelvenster.
3. **Kompas in de Start-gesture** — `if (!compassActive) requestCompass();` in `startSession`. iOS staat `DeviceOrientationEvent.requestPermission()` alleen toe binnen een user-gesture; `startSession` draait in de onclick van `btnStart`, dus dat is geldig. De guard voorkomt dubbele listeners. `btnKompas` blijft als fallback (her-aanvraag na 'geweigerd'). *Letterlijk automatisch bij laden kan niet op iOS — dit is het maximaal haalbare: de losse stap is weg.*

Bewust **niet** door `saveBlob` gejaagd: de ZIP-export. Die heeft een eigen `finalizeExport`-koppeling (herstelkopie pas wissen ná bevestigde opslag) die de 3-param `saveBlob` niet kan dragen zonder een 4e callback-param — wat de gedeelde signatuur zou breken. De ZIP houdt dus z'n expliciete share+finalize-structuur.

---

## pocket_count.html

`wid`→`wayId` — 35 standalone identifiers (lus-vars, object-keys, lokale vars) naar één consistente naam. `osm_way_id` (de KNIME-join-kolom) is het externe contract en bleef ongemoeid (4 sites). `node --check` schoon.

## README.md

De `kruispunttelling.html`-regel uit de tooltabel; dat was de enige levende verwijzing (geen dode link in `index.html`; archief-overdrachten als historie ongemoeid).

## parkeertelling.html — referentie-migratie

1. **Lokale `snap`→`hit`** in `onPosition` — de botsende result-var weggehaald zodat de namespace-naam vrijkwam.
2. **`snap`-namespace** — 9 globals samengebracht (~74 sites omgezet; alle `snap.X` resolven 1-op-1 op de literal).
3. **`saveBlob`** geport; de drie tussentijdse exports erdoorheen.
4. **Kompas-in-Start** + `btnKompas`-fallback.
5. **Opschoning**: dubbele `planningWegen`/`planningLayer`-declaratie gededupliceerd.

## fietsparkeren.html — replicatie

Zelfde vier ingrepen. Geen planning-duplicaat (had fiets niet), geen cap-lagen in het blok (auto-specifiek). Bewezen: `snap`-literal én `saveBlob` zijn **byte-identiek** aan parkeertelling.

## capaciteitstelling.html — harmonisatie + datasafety

Bij het migreren bleek capaciteit een **pré-v2.9-app**: afgesplitst vóór de hele v2.9-parkeerronde, dus álle datasafety-fixes ontbraken. Naast de standaard harmonisatie (snap-namespace, saveBlob, kompas-in-Start — snap-literal byte-identiek aan de andere twee) zijn de ontbrekende v2.9-fixes alsnog doorgevoerd:

- **`exportCSV` wiste de herstelkopie** (`clearSession()`) bij een tussenexport → verwijderd.
- **`exportZip` wiste onvoorwaardelijk** ná `generateAsync`, óók bij annuleren van het deelvenster → vervangen door de `finalizeExport`-koppeling (clearSession alleen na bevestigde opslag, conform parkeertelling).
- **`safetyDownload`** triggerde nog `exportCSV()`+`exportMapCanvas()` bij scherm-uit/app-switch → nu alleen `saveSession()`.
- **GPX `<n>`→`<name>`** (was ongeldige GPX) + app-naam "Capaciteitstelling".
- **Verkeerde `'parkeertelling_'`-bestandsprefixes** → `'capaciteitstelling_'` (exportCSV/GPX/MapCanvas + `exportZip`-`sid`).
- **`LS_KEY`-botsing**: capaciteit deelde z'n localStorage-herstelsleutel mét parkeertelling (`'parkeertelling_sessie'`). Bij gebruik van beide apps overschreven hun herstelkopieën elkaar → eigen `'capaciteitstelling_sessie'`.
- Dode legacy-functie `buildCsvString` gesignaleerd (nergens aangeroepen) — bewust niet verwijderd, alleen gedocumenteerd.

**Bewust uitgesteld voor capaciteit** (zie backlog): cumulatieve-snap-port en de header-/terrein-schema-fix — die tweede raakt het KNIME-schema en wacht op een schema-besluit.

---

## Onderzocht / vastgelegd

### Transect-teller (`traffic_counter_transect.html`) — snap-status
Onderzocht vóór de zip. Bevinding: de transect-teller snapt **wél**, maar met de oudste en lichtste van drie engines (eigen naamgeving: `snapNearestWay`/`snapClosest`/`snapToXY`/`snapBuildSegs`/`snapFetchNetwork`, losse `snapCacheLat/Lon`/`snapSegs`/`snapReady`). Elke telling krijgt live een `wayId`+`osmName` via nearest-way snap. Drie gaten t.o.v. de rest:

1. **`snapSegs` wordt per fetch volledig overschreven** (niet geaccumuleerd) → de v2.9-kandidaat-dropout-zwakte leeft hier nog.
2. **Geen offline `reassignTrajectory`** — terwijl de teller wél een `routeLog` logt. Mis-snaps op kruispunten blijven dus permanent fout; pocket trekt die achteraf recht.
3. **Derde naamgevingslijn** — niet in de `snap`-namespace.

Bewust níét in deze release meegenomen; het is een eigen engine-project (een `reassignTrajectory`-port is géén drop-in: pocket's versie leunt op een adjacency-/topologie-laag die de transect-engine mist). Zie backlog.

### Afgehandeld / gesloten uit v2.9-backlog
- **Harmonisatie** (`saveBlob` + `snap`-namespace naar de parkeer-apps): afgerond voor de drie GPS-apps. `traffic_counter.html` is de kale tally-tool zonder snap → n.v.t.
- **README**: `kruispunttelling`-verwijzing opgeschoond.
- **`wid`/`wayId`**: gelijkgetrokken in pocket (de enige app waar ze door elkaar liepen; de parkeer-apps waren al schoon).

---

## Backlog (open)

### Capaciteit (vervolg)
- **Cumulatieve-snap-port** — `snap.networkElements` wordt nog per fetch overschreven i.p.v. geaccumuleerd (mist `elementsNear`/dedup-op-id). Engine-werk.
- **Header-/terrein-schema** — terrein-entries (7 kol.: `sessie_id;osm_way_id;naam;zijde;type;n;ts`) worden onder de 8-koloms straten-header in `_capaciteit.csv` geplakt. *Beslispunt:* volgen ze de straten-kolommen (`…;soort;capaciteit;eerste;laatste`), of horen ze in een eigen `_terrein.csv` met eigen header? Raakt KNIME — wacht op schema-besluit.

### Transect-teller
- Goedkoop: cumulatieve-snap-fix (zoals in de parkeer-apps) + `snap`-namespace-harmonisatie.
- Ambitieus: `reassignTrajectory`-port (offline junction-correctie); vereist eerst een adjacency-/topologie-laag.

### Langer lopend (uit eerdere sessies)
- **Hoogtesignaal** (`altitude`/`altitudeAccuracy`) voor roltrap/trap-detectie — de enige uitweg uit de verticale-samenval-grens. Platform-kanttekening: web-`altitude` is GPS-afgeleid en binnen vaak ruis; barometer onbereikbaar. Eerst een meet-probe (altitude áchteraan in `_snap_trace.csv` loggen, één Centrumpassage-walk) vóór er een feature op wordt gebouwd.
- **Vlak-snappen** voor open pleinen (`area`/`pedestrian`-polygonen i.p.v. lijnen) — grotere architectuur-vraag (een punt ín een polygoon heeft geen "zijde").
- **Moving-observer-decompositie** (Wardrop & Charlesworth) voor pocket — oncoming-flow vs. stationaire dichtheid scheiden m.b.v. GPS-snelheid.
- Kleinere parkeer-punten (v2.9-scan #10): visited-highlight persisteren, dubbele snap per fix, aggregatie op `osmName` i.p.v. geocode-label.
- Diversen pocket/telplanning: adaptieve segmentlengte, IndexedDB-relay pocket→telrapport, "Nu"-knop telplanning, weekprofiel-popup auto-refresh.

---

## Validatie-discipline (deze release)
Per app na elke ingreep: JS geëxtraheerd + `node --check`, HTML-tagbalans (script/style/div), en een consistentie-check dat élke `snap.X`-toegang 1-op-1 resolvet op een gedefinieerde literal-key. Harmonisatie hard bewezen via byte-diff van `snap`-literal en `saveBlob` tussen de drie apps.
