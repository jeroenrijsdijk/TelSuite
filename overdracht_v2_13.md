# TrafficCounterSuite v2.13 — Overdracht

Twee sporen, één geest. **(1) De-risk** — de losse eindjes van v2.12 afgemaakt: één latente correctheidsbug genezen, dode code/CSS opgeruimd, en de losse transect-tool volledig geretireerd zonder één dode link. **(2) Redactionele consolidatie** van het suite-helpcentrum: transect volledig uit de handleiding, de brittle handmatige sectienummering eruit, en de rommelige opmaak rechtgetrokken.

De leidende gedachte sluit naadloos aan op v2.12: **drift wéghalen, niet toevoegen** — nu door de open punten te sluiten in plaats van nieuwe oppervlakte te openen.

---

## Gewijzigde bestanden

| Bestand | Status | Kern van de wijziging |
|---|---|---|
| `capaciteitstelling.html` | ✦ bijgewerkt | `["area"!="yes"]` op roads-query; **cumulatieve `networkElements`-accumulatie** (was overschrijven); dode `buildCsvString` weg |
| `index.html` | ✦ bijgewerkt | dode `.transect-card`-CSS + ongebruikte `--violet` var weg |
| `traffic_counter.html` | ✦ bijgewerkt | "Transect"-headerknop weg (tool geretireerd) |
| `traffic_counter_help.html` | ✦✦ herzien | transect **volledig** uit de handleiding (links, sectie, alle modus-prose, dode CSS); handmatige kop+comment-nummering verwijderd; TOC ontnummerd; back-links-markup + opmaak rechtgetrokken |
| `snap_methodology.html` | ✦ bijgewerkt | `traffic_counter_transect.html` uit de stateless-snap-opsomming |
| `README.md` | ✦ bijgewerkt | tabel-rij van de losse transect-tool weg |
| `traffic_counter_transect.html` | → gearchiveerd | verplaatst naar `_archief/` |

Ongewijzigd: `parkeertelling.html`, `fietsparkeren.html`, `pocket_count.html`, `snaptrace.html`, `telrapport.html`, `telplanning.html`, `zip_format_reference.html`, `build_bezocht.py`, `planningen/*`, `_archief/viterbi_rig/*`.

---

## Deel 1 — capaciteitstelling de-risk

Drie ingrepen in één bestand, waarvan één een echte correctheidswinst.

### 1a — cumulatieve `networkElements` (de bug)
`capaciteitstelling.html` had in z'n roads-fetch:
```js
snap.networkElements = data.elements;   // overschrijven
```
terwijl de variabele blijkens z'n eigen comment "cumulatief geaccumuleerd" hoorde te zijn (zoals in `parkeertelling.html`). Gevolg: elke fetch van een nieuw gebied **wiste het vorige netwerk**. Erger nog — `zoekTerreinen()` pusht parkeervlak-polygonen ín diezelfde `networkElements`, dus een opvolgende roads-fetch wiste óók die terreinen. De netwerk-CSV-export (`netwerk.csv`) bevatte daardoor alleen het laatste gebied.

**Fix** — gespiegeld op parkeertelling: dedup-op-id en alleen nieuwe ways toevoegen:
```js
var knownIds = {};
snap.networkElements.forEach(function(el){ knownIds[el.id] = true; });
data.elements.forEach(function(el){
  if (!knownIds[el.id]) snap.networkElements.push(el);
});
```

**Bewuste scope-grens:** snapping is *niet* aangeraakt. `buildSegments(data.elements, …)` draait nog op de vérse fetch, exact zoals voorheen — dus géén gedragswijziging in het veld, géén regressierisico. De vólledige parkeertelling-port (cumulatieve snap-kandidaten via `buildSegments(elementsNear(…))`) is bewust *niet* gedaan: capaciteit mist daarvoor `elementsNear`/`SNAP_SEGS_RADIUS`, én `buildSegments` filtert niet op highway-tag — dus die port zou eerst een filter nodig hebben, anders ga je voortaan óók op parkeervlak-randen snappen. Dat is feature-werk met veldvalidatie, geen de-risk. De carry-over note beschreef letterlijk het *overschrijven* van `networkElements`; precies dát is nu weg.

### 1b — `["area"!="yes"]` gelijkgetrokken
De roads-query miste als enige tool het `["area"!="yes"]`-filter (orthogonaal aan de v2.12 HIGHWAY_RE-de-drift). Toegevoegd; nu identiek aan de andere vijf live snap-tools. De parkeerterrein-query (`amenity=parking`) blijft bewust ongemoeid — daar is `area=yes` juist gewenst.

### 1c — dode `buildCsvString` weg
De oude enkel-CSV-builder, vervangen door de multi-file ZIP-export (`buildSessieCsvString`, `buildTelregelsCsvString`, `buildNetwerkCsvString`, `buildGpxString`). Gedefinieerd, nergens aangeroepen → verwijderd.

---

## Deel 2 — transect-tool volledig geretireerd

De losse `traffic_counter_transect.html` is in v2.11 functioneel opgevolgd door pocket's transect-modus en in v2.12 uit de index gehaald (maar bleef op schijf). Nu volledig geretireerd: **bestand → `_archief/`**.

**Het addertje:** in tegenstelling tot wat "niet meer geadverteerd" suggereerde, lkte de tool nog via live URL aan vanuit twee actieve bestanden — `traffic_counter.html` (de "Transect"-headerknop) en `traffic_counter_help.html` (nav-launcher + mode-tab-switcher). Blind verplaatsen had twee 404's opgeleverd, tegen de eigen "geen dode links"-discipline in.

**Aanpak — tool retireren, modus behouden.** De drie bestandslinks zijn verwijderd (+ de daardoor dood geworden `.mode-tab*`-CSS in de help, + de stale file-row in de bestandenlijst, + de README-rij, + de vermelding in `snap_methodology.html`). De launcher-lijst blijft coherent: transect-de-tool is weg, transect-de-modus is bereikbaar via de Pocket-link die er al stond.

**Modus-documentatie:** aanvankelijk behouden (de modus leeft in pocket), maar in dezelfde sessie alsnog volledig uit de handleiding gehaald — zie **Deel 4**. De scheiding blijft zuiver waar het telt: de twee telrapport-vermeldingen van transect als *data-type* blijven staan (pocket produceert dat ZIP-type nog), het *bestand* en alle *tool-documentatie* zijn weg.

---

## Deel 3 — index.html opschoning

De `.transect-card`-CSS (twee regels, restant van de in v2.12 verwijderde transect-kaart) en de daardoor ongebruikte `--violet`-variabele zijn weg. De CSS loopt nu schoon van het groen-blok door naar `.parking-card`; nul resterende refs naar beide.

---

## Deel 4 — Handleiding: Static-consolidatie, ontnummering & opmaak

`traffic_counter_help.html` is het helpcentrum voor de hele suite (≈38 secties). Drie ingrepen.

**Transect volledig eruit.** De pagina was *bimodaal* geschreven — "Static vs Transect" als contrast door de hele traffic_counter-hulp. Verwijderd: de eigen `#transect`-sectie, de overview-transect-kaart + "two modes"-kader, de "Transect mode"-subkop in de GPS-sectie, de "Transect CSV structure"-tabel, twee transect-veldtip-kaarten, en de ingebedde "In Transect mode …"-zinnen (session start/eind, undo, veldtips). De Methodiek-noot "Transect / Pocket" werd "Pocket". Nu-overbodige mode-koppen opgeruimd (GPS "Static mode"-kop weg; "Static CSV structure" → "CSV structure"). De daardoor dode CSS (`.card.mode-transect`, `.mb-transect`, `.tag.violet`, `--violet`) verwijderd. **Behouden:** de twee telrapport-vermeldingen van transect als *data-type* (pocket produceert dat ZIP-type nog).

**Handmatige nummering eruit.** De koppen droegen handmatige nummers ("6 — Transect…"), met daarnaast een tweede, al gedrifte nummering in de sectie-comments — comment-nummers ≠ kop-nummers, plus een dubbele "13". Elke edit dwong hernummering af. Alle kop- én comment-nummers verwijderd → titels spreken voor zich, de TOC levert de volgorde. De TOC zelf spiegelde die nummers met `<ol start="N">` → omgezet naar markerloze `<ul>`. Het brittle dubbel-systeem is weg.

**Opmaak.** De `back-links`-blokken hadden kale `<li>` direct in een `<div>` (ongeldige HTML): chip-rij → schone flex-links, beschreven-tools-blok → echte `<ul>`. Mis-ingesprongen `</div>` recht, trailing whitespace weg. Inline-styles, comment-banners en de en/nl-`lang`-mix bewust gelaten — functioneel, geen rommel. Een inline→class-refactor van de 108 inline-styles is apart beschikbaar als dat ooit wenselijk wordt.

---



**Geen wijzigingen.** v2.13 raakt UI, dode code en de capaciteit-fetch-accumulatie — niet de ZIP-structuur of de CSV-schema's. De `netwerk.csv`-export uit capaciteit bevat nu wél het volledige gefetchte netwerk i.p.v. alleen het laatste gebied (geen schemawijziging, wel completer). KNIME-readers en telrapport blijven ongewijzigd.

---

## Validatie-discipline (deze release)

- Alle edits als Python-passes met asserts (precies 1 vervanging per anker, count-checks per bestand).
- Per gewijzigd bestand JS geëxtraheerd + `node --check`: alle blokken groen (JSON-LD apart als valide JSON geverifieerd, niet als JS).
- `HIGHWAY_RE` na de capaciteit-querywijziging opnieuw geverifieerd byte-identiek (nog steeds 1 unieke regel over alle tools).
- `["area"!="yes"]` nu 1× over alle vijf live snap-tools.
- Finale dode-link-scan over de hele live suite: **nul** verwijzingen meer naar `traffic_counter_transect.html` (buiten `_archief/` en de overdracht-md's).
- Capaciteit: `buildCsvString` 0 refs; accumulatie-blok visueel + per-assert geverifieerd; snapping aantoonbaar ongewijzigd (`buildSegments` nog op `data.elements`).
- Handleiding-pass: alle transect-bits per-assert verwijderd/herschreven; tag-balans geverifieerd (section 39/39, div 156/156, ul 14/14, ol 4/4, table 14/14); resterende `transect`-refs = exact de 2 telrapport-data-type-regels; `mode-transect`/`mb-transect`/`violet` = 0 hits; TOC `start=`-attributen = 0; content-step-`<ol>`'s (4×) intact gelaten.

---

## Backlog (bijgewerkt)

### Afgerond deze release (was: "Kleine open punten" v2.12)
- ~~`traffic_counter_transect.html` archiveren~~ → **gedaan**, volledig geretireerd naar `_archief/` incl. delink.
- ~~Dode `.transect-card`-CSS + `--violet` in index.html~~ → **opgeruimd**.
- ~~`capaciteitstelling.html` mist `["area"!="yes"]`~~ → **gelijkgetrokken**.
- ~~Capaciteit: cumulatieve-snap-accumulatie (`networkElements` overschreven); dode `buildCsvString`~~ → **beide gedaan** (accumulatie minimaal/regressievrij; snap-kandidaat-port bewust uitgesteld).

### Ook afgerond deze release
- ~~Help-pagina puur op Static richten~~ → **gedaan** (Deel 4): transect volledig uit de handleiding, handmatige nummering eruit, opmaak rechtgetrokken.

### Geparkeerd / gedeprioriteerd (ongewijzigd t.o.v. v2.12)
- **Viterbi-merge** → geparkeerd in `_archief/viterbi_rig/`. Niet bewezen als universele upgrade; ont-parkeren = simpel-only opt-in ín `telrapport.html`.
- **Off-netwerk-drie-toestandssnap** → gedeprioriteerd (zia bleek een fetch-gat, geen echt off-netwerk).

### Carry-over (eerdere sessies, ongewijzigd)
- Capaciteit: vólledige cumulatieve-snap-port (`elementsNear` + `SNAP_SEGS_RADIUS` bijbouwen + highway-filter in `buildSegments`) — feature-werk, veldvalidatie vereist.
- telrapport: per-richting detailtabel (transect); winkelstraat-decompositie-view (Wardrop-Charlesworth).
- Pocket/telplanning: adaptieve segmentlengte, IndexedDB-relay pocket→telrapport, "Nu"-knop telplanning, weekprofiel-popup auto-refresh.
- Hoogtesignaal (`altitude`) voor roltrap/trap-detectie — eerst een meet-probe.
