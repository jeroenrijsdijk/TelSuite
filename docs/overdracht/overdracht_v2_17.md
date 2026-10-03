# TrafficCounterSuite v2.17 — Overdracht

Vier wijzigingen, geen enkele raakt een schema. **(1) Pocket — stall-detector + tijdspoort:** het anker herkent nu zelf wanneer het niet meer meebeweegt (haakse kruising, way-uiteinde) en herstelt in ~10–20s in plaats van tientallen seconden; een GPS-stilte >25s (gebouwpassage) wordt behandeld als teleport in plaats van genegeerd. De tijdspoort is ook naar **parkeertelling**'s looprichting-trail geport. **(2) Pocket — zichtbare fetch-mislukkingen + volgorde-guard:** een autorit met CarPlay op de achtergrond legde bloot dat mislukte netwerkverzoeken volledig stil bleven; nu krijgt elke mislukking een trace-regel, en een verouderde respons kan de cache niet meer met een oude positie overschrijven. **(3) Pocket — modus Parkeren:** vier vaste knoppen (bezet boven, leeg onder, links/rechts, min-knoppen middenin geclusterd), methodiek simpel tellen. **(4) Telrapport:** parkeer-tikken kleuren leeg/bezet op de kaart, en een nieuwe **polygoon-tool** vat tellingen binnen een getekend gebied samen per sessie én per wegsegment.

Alle vier zijn veldgedreven: de stall-detector en tijdspoort komen direct uit vier rig-sessies (4, 6 en 8 juli) en een replay-bewezen drempel; de fetch-fixes uit een echte autorit-ZIP (13 juli) die het CarPlay-achtergrondprobleem zichtbaar maakte. Additief, byte-identiteit bewaakt op de gedeelde blokken, geen bestaande beslislogica aangeraakt.

---

## Gewijzigde bestanden

| Bestand | Status | Kern van de wijziging |
|---|---|---|
| `pocket_count.html` | ✦ bijgewerkt | (1) **Stall-detector** (`snapStallStep`/`snapStallCheck`, K=3/RATIO=0.3/S_MIN=3) op de ~5m-routepunt-cadans → volledige anker-reset via het bestaande pad, `snap_path='stall_reset'` in de trace. **Tijdspoort** (`TIME_GAP_RESET_S=25`) bovenin de GPS-handler → `time_gap_reset` in de trace. (2) **`fetch_fail`/`fetch_stale`/`fetch_giveup`**-trace-events in `snapFetchNetwork`; **sequence-guard** (`fetchSeq`/`fetchApplied`) tegen out-of-order responses. (3) **Modus Parkeren**: `PK_CATS` (2×2, bezet-boven/leeg-onder), `adjustParkeer`/`buildParkeerCards`, tikken lopen door de bestaande `telHistory`/`snapResolveTap`-pijplijn — vullen alleen de al bestaande `type`/`richting`-kolommen |
| `parkeertelling.html` | ✦ bijgewerkt | (1) **Tijdspoort** op de trail: een tijdgat >25s reset `trail`/`trailCum` én nult `travelRefBearing` (in tegenstelling tot de bestaande afstands-spike-behandeling, die de richting bewust behoudt — multipath ≠ garage-in-en-uit-lopen) |
| `telrapport.html` | ✦ bijgewerkt | (3) `APP_CONFIG.pocket` uitgebreid met `leeg`/`bezet` (kleuren groen/rood, gelijk aan de knoppen in pocket); `perRowType` geldt nu ook voor `modus==='parkeren'`. (4) **Polygoon-tool**: klik-teken-dubbelklik-sluit op de kaart, samenvatting per sessie × per wegsegment × per type in het bestaande detailpaneel. Hergebruikt de al bestaande `pointInPolygon` (capaciteit-parkeerpolygonen) — geen duplicaat-logica |
| `README.md` | ✦ bijgewerkt | Versie → v2.17; release-noot |

Ongewijzigd: alle overige bestanden (`capaciteitstelling.html`, `fietsparkeren.html`, `telplanning.html`, `traffic_counter.html`, `snaptrace.html`, `snap_methodology.html`, `zip_format_reference.html`, `index.html`, `planningen/*`, `_archief/*`). **Geen schema- of ZIP-structuurwijziging.** Nieuwe *waarden* in bestaande vrije velden: `_snap_trace.csv` krijgt nieuwe `event`-types (`fetch_fail`/`fetch_stale`/`fetch_giveup`) en `snap_path`-waarden (`stall_reset`/`time_gap_reset`) — dat bestand wordt door telrapport en KNIME genegeerd. `_telregels.csv` krijgt nieuwe waarden in de al bestaande `type` (`leeg`/`bezet`) en `richting` (`links`/`rechts`) kolommen, en `_sessie.csv` een nieuwe `modus`-waarde (`parkeren`). KNIME is hiervan op de hoogte gesteld; sign-off is volgens afspraak geen blokkade.

---

## Deel 1 — Stall-detector + tijdspoort

**Aanleiding.** Vier veldwandelingen (rig-prototype `pocket_snaptest.html`, niet in deze levering) legden twee losse faalpatronen bloot. **Haaks kruisen / way-uiteinde:** het anker blijft aan een way hangen terwijl je 'm feitelijk verlaten hebt — `snapM` (positie langs de link) staat dan stil of springt niet mee, tien fixes lang exact hetzelfde getal in het ergste geval. Het bestaande afstands-reset (`SNAP_RESET_M=50`) zag dit pas na ~35–50s. **Temporeel GPS-gat:** een gebouwpassage (222s stilte, 25m netto verplaatsing bij terugkomst) is voor elke afstands-poort onzichtbaar — geen enkel bestaand mechanisme merkte het op.

**De stall-detector werkt op een ratio, niet een afstand.** Conditie per meting (zelfde way als de vorige, ~5m-cadans): `stepM ≥ S_MIN` ∧ `|ΔsnapM| < RATIO·stepM`. Dat is schaalvrij — "minder dan 30% van je verplaatsing projecteert op de link" komt neer op een hoek van ~72–108°, precies het smalle raam waar A (de snapM-richting) al zwijgt. Bij K=3 opeenvolgende hits: volledige anker-reset, hergebruik van het bestaande pad (anker→null, herbootstrap binnen dezelfde meting). De drempels zijn niet handmatig gekozen — ze zijn **replay-gevalideerd** tegen alle vier veldsessies (zie Validatie), en bleken ongevoelig voor de precieze waarde binnen S_MIN 3–4 / RATIO 0.3–0.5 / K 2–3: het signaal is fysiek, niet fragiel afgesteld.

**De tijdspoort is losstaand en simpel.** `Date.now()` sinds de vorige fix > 25s ⇒ behandel als teleport: anker, stall-teller én (in parkeertelling) de trail en `travelRefBearing` resetten. Bewust *niet* samengevoegd met de bestaande afstands-spike-behandeling (>50m in parkeertelling) — die twee betekenen iets anders: een afstandssprong kán multipath zijn (richting blijft geldig), een tijdgat betekent per definitie dat je iets deed waar de app niets van weet (garage in en uit lopen, gebouw doorkruisen) en de richting moet dus wél vervallen.

**Wat dit niet oplost.** De eerste meting na een ankerwissel blijft inherent stil (geen `ΔsnapM` zonder voorganger) — dat is bedoeld, A zwijgt liever dan te gissen.

---

## Deel 2 — Zichtbare fetch-mislukkingen + volgorde-guard

**Aanleiding.** Een autorit-ZIP (13 juli, CarPlay+Waze op de voorgrond, telefoon ingeplugd, scherm aan) toonde: alle 20 geslaagde netwerk-fetches over 33 minuten en 12,5 km bleven binnen 589×243m van het startpunt. GPS bleef foutloos doorlopen (iOS geeft locatie-tracking een uitzondering op achtergrond-throttling); gewone `fetch()`-aanroepen vanuit de backgrounded Safari-tab kregen die uitzondering niet. Het resultaat: geen dataverlies (elke tik/gps-regel had een correcte lat/lon), maar wel een onvolledig `_netwerk.csv` — en de mislukkingen waren volledig onzichtbaar in de export.

**De vaststelling, niet de blokkade.** Dit is een platformgrens (vergelijkbaar met de iOS-gebaar-eis voor kompastoegang), geen bug om weg te patchen. Wat wél repareerbaar was: de stilte.

**Twee kleine, additieve ingrepen in `snapFetchNetwork`.** (a) Elke mislukte Overpass-poging krijgt nu een `fetch_fail`-trace-regel (endpoint, pogingnummer, foutmelding); opgeven na de maximale pogingen loggen als `fetch_giveup`. (b) Een oplopend volgnummer (`fetchSeq`/`fetchApplied`) per logische fetch-aanvraag: komt een respons terug die inmiddels is ingehaald door een nieuwere, dan wordt-ie geweigerd (`fetch_stale`) in plaats van `cacheLat/Lon` met een verouderde positie te overschrijven.

**Wat dit niet oplost.** De onderliggende oorzaak (achtergrond-throttling tijdens CarPlay-navigatie) blijft bestaan. De echte oplossing — post-hoc herfetch van de ontbrekende stukken in telrapport, met map-matching en een retrospectieve richtingslaag — is **ontworpen maar nog niet gebouwd**; zie Backlog.

---

## Deel 3 — Modus Parkeren in pocket

**Vorm.** Vier gelijke, fullscreen knoppen: bezet (rood) boven, leeg (groen) onder, links/rechts als kolommen. De min-knoppen van alle vier convergeren naar het midden van het 2×2-raster (bovenrij-kaarten naar onder, onderrij naar boven; linkerkolom naar rechts, rechterkolom naar links).

**Methodiek: simpel tellen, letterlijk.** Eén tik = één `telHistory`-regel met GPS + snap-erving via de bestaande `snapResolveTap` — geen snelheid, geen decompositie. **Nul schemawijziging**: `type` en `richting` bestonden al als kolommen (winkelstraat/transect); de knoppen vullen ze met `leeg`/`bezet` respectievelijk `links`/`rechts`. Omdat het gewone `telHistory`-regels zijn, doen `reassignTrajectory`, het sessieherstel-vangnet en de telrapport-weergave automatisch mee.

**Bewust géén automatische zijde-bepaling.** Dit is niet parkeertelling.html met haar bearing-afgeleide kant — links/rechts is hier wat je indrukt. Dat past bij "simpel tellen": de teller is de waarheid, de app logt. (Zie Backlog voor een mogelijke kruisvalidatie tegen de retrospectieve richtingslaag.)

---

## Deel 4 — Telrapport: parkeer-kleuren + polygoon-tool

**Parkeer-kleuren.** Drie regels in `APP_CONFIG.pocket` (types/kleuren/labels uitgebreid) en `perRowType` geldt nu ook voor `modus==='parkeren'` — verder niets, het per-rij-kleur-mechanisme bestond al voor winkelstraat/transect.

**Polygoon-tool.** Knop "polygoon" onder Weergave. Aan: klik plaatst punten (met live streeplijn-preview), dubbelklik sluit af, Esc/"annuleren" stopt. Na afsluiten blijft de vorm zichtbaar en verschijnt de samenvatting in het bestaande detailpaneel: per sessie een kop (teller/datum/totaal), daaronder een tabel per geraakt wegsegment met aantal en per-type-uitsplitsing, subtotaal per sessie, eindtotaal. Werkt generiek op `telData` (dus op alle teltypes), respecteert de sessie-zichtbaarheid.

**Onderweg gevonden en gecorrigeerd:** er bestond al een `pointInPolygon`-functie (voor de capaciteits-parkeerpolygonen, met een ander signatuur — `[lat,lon]`-paren i.p.v. Leaflet-objecten). De eerste versie van de polygoon-tool definieerde er per ongeluk een tweede met dezelfde naam, wat de bestaande aanroep (regel ~3067) zou hebben gebroken. Verwijderd; de nieuwe tool converteert zijn Leaflet-vertices naar array-paren en hergebruikt de bestaande, ongewijzigde functie.

---

## Validatie

- **Alle drie gewijzigde HTML-bestanden**: inline JS geëxtraheerd + `node --check` groen; tag-balans gecontroleerd (geen dubbele DOM-ids); geen dubbele top-level functienamen (de `pointInPolygon`-bug hierboven was hier de vangst).
- **Functie-diff t.o.v. v2.16** (md5 per functie): `pocket_count.html` wijzigt exact `buildResult` (+1 regel: `snapM` toegevoegd), `snapFetchNetwork`, `startGps`, `stopTelling` (parkeren-routing); nieuw zijn `snapStallStep`/`snapStallCheck`/`traceFetchEvent` en de acht `pk*`-functies. `parkeertelling.html` wijzigt alléén `onPosition`. `telrapport.html`: `loadPocketZip` gewijzigd (parkeer-kleuren), zes nieuwe polygoon-functies, verder niets.
- **Stall-detector**: `snapStallStep` geëxtraheerd uit het gebouwde bestand en gereplayd tegen alle vier veld-CSV's. Sessie 1 (4 juli, nog geen live-detector): eerste triggers exact op de eerder geanalyseerde momenten (13:06:35, 13:08:21), alles binnen de bekende clusters. Sessies 2–4 (6+8 juli, wél live-detector — de derde hit zelf staat dus nooit in de data): replay-teller staat exact op K−1 vlak vóór elke door de app gelogde reset, en nul valse triggers daarbuiten.
- **Tijdspoort + stall-randgevallen + guard-semantiek**: 14 unit-asserts (24/25/26/222s-grenzen, way-wissel/stilstand/normale-voortgang/stall-op-de-detector, stale-vs-fresh fetch-fid). Structurele check dat `snapFetchNetwork` de volgorde validatie→stale-guard→applied-markering→mutaties aanhoudt.
- **HIGHWAY_RE**: byte-identiek over `pocket_count.html`, `parkeertelling.html` en v2.16 (md5).
- **Parkeren-modus**: 10 gedrags-unittests op de geëxtraheerde tellogica — 4 categorieën/unieke keys/2×2-structuur, tik zet juiste `type`/`richting`, categorieën onafhankelijk, undo pakt de juiste laatste passende entry, undo op nul doet niets, onbekende key genegeerd.
- **Polygoon-tool**: 6 asserts op de hergebruikte `pointInPolygon` (vierkant, driehoek, randgevallen); volledige `showPolygonSummary`-test met nagemaakte sessies bevestigt correcte per-sessie/per-segment/per-type telling, onzichtbare sessie genegeerd, punt buiten het gebied genegeerd.
- **Niet live gedraaid**: de stall-detector/tijdspoort-integratie in productie-pocket is per replay en unit-test gevalideerd, niet op een echt toestel. De eerstvolgende veld-ZIP is de proef; de trace maakt elk ingrijpen nu zichtbaar.

---

## Backlog (bijgewerkt)

### Afgerond deze release
- ~~snap-anker volgt niet mee bij haaks kruisen / way-uiteinde~~ → **stall-detector, K=3/RATIO=0.3/S_MIN=3, replay-gevalideerd over 4 sessies**.
- ~~temporeel GPS-gat (gebouwpassage) onzichtbaar voor afstands-poorten~~ → **tijdspoort (25s) in pocket + parkeertelling**.
- ~~mislukte netwerk-fetches volledig stil~~ → **`fetch_fail`/`fetch_stale`/`fetch_giveup`-trace-events + sequence-guard**.
- ~~geen parkeertelling-methodiek binnen pocket~~ → **modus Parkeren, 2×2, simpel tellen, nul schemawijziging**.
- ~~telrapport toont parkeer-tikken niet visueel onderscheiden~~ → **leeg/bezet-kleuren, gelijk aan de pocket-knoppen**.
- ~~geen manier om tellingen in een zelfgekozen gebied samen te vatten~~ → **polygoon-tool, per sessie × per segment × per type**.

### Volgende voor de hand liggende stap (ontworpen, nog niet gebouwd)
- **Near-perfect post-hoc reconstructie in telrapport** (architectuurkeuze vastgelegd: telrapport is de rekenplek, pocket-ZIP hoeft alleen veld-goed-genoeg te zijn). Vier lagen: (1) **gat-detectie + herfetch** — alleen de ontbrekende stukken langs de trail aanvullen, bestaand `_netwerk.csv` blijft grondwaarheid-van-die-dag; (2) **map-matching** op het aangevulde net via het bestaande `reassignTrajectory`-skelet, her-afgesteld voor auto-snelheid/-schaal; (3) **richtingslaag** — de retrospectieve schuifvenster-regressie (±15s, wayId-continuïteitsgrens bevestigd geen blinde vlek bij zijwegen, hysterese 2 vensters, min-uitslag 3m) op de schone post-match-coördinaat i.p.v. de ruwe live-anker; prototype op de rig-data: 11/15 eerder foutieve tikken correct-of-eerlijk-onzeker, bochtcluster blijft per definitie onzeker; (4) **tik-hertoekenning** met way+segment+richting. Parameters van laag 3 nog niet replay-gevalideerd over alle sessies zoals K/RATIO/S_MIN dat wel waren — dat hoort vóór de bouw. De autorit-ZIP (13 juli) is het natuurlijke testcorpus.
- **Richting als exportkolom.** Zodra laag 3/4 hierboven gebouwd is: `richting` per tik (of expliciet "onzeker") als kolom in de export. KNIME-sign-off nodig vóór dat definitief wordt — kan parallel lopen, hoeft de bouw niet te blokkeren zolang telrapport het resultaat eerst alleen toont.
- **Kruisvalidatie parkeren vs. parkeertelling.html.** De nieuwe simpel-tellen-modus logt `richting` als geklikt (mens), parkeertelling.html leidt 'm af (bearing). Geklikt naast gereconstrueerde looprichting is precies de A/B-vergelijking van de richtingslaag, maar met menselijke grondwaarheid — gratis onderzoeksdata zodra beide bestaan.

### Nog open veldvakjes (rig, niet-blokkerend)
- Haaks-kruisen-trigger (cluster-1-type van 4 juli) nog niet live gezien in rig v2 — de twee geobserveerde v2-clusters waren allebei endpoint-clamps (inclusief een nieuwe variant: bevriezing op `snapM=0` aan het wég-begin, niet alleen het eind).
- Langdurige stilstand (5+ min, bewust naast een gevel) — het enige scenario waarin de stall-teller in theorie zonder decay zou kunnen vollopen. Niet blokkerend voor deze release: de detector heeft vier schone sessies achter zich en de tijdspoort verkleint het risico eerder dan dat 'ie het vergroot.

### Beslissing nog open (carry-over)
- **Planning/Opdrachten-workflow** (telplanning): A (download-als-vangnet) vs B (lokale planning terugschrijven naar server). Aanbeveling ongewijzigd: A.

### Wens voor latere release (schema — vereist KNIME-sign-off)
- Gebiedsnaam (`sessie_naam`) in `_sessie.csv` bewaren bij parkeer-/fietsexport.
- Richting per tik als exportkolom (zie hierboven).

### Geparkeerd / carry-over (ongewijzigd)
- **Sleep-correctie voor pocket-tellingen** — vereist het `snap_trace`/segment-model, veldvalidatie nodig.
- Moving Observer / Wardrop-Charlesworth heen-en-terug-decompositie (`passanten.html`-prototype bestaat al) — nu extra relevant omdat de richtingslaag uit de near-perfect-reconstructie hier direct op toepasbaar is (observer-richting per tegemoet-tik interpoleren).
- Viterbi-merge → `_archief/viterbi_rig/`; ont-parkeren = simpel-only opt-in.
- Capaciteit: volledige cumulatieve-snap-port (`elementsNear` + `SNAP_SEGS_RADIUS` + highway-filter).
- telrapport: per-richting detailtabel (transect); winkelstraat-decompositie-view.
- Pocket/telplanning: adaptieve segmentlengte, IndexedDB-relay pocket→telrapport, weekprofiel-popup auto-refresh, afwijkende-waarden-filter.
- Hoogtesignaal (`altitude`) voor roltrap/trap-detectie — eerst een meet-probe.
- Stand-still-locatie-aggregatie voor herhaalde tellingen op dezelfde plek.
- Off-netwerk/area-snapping; `snapSegs`-vervanging-bij-refetch (structureel).
- Helpfile: de ~39 resterende enkel-property kleur-inlines (lage waarde).
