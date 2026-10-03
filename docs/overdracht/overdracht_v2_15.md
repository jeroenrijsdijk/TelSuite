# TrafficCounterSuite v2.15 — Overdracht

Drie wijzigingen plus een veld-bugfix. **(1) Telrapport** krijgt een **gegroepeerde sessielijst**: laad gerust alles in, en filter daarna per soort telling (winkelstraat, fietsparkeren, autoparkeren, …) met een kop-toggle per groep. Geen nieuwe schakelaar bovenop de lijst, maar het bestaande solo-gebaar opgetild van één sessie naar een hele soort. **(2) Telrapport** accepteert nu ook een **gesleepte map**: alle ZIPs/CSVs erin (recursief, incl. submappen) worden één voor één ingeladen — plus een "kies een map"-knop als desktop-fallback. **(3) De vier export-tools** verpakken hun ZIP nu met **maximale compressie** (DEFLATE-9 i.p.v. STORE) — op een echte winkelstraat-telling 83% kleiner. **(4) Android-download-fix** (volgde uit (3)): de tragere compressie legde een latente `saveBlob`-bug bloot waardoor de download op Android stil faalde. **(5) traffic_counter GPS-fix**: het startpunt vergrendelde op de eerste fix ≤25m (vaak nog tientallen meters naast → verkeerde straatnaam); nu een inloop-tijd + convergentie-detectie zodat de béste fix wordt genomen.

In de geest van v2.12–v2.14: additief, maar **de-drift waar het kan**. De groepering rijdt volledig mee op de al bestaande `visible`-vlag en `applySessionVisibility()` — er komt geen tweede zichtbaarheidsmechaniek bij. De iconen-ladder die voorheen inline in `renderSessions` stond, is samengetrokken tot één bron (`sessionGroup()`), die nu zowel het rij-icoon als de groepskop voedt.

---

## Gewijzigde bestanden

| Bestand | Status | Kern van de wijziging |
|---|---|---|
| `telrapport.html` | ✦ bijgewerkt | (a) Sessielijst gegroepeerd per soort telling met kop-toggle (oog = groep tonen/verbergen, caret = in-/uitklappen); `sessionGroup()`/`makeSessionRow()`/`syncGroupHeads()`. (b) **Map-drop**: gesleepte mappen recursief uitgelezen (File-and-Directory-Entries-API) en sequentieel ingeladen via gedeelde `ingestFiles()`; "kies een map"-knop (`webkitdirectory`) als desktop-fallback |
| `pocket_count.html` · `parkeertelling.html` · `fietsparkeren.html` · `capaciteitstelling.html` | ✦ bijgewerkt | (a) ZIP-export op maximale compressie: `generateAsync` krijgt `compression:'DEFLATE', compressionOptions:{level:9}` (was impliciet STORE). (b) **`saveBlob` Android-fix**: deelblad alleen nog op iOS (Android kreeg het ook, met verlopen-gesture-risico en lege `.catch`); download-anker hangt nu in de DOM |
| `traffic_counter.html` | ✦ bijgewerkt | **Startpunt-GPS** wacht nu op een ingelopen fix i.p.v. te vergrendelen op de eerste ≤25m: minimale inloop-tijd (`GPS_MIN_SETTLE_MS`) + convergentie-detectie (`GPS_CONVERGE_MS`), strakkere accept-drempel (20m), vroege vergrendeling alleen bij een uitstekende fix (≤8m); live "settling… (Ns)"-feedback |
| `README.md` | ✦ bijgewerkt | Versie → v2.15; telrapport-regel + release-noot |

Ongewijzigd: alle overige bestanden (`telplanning.html`, `traffic_counter.html`, `snaptrace.html`, indexen, helpers, `planningen/*`, `_archief/*`). **Geen schema- of ZIP-structuurwijziging** — de compressie-wijziging raakt alleen de opslagmethode binnen de ZIP, niet de bestandsset of de CSV-schema's. KNIME-readers en de downstream-pipeline blijven ongemoeid (elke unzip-tool pakt DEFLATE net zo transparant uit als STORE).

---

## Het idee

De sessielijst was een platte, omgekeerd-gesorteerde rij. Bij veel geladen tellingen werd "alleen de winkelstraattellingen zien" een kwestie van handmatig sessies aan/uit klikken. Maar telrapport *wéét* per sessie al welke soort het is — de `app_type` (+ `modus` voor pocket) bepaalt al het rij-icoon. Die kennis was alleen niet als filter ontsloten.

**Sleutel = soort, schoon afleidbaar.** Binnen de telrapport-pijplijn schrijft niets anders dan `parkeertelling.html` de `app_type` `'auto'`, en niets anders dan `fietsparkeren.html` de `'fiets'`. De statische `traffic_counter.html` voedt geen `app_type` in deze pijplijn. Dus elke groepssleutel verwijst schoon naar precies één soort meting — geen botsing tussen fietsparkeren en fiets-doorstroom. De enige split die `app_type` zelf niet maakt is binnen `pocket`, waar `modus` (winkelstraat / transect / simpel) het onderscheid levert — precies de split die de iconenregel al maakte.

**Groepssleutels** (volgorde = `GROUP_ORDER`):
`auto` 🚗 Autoparkeren · `fiets` 🚲 Fietsparkeren · `capaciteit` 🅿 Capaciteit · `pocket:winkelstraat` 🛍️ Winkelstraat · `pocket:transect` ↔️ Transect (pocket) · `pocket:simpel` 📷 Pocket · `transect` 🚶 Transect · `standstill` 📍 Stilstaand. Onbekende soorten vallen terug op de 🚲-tak en sorteren achteraan.

**Datadreven.** `renderSessions()` groepeert de geladen sessies en toont alleen de soorten die *daadwerkelijk* aanwezig zijn. Een toekomstig teltype hoeft alleen een tak in `sessionGroup()` te krijgen; de lijst, het filter en de oog-status volgen vanzelf.

---

## Wat er precies is gebeurd

**`sessionGroup(s) → {key, icon, label}`** — nieuwe enkele bron voor "soort telling". Vervangt de inline icoon-ladder in `renderSessions` (die is nu een aanroep) en voedt ook de groepskoppen. Eén plek om te wijzigen i.p.v. twee.

**`makeSessionRow(sid) → HTMLElement`** — de rij-bouw is 1:1 uit de oude `forEach` gelicht naar een functie. Markup, classes en het `title`-gebaar-label zijn ongewijzigd, zodat de bestaande delegatie (klik = aan/uit, shift = alles, rechtsklik = solo) onaangeroerd blijft werken — óók binnen een groep.

**`renderSessions()`** — bouwt nu per soort een `.session-group` met een `.session-group-head` (caret · icoon · label · aantal · oog) en daaronder de rijen. Ingeklapte staat leeft in een module-`Set` `collapsedGroups` en wordt bij elke render hertoegepast (de lijst herbouwt bij elke nieuwe lading, niet bij een losse toggle).

**`syncGroupHeads()`** — herberekent de oog-status van elke kop puur uit de data: ● alles aan, ○ alles uit, ◐ gemengd (met `n/total`-tooltip). Aangeroepen aan het eind van `renderSessions`, na een groep-toggle, en in de bestaande klik-/contextmenu-handlers — zodat een individuele toggle de groepskop meteen laat meebewegen.

**`toggleGroupVisibility(key)`** — zet de hele soort aan als er nog iets uit staat, anders alles uit; per sessie via de bestaande `applySessionVisibility`, gevolgd door `recolorAll/updateStats/syncGroupHeads`.

**`toggleGroupCollapse(key)`** — puur visueel in-/uitklappen (raakt `visible` niet aan); rijen verdwijnen via `.session-group.collapsed .session-row { display:none }`.

**Besturing** — één extra gedelegeerde click-listener op `#sessions-list`: een tik op `.sg-eye` toggelt zichtbaarheid (en `stopPropagation` zodat de kop niet óók inklapt), een tik elders op de kop klapt in/uit. De listener staat los van de session-row-handler, die in een kop simpelweg geen `.session-row` vindt en vroeg returnt.

**iOS-discipline gevolgd:** alle nieuwe CSS in het `<style>`-blok (niet in JS); de kop en het oog zijn `<div>`/`<span>` met click-handlers, geen `<button>` zonder onclick — conform de bekende touch-absorptie-valkuil. Het oog is een royaal tikdoel (28×26 px).

---

## Deel 2 — Map-drop in telrapport

De dropzone las een drop tot nu toe via `dataTransfer.files` — prima voor losse bestanden, maar een **map** komt daar niet als inhoud binnen. Een gesleepte map zit in `dataTransfer.items` en moet via de **File-and-Directory-Entries-API** (`webkitGetAsEntry`) recursief worden uitgelezen.

**Aanpak.** De drop-handler snapshot de entries **synchroon** uit het event (items/entries verlopen na de event-tick), en leest daarna async door:
- `readAllEntries(reader)` — leest `readEntries()` in batches door tot leeg. Dit is de klassieke valkuil: `readEntries` levert max ~100 entries per aanroep, dus één aanroep mist de rest bij grote mappen. De loop dekt dat af.
- `walkEntry(entry)` — file → `[File]`; directory → recursief de kinderen; anders leeg.
- `gatherFiles(entries)` — platgeslagen lijst van álle files onder de drop (mappen én losse bestanden door elkaar werken).

Alles komt samen in **`ingestFiles(files)`**: filtert op `.zip`/`.csv`, sorteert op naam (voorspelbare volgorde), en laadt **sequentieel** met `await loadFile(f)` — `loadFile` geeft de zip/csv-promise terug, dus dit serialiseert echt en voorkomt tientallen gelijktijdige `JSZip.loadAsync`-loads bij een volle map. De dropzone-tekst toont intussen `⏳ laden… i/m`. De drie invoerkanalen (drop, bestandskiezer, mapkiezer) lopen nu alle drie door deze ene `ingestFiles` — de oude losse `forEach(loadFile)` is eruit.

**Desktop-fallback.** Een tweede, verborgen `<input webkitdirectory>` met een "kies een map…"-link onder de dropzone; `webkitdirectory` levert een platte FileList van de hele map (geen recursie nodig op dat pad). Voor browsers zónder entries-API valt de drop terug op `dataTransfer.files`.

**Veld-/platformnoot.** Map-slepen en `webkitdirectory` zijn **desktop**-features; iOS Safari kent ze niet. Dat is hier passend — telrapport is de analyse-tool op de computer (waar je veel ZIPs samenbrengt voor het weekprofiel), niet de veld-app op de telefoon. De per-bestand-laadpaden (`loadZip`/`loadStandStillCsv`) zijn ongewijzigd.

---

## Deel 3 — Maximale ZIP-compressie bij export

De vier tools die een sessie-ZIP wegschrijven (`pocket_count`, `parkeertelling`, `fietsparkeren`, `capaciteitstelling`) bouwen die met JSZip 3.10.1 en riepen `generateAsync({type:'blob'})` aan — zónder compressie-optie. JSZip's default is dan **STORE**: de CSV's, GPX en PNG gaan ongecomprimeerd de ZIP in. Voor tekst (CSV/GPX) is dat zonde; die comprimeren juist enorm.

**Fix.** Elke `generateAsync` krijgt nu `compression:'DEFLATE', compressionOptions:{level:9}` — maximale deflate. Op een echte winkelstraat-telling (`20260620_134040_bbm_pkt`, 6 bestanden, 235 KB) levert dat **40 KB op — 83% kleiner**; de zwaartepunten `netwerk.csv` (72 KB) en `snap_trace.csv` (130 KB) zijn vrijwel pure tekst en krimpen het hardst. Een ingebedde PNG (in tellingen die er een hebben) krimpt nauwelijks — die is al deflate-gecomprimeerd — maar dat is hooguit neutraal; de tekst domineert de winst.

Globale instelling, geen per-bestand-compressie: simpeler en onderhoudbaarder, en de PNG-uitzondering is het niet waard apart te regelen. Niveau 9 op een paar honderd KB tekst is op de telefoon verwaarloosbaar qua tijd (milliseconden). De ZIP-inhoud, bestandsnamen en CSV-schema's blijven byte-voor-byte identiek; alleen de opslagmethode in de container verandert.

---



- Inline JS geëxtraheerd + `node --check`: groen.
- Tag-balans: `div` 99/99 (ongewijzigd — nieuwe DOM komt via `createElement`/`innerHTML`, niet als statische tags), `script` 4/4, `style` 1/1, `details` 4/4.
- **Groep-logica apart unit-getest** met een gemengde mock-lading (winkelstraat ×2, fietsparkeren, autoparkeren ×2 waarvan één uit, capaciteit, transect-pocket, simpel-pocket, onbekend type): `sessionGroup` sleutels/labels/iconen correct; `GROUP_ORDER`-sortering correct; oog-status correct (autoparkeren [aan,uit] → ◐ gemengd, rest ● aan); toggle-target correct ("iets aan → hele groep uit; niets aan → hele groep aan"); onbekend type → 🚲-fallback achteraan.
- Twee echte winkelstraat-ZIPs (`app_type=pocket`, `modus=winkelstraat`) groeperen onder 🛍️ Winkelstraat.
- **Compressie:** vier tools na de patch `node --check` groen; export-winst gemeten op de echte bbm-ZIP (STORE 235 KB → DEFLATE-9 40 KB, 83%).
- **Map-drop apart unit-getest** met een gemockte mappenboom (root + geneste submap + lege submap, `readEntries` in meerdere batches): recursie verzamelt alle bestanden, lege submap wordt overgeslagen, de batch-loop leest volledig door, en het zip/csv-filter + naam-sortering houdt precies de 4 laadbare bestanden over (3 zip + 1 csv, .txt/.png eruit). Tag-balans na de HTML-toevoeging: `div` 100/100.
- **Android-download-fix:** vier tools `node --check` groen na de `saveBlob`-vervanging; geverifieerd dat `saveBlob` in pocket het hoofd-zip-pad voedt (auto + preview-knop) en in de andere drie alleen de losse csv/gpx/png-exports (hoofd-zip daar via eigen download-fallback, ongemoeid).

---

## Deel 4 — Android-download-fix (saveBlob)

**Symptoom.** In pocket op Android werd de ZIP niet gedownload, en de "ZIP opslaan"-knop in de preview deed niets. De andere drie tools hadden hier géén klacht.

**Oorzaak — twee dingen die samenkwamen.** `saveBlob` koos het deelblad-pad puur op `if (navigator.canShare)` — maar dat bestaat óók op Android. Dus Android ging via `navigator.share({files})`, en dat eist een *levende* user-gesture. Door de tragere DEFLATE-9 (Deel 3) was die gesture verlopen tegen de tijd dat de blob klaar was → `share` faalde → de `.catch` was **leeg** → stil niets. De compressie was de trigger, de lege `.catch` de eigenlijke bug. En zelfs het download-link-vangnet was broos: het `<a>`-anker werd niet aan de DOM gehangen, en Android negeert een `click()` op een los anker.

Waarom alleen pocket: pocket's *hoofd*-zip-export loopt via `saveBlob`. Parkeer/fiets/capaciteit gebruiken voor hun hoofd-zip een ánder pad dat bij een mislukte share terugvalt op `downloadBlob` — dat werkte dus al. Hun `saveBlob` wordt alleen voor losse csv/gpx/png-exports gebruikt; díé hadden stilletjes dezelfde bug.

**Fix (alle vier, één gedeeld patroon).** `saveBlob`: deelblad **alleen op iOS** (`/iP(hone|ad|od)/` + iPad-op-desktop-UA); Android/desktop → download-link met het anker **in de DOM** (`appendChild` → `click` → opruimen); geen stille `.catch` meer als enige uitweg. Pocket's preview-knop (verse gesture) downloadt nu betrouwbaar op Android; de losse-bestand-exports van de andere drie zijn meteen mee opgeknapt.



---

## Deel 5 — traffic_counter: startpunt wacht op een ingelopen GPS-fix

**Symptoom.** Het startpunt lag soms te ver van de werkelijke locatie — soms zelfs de verkeerde straatnaam (reverse-geocode op een punt dat een halve straat naast zat).

**Oorzaak.** `requestGPS()` draait een `watchPosition` en vergrendelde op de **eerste** fix met `accuracy ≤ 25m`. Maar de eerste sub-drempel-fix is vaak nog aan het inlopen; de gerapporteerde nauwkeurigheid is een schatting en de echte fout kan groter zijn. Een paar seconden langer wachten laat de GPS convergeren (van ~25m naar ~8–12m) en stabiliseert de positie.

**Fix.** Vergrendel niet meer op de eerste hit, maar volgens prioriteit: (1) een **uitstekende** fix (≤8m) vergrendelt meteen na een korte bevestiging (≥2,5s); anders (2) na een **minimale inloop-tijd** (8s) zodra de beste fix ≤20m is; anders (3) zodra de nauwkeurigheid **~4s niet meer verbetert** (geconvergeerd) — neem dan de beste; anders (4) de harde 30s-bovengrens. Live feedback toont "+/-Xm, settling… (Ns)". De telling start onveranderd direct; alleen de fix loopt netjes in op de achtergrond.

**Gedrag (gesimuleerd):** normaal inlopen → vergrendelt ~9s @ ~9m (was ~3s @ ~22m); al-uitstekend (6m@3s) → meteen op 3s; plateau op 33m → 9s via convergentie (hangt niet); aanhoudend slecht → 30s-cap met de beste fix. De exacte bug-casus (eerste hit 22m@2s) levert nu ~10m i.p.v. 22m.

---

## Backlog (bijgewerkt)

### Afgerond deze release
- ~~telrapport: alle tellingen laden maar per soort kunnen filteren~~ → **gegroepeerde sessielijst met kop-toggle (Optie B)**.
- ~~telrapport: een hele map met ZIPs/CSVs in één keer kunnen inladen~~ → **map-drop (recursief) + mapkiezer, sequentieel via `ingestFiles`**.
- ~~export-ZIP op maximale compressie bij opslaan~~ → **DEFLATE-9 in de vier export-tools** (≈83% kleiner).
- ~~pocket Android: ZIP downloadt niet, "ZIP opslaan"-knop werkt niet~~ → **`saveBlob` Android-fix** (deelblad alleen iOS, download-anker in de DOM) in alle vier de export-tools.
- ~~traffic_counter: startpunt te ver weg / verkeerde straatnaam~~ → **GPS wacht op een ingelopen fix** (inloop-tijd + convergentie i.p.v. eerste ≤25m).

### Volgende voor de hand liggende stap (gebrainstormd, nog niet gebouwd)
- **Winkelstraat → passanten/uur (Moving Observer / Wardrop-Charlesworth).** De `tegemoet`-tik ís de meeting-count die de methode nodig heeft; `pocket_count.html` is hier al bewust voor opgezet (twee categorieën, GPS-lengte + -snelheid). Schatter per traversal: `q = 3600·M·v_p / (L + v_p·t)` → passanten/uur van de *tegengestelde* stroom. Eén vrije knop (`v_p`, voetgangerssnelheid, ~1,0 m/s in een drukke straat → band ±15%). `stilstaand` strikt apart houden als *verblijf*-metric, niet bij de stroom optellen.
  - One-way meet de tegen-stroom; **heen-en-terug** geeft de echte tweerichtings-footfall zonder extra knop (elke stroom is op precies één been "tegemoet"). Robuust tegen stoppen/tikken (L en t schuiven samen mee).
  - Open keuze: schatter draaien op wat er nú is (one-way → tegen-stroom + verblijf, met ×2-symmetrie eerlijk gevlagd), óf meteen de heen-en-terug-koppeling inbouwen.
  - Leefruimte: analyse-view, géén tool-/schemawijziging → geen KNIME-sign-off. Kan sectie in `telrapport.html` of een klein eigen viewertje.

### Beslissing nog open (carry-over)
- **Planning/Opdrachten-workflow** (telplanning): A (download-als-vangnet) vs B (lokale planning terugschrijven naar server). Aanbeveling: A.

### Wens voor latere release (schema — vereist KNIME-sign-off)
- Gebiedsnaam (`sessie_naam`) in `_sessie.csv` bewaren bij parkeer-/fietsexport, zodat een hertelling de oorspronkelijke naam i.p.v. de brondatum-proxy terughaalt.

### Geparkeerd / carry-over (ongewijzigd)
- **Sleep-correctie voor pocket-tellingen** (nieuw geïdentificeerd, dekkings-gat — géén regressie). De drag-correctie ("sleep-modus") is alleen voor `auto`/`fiets` gebouwd: `enterEditMode` heeft de grens `if (s.appType !== 'auto' && s.appType !== 'fiets') return;`, en het Correctie-paneel verschijnt alleen bij `(hasFiets||hasAuto)`. Pocket-punten (winkelstraat/transect/simpel) zijn dus nooit sleepbaar geweest. De `appType`-grens + paneel-zichtbaarheid verruimen is triviaal, **maar** pocket gebruikt een ánder snap-model dan auto/fiets (`snap_trace`, segmenten, de "irreducible remainder"-junctie uit v2.13): de snap-op-drag (`snap sleep-positie op gekozen way`) en de export-herbouw moeten het pocket-segmentmodel respecteren i.p.v. de auto/fiets-telregels. Dus: één-regel-guard, maar échte feature-werk eronder. Veldvalidatie vereist.
- Viterbi-merge → `_archief/viterbi_rig/`; ont-parkeren = simpel-only opt-in.
- Capaciteit: volledige cumulatieve-snap-port (`elementsNear` + `SNAP_SEGS_RADIUS` + highway-filter).
- telrapport: per-richting detailtabel (transect); winkelstraat-decompositie-view (zie Moving Observer hierboven).
- Pocket/telplanning: adaptieve segmentlengte, IndexedDB-relay pocket→telrapport, weekprofiel-popup auto-refresh, afwijkende-waarden-filter.
- Hoogtesignaal (`altitude`) voor roltrap/trap-detectie — eerst een meet-probe.
- Stand-still-locatie-aggregatie voor herhaalde tellingen op dezelfde plek.
- Off-netwerk/area-snapping; `snapSegs`-vervanging-bij-refetch (structureel).
- `traffic_counter_help.html`: optionele inline→class-refactor (~108 inline-styles).
