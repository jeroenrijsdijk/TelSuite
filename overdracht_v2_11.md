# TrafficCounterSuite v2.11 — Overdracht

Een **feature- én funderingsrelease** met twee verweven verhaallijnen.

De eerste is de **terrein-schema-beslissing** voor capaciteit (open beslispunt uit de v2.10-backlog), plus een terrein-datasafety-gat dat daarbij boven kwam. De tweede, veel grotere, is dat **pocket_count een multi-modus moving-observer-platform** wordt: één snap-core, drie telmodi (`Simpel`, `Transect`, `Winkelstraat`), met een localStorage-vangnet dat pocket nog miste.

De leidende gedachte uit de transect-brainstorm: oud-`traffic_counter_transect.html` werd niet verbouwd of opnieuw geschreven, maar **getransplanteerd** — z'n waardevolle helft (richting-inferentie + telmodel) leeft nu als modus ín pocket, op pocket's bewezen anker/hysterese/adjacency-snap. Geen tweede engine, geen drift: één bron van waarheid. De oude losse transect-tool is daarmee functioneel opgevolgd (z'n telrapport-pad is dormant gemaakt, niet meer onderhouden — bewust, op verzoek).

---

## Gewijzigde bestanden

| Bestand | Status | Kern van de wijziging |
|---|---|---|
| `capaciteitstelling.html` | ✦ bijgewerkt | los `_terrein.csv` (eigen bestand, identiek schema) + terrein-datasafety in `saveSession`/`restoreSession` |
| `pocket_count.html` | ✦ bijgewerkt | **multi-modus** (Simpel/Transect/Winkelstraat) + localStorage-herstel + gedeelde `snapResolveTap` |
| `telrapport.html` | ✦ bijgewerkt | leest `_terrein.csv`; modus-bewuste pocket-render (transect-richting, winkelstraat-categorieën) |
| `telrapport_viterbi.html` | ✦ bijgewerkt | leest `_terrein.csv` (zelfde vier ingrepen als telrapport) |
| `zip_format_reference.html` | ✦ bijgewerkt | `_terrein.csv` gedocumenteerd |

Ongewijzigd: `traffic_counter.html`, `traffic_counter_transect.html` (de oude losse tool blijft staan maar wordt opgevolgd door de pocket-modus), `traffic_counter_help.html`, `telplanning.html`, `telrapport_viterbi.html`-render­logica, `snaptrace.html`, `snap_methodology.html`, `build_bezocht.py`, `index.html`, `planningen/*`.

---

## Deel 1 — Capaciteit: terrein-schema + datasafety

### `_terrein.csv` (beslispunt gehakt)
De v2.10-backlog liet open of terrein-entries de straten-kolommen volgen of een eigen bestand krijgen. **Besluit: eigen bestand.** Tot v2.10 werden 7-koloms terrein-regels letterlijk ónder de 8-koloms straten-header in `_capaciteit.csv` geplakt → kolomverschuiving downstream.

Nu schrijft `exportZip` een los `_terrein.csv` met een **byte-identieke header** aan `_capaciteit.csv`:

```
sessie_id;osm_way_id;naam;zijde;soort;capaciteit;eerste_waarneming;laatste_waarneming
```

- `osm_way_id` (op jouw verzoek, voor KNIME-consistentie), `zijde` = `nvt` (een vlak heeft geen kant).
- Geaggregeerd per (`osm_way_id` × `soort`), net als `buildStratenCsvString`.
- Identieke header = één KNIME-reader op beide bestanden, en een UNION (met constante `bron`-kolom) blijft triviaal. Nooit meer onder de straten-rijen geplakt: twee schone bestanden, één schema.

### Terrein-datasafety (gat gevonden bij het migreren)
`saveSession` persisteerde wél `entries` maar **niet** `terreinEntries`, en bailde op `if (!entries.length) return;`. Gevolg: bij crash/scherm-uit overleefden straat-tellingen de herstelkopie maar verdwenen terrein-tellingen, en een pure-terreinsessie schreef nooit een kopie. Beide gedicht: `terreinEntries` zit nu in de blob, de guard accepteert pure-terreinsessies, en `restoreSession` haalt ze terug en telt ze mee in de herstelmelding.

---

## Deel 2 — Pocket als multi-modus platform

### De architectuur (waarom het schoon blijft)
Eén centrale beslissing draagt alles: **elke tik — in welke modus dan ook — is een `telHistory`-entry**, met optioneel `type` en `richting` per entry. Daardoor erven snap, export, herstel én `reassignTrajectory` automatisch mee; alleen de telschermen en de richting-inferentie zijn modus-specifiek.

De snap-resolutie van een tik (anker erven → read-only projecteren → terugval op dichtstbijzijnde way → in `telHistory`/wachtrij) is uit `doTap` getrokken naar **`snapResolveTap(tapEntry)`**, die zowel Simpel als Transect als Winkelstraat aanroepen. Eén bron van waarheid voor de snap; geen duplicatie, geen drift.

### De moduskiezer
Het bestaande "Wat tel je?"-scherm is de moduskiezer geworden: **Simpel · Transect · Winkelstraat**. `Simpel` onthult daaronder de oude object-keuze (Auto/Fiets/Voetganger/Iets Anders) → identiek gedrag, één tik later. De gekozen modus gaat als `modus`-vlag mee in `sessie.csv` (`app_type` blijft `'pocket'`, zodat telrapport de familie blijft herkennen — de modus is de sub-discriminator).

### Modus: Simpel
Ongewijzigd telgedrag (enkelvoudige tik-snap-telling). `modus=simpel`.

### Modus: Transect (getransplanteerd)
Kaarten-telscherm: per voertuigtype (`car/truck/moto/bike/ped`) twee richtingsknoppen (A/B) met tellers. De **richting-inferentie** uit oud-transect (`tcApplyHeading`/`autoDirections`/`tcCardinalNL`/`tcDestinationPoint`/`tcPlaceNameAt`/kompas) vult de Kompas-knop met "Van X naar Y" uit heading (GPS of `deviceorientation`) + reverse-geocode. **Géén live Leaflet-kaart** — bewust weggelaten (consistent met pocket); visualisatie via de bestaande preview. `adjustTransect` roept `snapResolveTap` aan; `reassignTrajectory` is al in pocket, dus transect erft de offline junction-correctie gratis. `modus=transect`.

### Modus: Winkelstraat (nieuw)
Moving-observer voetgangerstelling met twee vaste categorieën — **Tegemoet** (oncoming) en **Stilstaand** (stationary). Twee grote knoppen, snel één-handig tikken. Dit zijn methodologisch de juíste twee: stilstaande / lengte = lineaire dichtheid; tegemoet / tijd met relatieve snelheid = flow (Wardrop & Charlesworth). Meelopend is bewust weggelaten (ruizig, achter je). **De app tikt en logt; KNIME decomponeert.** Daarvoor logt elke tik de **waarnemersnelheid** (`snelheid`, m/s uit `pos.coords.speed`); padlengte/duur komen uit de GPS-track. `modus=winkelstraat`.

### localStorage-herstel (pocket miste dit)
Pocket had geen herstelkopie (alleen `saveBlob` voor export). Nu telt élke tik door naar `localStorage['pocket_sessie']`; bij het laden komt een niet-afgeronde telling terug via een banner (Download / Verwijder). **Wis-discipline conform de v2.9/2.10-les:** de kopie blijft staan tot bevestigd-klaar (preview sluiten) of bij een nieuwe sessie — nooit blind na `generateAsync` (een geannuleerd deelvenster wist dus niets). De `reassignTrajectory`-aanroep is geguard (`if (Object.keys(snap.elements).length)`) zodat een herstel-export zonder live netwerk veilig is: tikken behouden hun reeds-gesnapte `wayId`. Het herstel is modus-bewust (modus + richtinglabels + tellers gaan mee).

**Bewust níét gepersisteerd:** de OSM-netwerk-cache (`snap.elements`) — te groot voor localStorage + secundair. De tikken dragen hun eigen `wayId`, dus de export blijft volledig; een herstel-ZIP mist alleen `_netwerk.csv` (de geometrie).

---

## Deel 3 — telrapport

- **`_terrein.csv`** wordt nu gelezen en via dezelfde parser (identiek schema) bij de straten-rijen gevoegd — anders was terrein stil uit de rapporten verdwenen. Zelfde ingreep in `telrapport_viterbi.html`.
- **Modus-bewuste pocket-render** in `loadPocketZip`: bij `modus=transect`/`winkelstraat` kleurt elke marker op zijn **per-rij type** i.p.v. het sessie-type; transect-tooltips tonen "type → richtinglabel" (labels uit `sessie.csv`), winkelstraat toont de categorie. `truck`/`moto`/`tegemoet`/`stilstaand` toegevoegd aan de pocket-config (kleuren + labels). De sessie-badge toont 📷 (simpel) / ↔️ (transect) / 🛍️ (winkelstraat).
- Het **oude losse transect-pad** (`app_type='transect'`) is dormant gelaten — niet verwijderd (zou alleen referenties raken), maar niet langer onderhouden. Nieuwe transect-data loopt via het pocket-pad.

---

## Datacontract — wijzigingen (allemaal additief, header-naam-gebaseerd)

**`sessie.csv`** (pocket) — twee kolommen achteraan:
```
…;n_waarnemingen;modus;richting_a;richting_b
```
`app_type` blijft `'pocket'`. `modus` ∈ {simpel, transect, winkelstraat}. `richting_a/b` gevuld bij transect, anders leeg.

**`telregels.csv`** (pocket) — twee kolommen achteraan:
```
…;gps_level;richting;snelheid
```
`richting` (a/b) gevuld bij transect; `snelheid` (m/s) gevuld bij winkelstraat; `type` is nu per-rij (transect/winkelstraat) i.p.v. sessie-breed.

**`_terrein.csv`** (capaciteit) — nieuw bestand, identieke header aan `_capaciteit.csv`.

Geen positieverschuiving: alle nieuwe kolommen staan achteraan, conform de bestaande discipline. KNIME en telrapport lezen op header-naam en negeren onbekende kolommen.

---

## Validatie-discipline (deze release)
Per ingreep: JS geëxtraheerd + `node --check`, HTML-tagbalans (script/style/div/button), en CSV-kolomuitlijning gecontroleerd (telregels 15/15, sessie 10/10 over álle drie modi; terrein 8/8). De drie moving-observer-modi zijn met een gemockte DOM/snap runtime getest: tellen, undo (verwijdert de juiste type/richting/categorie-entry), totaal, en de herstelcyclus (tik → kopie → "crash" → herstel met data intact). De telrapport-render-keuze is getest: transect/winkelstraat triggeren per-rij type, Simpel niet.

---

## Backlog (open)

### Pocket / off-network (uitgesteld, gewenst — geen MOETEN)
- **Off-network-modus** als volwaardige derde snap-toestand (netwerk ↔ ambigu ↔ off-netwerk), drie-toestandspoort op pocket's bestaande loodrechte-afstandsmeting + hysterese. Voor kris-kras door gebieden waar je niet op OSM-lijnen loopt. Vereist veldtuning (drempels/hysterese, ~4 rondes op echte walks, zoals pocket's snap). Aggregatie uit post-hoc clustering (telrapport doet dit al) — losse punten mogen blijven; modus-vlag (`netwerk`/`vlak`/`vrij`) op de telregel, géén apart bestand.
- **Vlak-snappen** als tier daarbinnen: punt binnen polygoon → `area_id` + WKT genormaliseerd in een geometrie-zusje (niet WKT-op-elke-rij — row-bloat + QGIS-laagvermenging). Sluit tegelijk het `vlak-snappen`-backlogitem.
- **Hoogtesignaal** (`altitude`) voor roltrap/trap-detectie — eerst een meet-probe (altitude áchteraan in `_snap_trace.csv`, één Centrumpassage-walk) vóór er een feature op wordt gebouwd.

### Capaciteit (vervolg)
- **Cumulatieve-snap-port** — `snap.networkElements` wordt nog per fetch overschreven i.p.v. geaccumuleerd (mist `elementsNear`/dedup-op-id). Engine-werk.
- Dode legacy-functie `buildCsvString` (gesignaleerd in v2.10) — nog niet verwijderd.

### telrapport
- **Per-richting detailtabel** voor transect — de richting zit nu in tooltips + markerkleur; het wegvak-detailpaneel toont nog het totaal (som over richtingen). Een echte per-richting/per-categorie detailtabel is een latere verfijning.
- **Winkelstraat-decompositie-view** — KNIME doet de Wardrop-Charlesworth-rekenkunde; een samenvattende dichtheid/flow-weergave in telrapport zou een vervolg zijn.

### Langer lopend (uit eerdere sessies)
- Moving-observer-decompositie voor pocket-verkeer (oncoming vs. stationair via GPS-snelheid) — de winkelstraat-modus is hiervan de voetganger-variant; de verkeer-variant blijft open.
- Diversen pocket/telplanning: adaptieve segmentlengte, IndexedDB-relay pocket→telrapport, "Nu"-knop telplanning, weekprofiel-popup auto-refresh.
