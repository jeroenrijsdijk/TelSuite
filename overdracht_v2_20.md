# TrafficCounterSuite v2.20 — Overdracht

Deze release heeft twee onderdelen, beide rond de nabewerking en de kaartanalyse. **(1)** De v2.19-backlog-post *link/segment-samenvatting voor de wandelmodi* is gebouwd: wandel-recon-ZIP's (transect/winkelstraat/simpel) leveren nu een **`_segmentsamenvatting.csv`** — tellingen per **link × richting × categorie**, tidy-long, van nul opgebouwd uit de gereconstrueerde tikken. Telrapport toont diezelfde uitsplitsing als een lichte **categorie×richting-tabel** onder de bestaande weekprofiel-popup, met per categorie de p/m·u die de segment-p/m·u opdeelt. **(2)** Het helpcentrum kreeg een nieuwe sectie die de **drukte-berekening (p/m·u) en het weekprofiel** uitlegt — de formule, poolen-vs-gemiddelde, de dag-van-de-week-as, en het recon-gedrag.

Alles additief; byte-identiteit bewaakt op alle ongewijzigde bestanden. Drie bestanden geraakt: `parkeer_reconstructie.html`, `telrapport.html`, `traffic_counter_help.html`.

---

## Gewijzigde bestanden

| Bestand | Status | Kern van de wijziging |
|---|---|---|
| `parkeer_reconstructie.html` | ✦ bijgewerkt | (A) `wandelProfiel`-fabriek: `metRichting` geëxposeerd + vlag `heeftSegmentSamenvatting:true` (één plek → alle drie de wandelmodi); (B) nieuwe `segLenM()` + `bouwSegmentSamenvatting()`; (C) `bouwZipBlob` schrijft `_segmentsamenvatting.csv` bij wandelprofielen; (D) `reconstructie`-vlag in `_sessie.csv` → `v2.20` |
| `telrapport.html` | ✦ bijgewerkt | (E) `segSummary`-state; (F) `_segmentsamenvatting.csv` ingelezen in `loadPocketZip` (extra param `segCSV`, gelezen in de dispatch); (G) `renderSegmentBreakdown()` + aanroep in `openWeekprofile`; (H) reset opgeruimd |
| `traffic_counter_help.html` | ✦ bijgewerkt | (I) nieuwe sectie **"Drukte & weekprofiel — hoe de p/m·u wordt berekend"** + TOC-regel + kleine `.formula`-klasse; (J) recon-callout aangevuld met de v2.20-uitsplitsing |

Ongewijzigd (byte-identiek): `pocket_count.html`, `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html`, `traffic_counter.html`, `telplanning.html`, `snaptrace.html`, `snap_methodology.html`, `zip_format_reference.html`, `index.html`, `README.md`, `winkelstraat_rekenrig.html`, `build_bezocht.py`, `planningen/*`, `_archief/*` en alle eerdere overdrachten.

**Schema-signaal voor KNIME.** De wandel-recon-ZIP heeft één nieuwe output die sign-off vraagt:
- **`_segmentsamenvatting.csv`** (tidy-long) — schema: `sessie_id;osm_way_id;segment_index;segment_count;straat;highway;richting;categorie;aantal;segment_lengte_m`. Eén rij per (link × richting × categorie) met ≥ 1 geplaatste tik. `richting` (a/b) alleen bij transect; leeg bij winkelstraat/simpel. `aantal` = aantal `ok`-tikken; `segment_lengte_m` uit de segment-geometrie (1 decimaal). **Presence staat bewust NIET hier** — joinbaar met `_bezocht.csv` op (`osm_way_id`, `segment_index`).
- De `reconstructie`-vlag in `_sessie.csv` staat nu op `v2.20`. Telrapport gebruikt die vlag alleen op waarheid (recon-detectie), dus oudere v2.19-recon-ZIP's blijven correct herkend.

---

## Deel 1 — `_segmentsamenvatting.csv` (de tik-kant van de Viterbi-route)

**Aanleiding.** Auto/fiets verfijnen een bestaand `_straten.csv`; wandel-ZIP's hébben dat niet. Deze samenvatting is daarom van nul opgebouwd uit de gereconstrueerde tikken. Ze is de **tik-kant** van precies dezelfde Viterbi-route waarvan `_bezocht.csv` de **presence-kant** is (v2.19); de twee joinen schoon op (`osm_way_id`, `segment_index`).

**Vorm: tidy-long, geen brede tabel.** Wandelcategorieën zijn vrij configureerbaar (car/truck/ped/tegemoet/winkeltype/object…) — een vaste brede kop (zoals auto's `goed;fout;leeg;spec`) klopt nooit. Eén rij per (link × richting × categorie) is bovendien exact wat de backlog vroeg en meteen KNIME-vriendelijk.

**Presence genormaliseerd, niet gedupliceerd.** Aanwezigheidstijd is een eigenschap van het *segment*, niet van de categorie×richting-combi. Ze in elke rij herhalen zou het model vertroebelen; daarom leeft ze in `_bezocht.csv` en wordt ze gejoind. Densiteit downstream: `p/m·u = aantal ÷ (segment_lengte_m × Σduur_sec/3600)` — dezelfde formule die telrapport toont, nu per categorie×richting uitsplitsbaar.

**Profiel-gedreven.** Eén vlag `heeftSegmentSamenvatting` in de `wandelProfiel`-fabriek zet het aan voor transect/winkelstraat/simpel tegelijk; parkeren/auto/fiets krijgen het niet. `bouwSegmentSamenvatting(sid)` aggregeert `S.taps` (status `ok`, met way) naar (way, seg, richting, categorie); straatnaam per way uit de herbouwde `_bezocht.csv` (zelfde naamgeving), lengte/highway/segment_count uit `_netwerk.csv`. `richting` komt uit `src.richting` (veld-grondwaarheid a/b) en alleen als het profiel `metRichting` is. `segLenM()` is byte-gelijk aan `telrapport.segmentLengthM`, zodat de lengte in het CSV overeenkomt met wat telrapport uit dezelfde geometrie afleidt.

**Randgeval.** `ongesnapt`-tikken (geen way) tellen niet mee op een link — hun aantal staat al in `_reconstructie_log.csv` (`tikken_ongesnapt`). Wandelprofielen kennen geen `onzeker`-status (opLink plaatst altijd als `ok`), dus in de praktijk zijn alle wandeltikken `ok` of `ongesnapt`.

---

## Deel 2 — Telrapport: categorie×richting-uitsplitsing in het weekprofiel

**Aanleiding.** Wandel-recon-ZIP's zijn `app_type=pocket` mét `bezocht`, dus de bestaande weekprofiel-popup opende al bij een klik op zo'n segment (met de presence-gebaseerde p/m·u). Wat ontbrak was de tik-uitsplitsing per categorie/richting die de nieuwe samenvatting nu levert.

**Fix (licht, hergebruik).** `loadPocketZip` leest `_segmentsamenvatting.csv` in `segSummary[sid][key]`. `renderSegmentBreakdown(key, lenM)` pool't over de **zichtbare** sessies naar (categorie, richting), berekent per categorie de p/m·u met **dezelfde presence** als het weekprofiel (Σ`durSec` over de zichtbare visits van dat segment), en rendert een `cmp-table` onder de sessietabel. De richting-kolom verschijnt adaptief — alleen als er echt richtingen zijn (transect); winkelstraat/simpel tonen 'm niet. Kleuren via de bestaande `intensityClass`. Geen nieuwe CSS.

**Decompositie klopt.** Omdat elke categorie-p/m·u = `aantal / (lenM × totSec/3600)` met dezelfde noemer, tellen de categorie-tarieven op tot de segment-totaal-p/m·u. Zo is de uitsplitsing intern consistent met het weekprofiel.

**Bekende marginale afwijking.** De uitsplitsing telt *alle* geplaatste tikken op het segment; het weekprofiel-totaal telt tikken bínnen de presence-vensters (`n_tellingen`). Voor een normale moving-observer-wandeling vallen alle tikken in het venster en matcht het exact. Alleen als een tik in een uitgefilterde run (< 5 s / < 3 punten) valt, kan de Σ van de uitsplitsing een fractie boven het presence-totaal liggen. Aanvaardbaar en zeldzaam; de uitsplitsing telt bewust álle gereconstrueerde tikken (de ware telling).

---

## Deel 3 — Help: drukte-berekening & weekprofiel

Nieuwe sectie in de telrapport-groep van `traffic_counter_help.html`, met TOC-regel:
- **Kernformule** uitgelicht (`p/m·u = tikken ÷ (segmentlengte_m × aanwezigheidstijd_uur)`) + lees-hint en de drie ingrediënten met hun bron in de ZIP.
- **"Poolen, geen gemiddelde"** — het tijd-gewogen karakter met het gewogen voorbeeld (23.3 vs. het misleidende rekenkundige 31.4).
- **Dag-van-de-week-as** en de proportionele uur-splitsing van visits over uurgrenzen.
- **Recon-callout** — op recon-ZIP's zijn teller, presence én geometrie de gereconstrueerde versie; `_…_origineel.csv` wordt nooit gebruikt; schonere noemer; **plus de v2.20-uitsplitsing** (categorie×richting).
- **Intensiteitsklassen** met kleur-swatches.

Eén nieuwe `.formula`-klasse in de v2.16-opschoningsgeest (geen inline-styles, behalve de gesanctioneerde swatch-kleuren).

---

## Validatie

Op elk build-blok:
- **`node --check`** op de geëxtraheerde inline-JS van beide HTML-tools — schoon.
- **HTML tag-balans** via een echte parser met scripts/styles gestript — schoon (help: 40 `<section>` ↔ 40 `</section>`).
- **Diff tegen de v2.19-baseline** — exact drie bestanden gewijzigd; alle overige suite-bestanden **byte-identiek** (bevestigd met `diff -rq`).

Functioneel, headless in een Node-sandbox met de echte functies:
- **`bouwSegmentSamenvatting`** op synthetische transect- en winkelstraat-tikken: rijen per (way, seg, richting, categorie); richting gevuld bij transect en leeg bij winkelstraat; nieuw-opgehaalde naamloze way netjes zonder straat maar mét highway/lengte; `ongesnapt`-tik uitgesloten; deterministische sortering (way, seg, richting, categorie); lengtes correct uit de WKT-geometrie.
- **`renderSegmentBreakdown`** op synthetische `segSummary` + `visitData` over twee sessies: correct gepoold (car/a = 8+2 = 10), p/m·u per categorie (16.7 / 6.7 / 5.0) die optelt tot de segment-Σ (28.5); adaptieve richting-kolom; sessie-zichtbaarheid gerespecteerd.

**Nog in de browser te bevestigen (niet in de sandbox toetsbaar):** de popup-render op een echte wandel-recon-ZIP (transect mét a/b, winkelstraat/simpel zonder); dat het CSV daadwerkelijk in het `_recon.zip` belandt bij een echte veld-reconstructie; en de leesbaarheid van de uitsplitsingstabel op de telefoon.

---

## Backlog (bijgewerkt)

### Afgerond deze release
- **Link/segment-samenvatting voor wandelmodi** — `_segmentsamenvatting.csv` (tidy-long, link × richting × categorie), profiel-gedreven; joinbaar met `_bezocht.csv`.
- **Lichte telrapport-weergave** — categorie×richting-uitsplitsing in de weekprofiel-popup met p/m·u-decompositie.
- **Help** — sectie drukte-berekening & weekprofiel + recon-uitsplitsing.

### Losse eindjes / voor een volgende sessie
- **Kaart-validatie van de link-herzieningen** (uit v2.19) — steekproef van de ~47 % verschoven tikken rond passages/kruispunten; nu extra interessant omdat de categorie×richting-uitsplitsing per segment zichtbaar is.
- **`zip_format_reference.html` — recon-sectie.** Het referentiedoc beschrijft de rauwe veld-ZIP's, niet de recon-outputs (`_…_origineel.csv`, `_reconstructie_log.csv`, en nu `_segmentsamenvatting.csv`). Een eigen "Reconstructie-ZIP"-blok zou het compleet maken.
- **Twee kleine live-verbeteringen in pocket** (uit v2.18, nog open): `fetch_fail`-trace-events per mislukte poging, en een sequence-guard tegen out-of-order fetch-antwoorden die `cacheLat/Lon` overschrijven.

### Wacht op andere trajecten
- **Bezettingsgraad-herberekening voor auto** (`bezet`/`vrij`/`bezettingsgraad_pct`) — wacht op de ombouw van de parkeertelling zelf; nu ongewijzigd overgenomen uit het origineel.
- **`gebiedsnaam` in `_sessie.csv`** — vereist KNIME sign-off.
- **Per-categorie parallelle-link-toewijzing** — expliciet buiten scope (breekt de route-consistentie van de Viterbi); wandeltikken landen op de link onder de gelopen route.

### Principes bevestigd deze sessie
- **Ontwerpen en scherpstellen vóór bouwen** — vorm (tidy-long i.p.v. breed), bestandsnaam en presence-normalisatie eerst afgestemd; de bouw was daarna chirurgisch.
- **`bezocht` en `segmentsamenvatting` zijn twee kanten van dezelfde Viterbi-route** — presence resp. tikken, joinbaar op way+segment; geen duplicatie.
- **Profiel-gedreven, DRY** — één vlag in de `wandelProfiel`-fabriek zet de samenvatting aan voor alle wandelmodi; een nieuwe wandelmodus erft 'm gratis.
- **Lichte weergave = hergebruik** — de uitsplitsing hangt onder de bestaande weekprofiel-popup; geen nieuwe modal, geen nieuwe CSS.
- **Additief en byte-identiteit-bewaakt** — alleen de drie geraakte bestanden wijzigen.
