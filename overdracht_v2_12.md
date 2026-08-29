# TrafficCounterSuite v2.12 — Overdracht

Een **de-drift- + de-risk-release**. Geen nieuwe engine, geen datacontract-wijziging — de release is precies geworden waar de metingen ons brachten.

De aanleiding was een vraag over de twee telrapporten (`telrapport.html` vs `telrapport_viterbi.html`): Viterbi leek tikken beter toe te delen — naast elkaar laten of niet? Dat opende een veldvalidatie van de Viterbi-engine op echte ZIPs, en die validatie stuurde ons wég van twee grote algoritmische brokken (Viterbi mergen, off-netwerk-toestand bouwen) naar twee kleine, zekere winsten. De leidende gedachte: **drift wéghalen in plaats van een engine toevoegen.**

---

## Gewijzigde bestanden

| Bestand | Status | Kern van de wijziging |
|---|---|---|
| `pocket_count.html` | ✦ bijgewerkt | Overpass-filter gehoist naar `HIGHWAY_RE` + `track`/`bridleway` toegevoegd |
| `parkeertelling.html` | ✦ bijgewerkt | idem; tevens `steps`/`corridor` hersteld (stille drift) |
| `capaciteitstelling.html` | ✦ bijgewerkt | idem |
| `fietsparkeren.html` | ✦ bijgewerkt | idem |
| `traffic_counter_transect.html` | ✦ bijgewerkt | idem (filter); blijft op schijf, niet meer in index |
| `snaptrace.html` | ✦ bijgewerkt | `HIGHWAY_RE`-waarde geüpdatet (`track`/`bridleway`) |
| `index.html` | ✦ bijgewerkt | transect-kaart weg, Pocket = multi-modus, standalone-opmerking |
| `telrapport_viterbi.html` | → gearchiveerd | naar `_archief/` (fork geparkeerd) |
| `_archief/viterbi_rig/` | ✦ nieuw | `viterbi_engine.js` + 8 rig-scripts + `README.md` |

Ongewijzigd: `telrapport.html` (nu enige renderer), `traffic_counter.html`, `traffic_counter_help.html`, `telplanning.html`, `snap_methodology.html`, `zip_format_reference.html`, `build_bezocht.py`, `planningen/*`, `README.md`.

---

## Deel 1 — Overpass-filter de-drift (`HIGHWAY_RE`)

### Aanleiding (zia, echte transect-telling)
Een echte telling (`zia`) had 13/20 GPS-fixes "off-netwerk" op ~70 m van elke way — met *goede* nauwkeurigheid (mediaan 7 m) en een glad-kruipende afstand (74→78 m). Geen ruis, geen koude fix: een echt spoor langs een **bospad dat wél in OSM staat** (`highway=track`) maar niet werd opgehaald. De query haalt `path` volop op (85 stuks rond de walk), maar `track` zat niet in de filter → het pad werd nooit gedownload → niets om naar te snappen.

### De drift (zes plekken, al uiteengelopen)
De highway-filter stond zes keer in de suite, en was al gedrift:
- vier tools (`parkeertelling`, `capaciteitstelling`, `fietsparkeren`, `traffic_counter_transect`) hadden `…|cycleway|path` — de oude versie, **zonder** `steps`/`corridor` (de Centrumpassage-fix uit v2.x was er nooit naartoe gesijpeld);
- `pocket_count` had `…|path|steps|corridor` (actueel);
- `snaptrace` had de filter al gehoist naar een `HIGHWAY_RE`-constante.

### De ingreep
Eén kanonieke regel, in elk bestand bovenaan (snaptrace's eigen patroon), met sync-comment:
```js
// Snap-netwerk highway-filter — HOUD GELIJK over alle tools (grep HIGHWAY_RE).
var HIGHWAY_RE = 'residential|living_street|primary|secondary|tertiary|unclassified|service|pedestrian|footway|cycleway|path|track|bridleway|steps|corridor';
```
Elke Overpass-query bouwt nu met `"~"'+HIGHWAY_RE+'"`. Onder de single-file-zonder-build-constraint kan er geen échte gedeelde bron zijn, maar dit komt er het dichtst bij: zes byte-identieke regels, greppbaar (`grep HIGHWAY_RE *.html`), met de volgende wijziging één-regel-per-bestand.

Dit dicht **twee** gaten in één pass: `track`/`bridleway` (zia's bospad + toekomstige ruiterpaden) én de stille `steps`/`corridor`-drift in vier tools.

**Vooruit-werkend:** zia's bestaande ZIP is niet retro-te-helen (het pad zat niet in de download); de eerstvolgende telling langs zo'n pad pakt het wel mee.

---

## Deel 2 — telrapport-consolidatie (drift via eliminatie)

`telrapport_viterbi.html` was een fork van `telrapport.html` met een Viterbi-map-matching-engine erbovenop. Probleem: ze waren in **beide** richtingen gedrift — `telrapport.html` had de v2.11-pocket-presentatie (8-type config, intensiteitslegenda, modus-badges), de viterbi-fork had alleen de oude 4-type-config + de engine. Geen van beide was een superset; een v2.11-winkelstraat/transect-ZIP rende fout in de viterbi-tool.

**Besluit (op verzoek): consolideren.** `telrapport.html` is de enige productie-renderer (al v2.11-compleet). `telrapport_viterbi.html` → `_archief/`. Drift-oppervlak weg door eliminatie, niet door synchronisatie. Geen dode links (index linkte toch al niet naar telrapport).

De Viterbi-capaciteit is volledig bewaard in `_archief/viterbi_rig/`: de geïsoleerde engine (`viterbi_engine.js`, Newson-Krumm `matchTopo`) + een headless rig + een README die vastlegt waarom hij geparkeerd staat en hoe je hem ont-parkeert (als simpel-only opt-in ín `telrapport.html`, niet als tweede fork).

---

## Deel 3 — De Viterbi-veldvalidatie (waarom geparkeerd)

Op echte ZIPs bleek Viterbi géén universele snap-upgrade. Drie raadsels, drie verschillende oorzaken, geen ervan "Viterbi is goed/slecht":

- **txb** (convergente trio 130419432 e.a.): sub-meter-convergent → irreducibel. Viterbi *verplaatst* de ambiguïteit (14 tikken 7/7 over twee buren), lost 'm niet op. Bevestigt de v2.10-closure.
- **evj** (winkelstraat): schone, nauwkeurige, continue data (ways op 8 m) — en `matchTopo` haakt tóch op 37/42 fixes af. Limiet van het topologische HMM in dichte voetganger-netten. Maar winkelstraat snapt niet op traject, dus dit deert die modus niet.
- **zia** (transect): de "off-netwerk" bleek een **fetch-gat** (Deel 1), geen echt off-netwerk en niets dat Viterbi kon redden. Plus: scherm-uit-workflow (batterij sparen, weinig events) → schaars/brokkelig spoor (gaten tot 429 s) → trajectorie-matching breekt structureel.

**Sweet spot van Viterbi:** continue-loop simpel/object-surveys (dicht GPS-spoor, op gemapt netwerk). Daar gaf het een schoon continu pad. Voor de tel-modi (transect/winkelstraat) is het het verkeerde gereedschap — die leunen op locatie + GPS-snelheid, niet op traject.

---

## Deel 4 — index.html

- **Transect-kaart verwijderd** (HTML + en/nl-dict-entries). De oude losse tool `traffic_counter_transect.html` blijft op schijf (bereikbaar via URL, niet meer geadverteerd), opgevolgd door pocket's transect-modus.
- **Pocket herbeschreven** als multi-modus-platform: label "Pocket — three modes / drie modi", titel "Move and Count / Tellen in beweging", desc dekt simpel + transect + winkelstraat. Pocket staat nu op plek 2 (na Static), omdat het de lopende-telling-rol overneemt.
- **Standalone-opmerking** bovenaan toegevoegd (en/nl): *"Standalone traffic-counting tools — each runs entirely in your browser. No install, no account; your data stays on your device."*

---

## Datacontract

**Geen wijzigingen.** v2.12 raakt de fetch-filter en de UI, niet de ZIP-structuur of de CSV-schema's. KNIME-readers en telrapport blijven ongewijzigd.

---

## Validatie-discipline (deze release)

- Highway-de-drift als één Python-pass met asserts (precies 1 vervanging per bestand); daarna per bestand JS geëxtraheerd + `node --check` (alle 6 groen); `HIGHWAY_RE` byte-identiek geverifieerd (6×) en elke query gekoppeld.
- index.html-patch met asserts (transect-kaart + 6 dict-regels weg, pocket-copy 2-talig, introNote compleet); `node --check` op het app-script groen.
- Rig na verplaatsing opnieuw `node --check` (9 bestanden groen) + smoke-test (engine draait vanaf `_archief`).

---

## Backlog (bijgewerkt)

### Geparkeerd / gedeprioriteerd door deze release
- **Viterbi-merge** → geparkeerd. Engine + rig in `_archief/viterbi_rig/`. Niet bewezen als universele upgrade; ont-parkeren = simpel-only opt-in ín `telrapport.html`.
- **Off-netwerk-drie-toestandssnap** → gedeprioriteerd. zia was het bewijs ervoor en bleek een fetch-gat. Tenzij er echte open-terrein-tellingen opduiken (geen way in OSM), is de toestand niet nodig.

### Kleine open punten (uit deze sessie)
- `traffic_counter_transect.html` zelf archiveren naar `_archief/`? (nu alleen uit index)
- Dode `.transect-card`-CSS (+ ongebruikte `--violet`) in index.html opruimen?
- `capaciteitstelling.html` mist `["area"!="yes"]` in z'n Overpass-query (orthogonaal aan de filter-de-drift) — gelijktrekken?

### Carry-over (eerdere sessies, ongewijzigd)
- Capaciteit: cumulatieve-snap-port (`snap.networkElements` per fetch overschreven i.p.v. geaccumuleerd); dode `buildCsvString` verwijderen.
- telrapport: per-richting detailtabel (transect); winkelstraat-decompositie-view (Wardrop-Charlesworth).
- Pocket/telplanning: adaptieve segmentlengte, IndexedDB-relay pocket→telrapport, "Nu"-knop telplanning, weekprofiel-popup auto-refresh.
- Hoogtesignaal (`altitude`) voor roltrap/trap-detectie — eerst een meet-probe.
