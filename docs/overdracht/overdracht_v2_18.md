# TrafficCounterSuite v2.18 — Overdracht

Één grote nieuwe deliverable en drie kleinere reparaties. **(1) Nieuwe tool — `parkeer_reconstructie.html`:** een standalone desktop-reconstructor die een parkeer-ZIP inleest, het wegennet vers ophaalt uit OSM (mét node-topologie), de hele route Viterbi-hersnapt, de looprichting reconstrueert en de tikken links/rechts 4 m uit de wegas plaatst — met een herschreven `_recon.zip` als resultaat. De tool is **multi-teltype**: pocket-parkeren, auto (parkeertelling.html) en fiets (fietsparkeren.html) draaien op één gedeelde motor, met een dun profiel per teltype. **(2) Pocket — fetch-discipline + eerste-fetch-garantie:** de fetch-storm die bij slechte dekking honderden verzoeken afvuurde is getemd, en de allereerste netwerk-fetch geeft nooit meer definitief op — zonder netwerk snapt niets. **(3) Static (`traffic_counter.html`) — iOS-exportfix:** de CSV-export laadde niet op iPhone; output is nu een ZIP (zoals de rest van de suite). **(4) Richtingslaag gevalideerd:** de retrospectieve looprichting-reconstructie is tegen rig-data getoetst en de parameters zijn vastgelegd — ze draaien nu in de reconstructietool.

De reconstructietool is de vrucht van deze sessie en tegelijk het antwoord op een langlopend backlog-item: de post-hoc reparatie van sessies waar het live-netwerk incompleet bleef (CarPlay-achtergrond, slechte dekking, Overpass-storingen). Alles is veldgedreven — drie echte veld-ZIP's (pocket-parkeren, auto, fiets) plus zes rig-sessies stuurden elke drempel en elk profiel. Additief waar het bestaande bestanden raakt; byte-identiteit bewaakt op alle uit pocket overgenomen constanten en de Viterbi-motor.

---

## Gewijzigde en nieuwe bestanden

| Bestand | Status | Kern van de wijziging |
|---|---|---|
| `parkeer_reconstructie.html` | ✦ **nieuw** | Standalone reconstructor. Pijplijn: ZIP inlezen → profiel kiezen → verse bbox-fetch uit OSM (`out body geom` → geometrie + node-IDs) → Viterbi-hersnap (`MATCHER`, byte-identiek overgezet uit `reassignTrajectory`) → richtingslaag (`RECON.reconstructDirection`) → links/rechts-offset 4 m uit de wegas → herschreven `_recon.zip`. Kaart met grijs/luchtfoto-schakelaar, transparantie en diep inzoomen. **Multi-teltype** via een `PROFIELEN`-register (pocket-parkeren/auto/fiets) |
| `pocket_count.html` | ✦ bijgewerkt | (2) **Fetch-discipline** in `snapFetchNetwork`: in-flight guard (`fetchInFlight`, één fetch tegelijk), exponentiële backoff op de retry (`snapBackoffMs`, 500·2ⁿ tot 8 s), cooldown+debounce op de `cacheLat===null`-noodpoort in `snapCheckRefresh`. **Eerste-fetch-garantie**: zolang er nog nooit een netwerk binnenkwam wordt de fetch nooit definitief opgegeven (`fetch_retry_first`), alleen de tussenpozen lopen op |
| `traffic_counter.html` | ✦ bijgewerkt | (3) **iOS-exportfix**: `saveBlob` letterlijk uit pocket overgenomen (iOS → `navigator.share`, elders → download-link), `exportCSV` verpakt de CSV in een ZIP via JSZip, vangnet via `lastZipBlob`/`lastZipCount`, reset wist het vangnet |
| `overdracht_v2_18.md` | ✦ nieuw | Dit document |

Ongewijzigd: alle overige bestanden (`telrapport.html`, `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html`, `telplanning.html`, `snaptrace.html`, `snap_methodology.html`, `zip_format_reference.html`, `index.html`, `README.md`, `planningen/*`, `_archief/*`).

**Schema-signalen voor KNIME.** Twee nieuwe outputs die de downstream-pijplijn kunnen raken:
- **Static levert nu een ZIP** in plaats van een losse CSV (iOS-fix). Zelfde CSV-inhoud, andere verpakking.
- **De `_recon.zip` bevat nieuwe kolommen.** In `_telregels.csv`: `lat_marker`, `lon_marker`, `zijde`, `recon_status`. Nieuwe bestanden: `_netwerk_origineel.csv` (grondwaarheid naast het verse netwerk), `_reconstructie_log.csv`, en voor auto/fiets een **herberekend** `_straten.csv` naast `_straten_origineel.csv`. Sign-off vereist vóór de recon-ZIP de KNIME-pijplijn in gaat.

`winkelstraat_rekenrig.html` (moving-observer footfall-prototype) is als los prototype meegeleverd maar **nog niet in de suite geïntegreerd** — zie Backlog.

---

## Deel 1 — parkeer_reconstructie.html

**Aanleiding.** Een parkeer-tik krijgt op het veld een way toegewezen via de live-snap, maar dat gaat soms mis: bij slechte dekking komt het netwerk incompleet binnen (tikken zonder way), bij multipath in stadskloven snapt een tik op de verkeerde parallelle way, en de looprichting die de kant links/rechts bepaalt is niet altijd betrouwbaar. Op de desktop, achteraf, is er ruimte om het beter te doen dan live kan: het hele netwerk vers ophalen, de route topologie-bewust hersnappen, en de richting uit de volledige trajectorie reconstrueren. Dat is wat deze tool doet.

**De pijplijn.** Vijf stappen, elk zichtbaar in het paneel. (1) **Inlezen** — ZIP openen, teltype herkennen via het profiel. (2) **Route-gebied** — bounding box van de trail + 250 m marge. (3) **Verse fetch** — één Overpass-query over de bbox met `out body geom`, wat zowel geometrie als node-IDs levert; daaruit wordt de node-adjacency gebouwd (`MATCHER.buildAdjacency`). (4) **Hersnap + richting** — de hele trajectorie (GPS-fixes én tikken chronologisch samen) door de Viterbi-map-matcher, dan de richtingslaag op de gesnapte snapM-reeks. (5) **Offset** — elke tik 4 m links of rechts uit de wegas, met de kant uit het teltype-profiel.

**De motor is byte-identiek overgenomen.** `MATCHER.matchTrajectory` is de volledige Viterbi uit `reassignTrajectory` in pocket: emissiekost (afstand tot way, Gaussisch), transitiekost (topologie-eerst via node-adjacency: gedeelde-node-hop wint), koerskost (GPS-stapkoers vs way-koers mod 180). Constanten identiek (`SR=40`, `SIG_MIN=5`, `HOP1=4`, `HOP2=12`, `GAMMA=0.02`, `BETA=2`, `HEAD_REF_M=10`), md5-geverifieerd. `splitWayIntoSegments` (`SEGMENT_TARGET_M=40`, `SEGMENT_MIN_M=60`) eveneens byte-identiek. Zo blijft er straks één snap-motor in de suite in plaats van twee die uit elkaar kunnen driften.

**Node-adjacency is dragend, niet optioneel.** Zonder de gedeelde-node-informatie valt de transitiekost weg en presteert de Viterbi als een simpele afstands-snap. Die informatie zit niet in `_netwerk.csv` (alleen geometrie), dus de verse bbox-fetch mét node-IDs is de enige manier om de topologie te krijgen. Empirisch bevestigd: op de parkeer-ZIP week de matcher zónder adjacency op 92 van 210 fixes af van de live-snap; mét adjacency legt hij de route consistent. Vandaar dat de verse fetch de aanbevolen (en bij een netwerkloze ZIP: enige) route is.

**Links/rechts-geometrie.** De offset = `travelSign · labelSign · leftVector`, waarbij alleen het teken van de bewegingsrichting nodig is (niet de precieze koers), met cos(lat)-correctie. De **zelftoets** is de kwaliteitsmaat: op een way waar zowel links- als rechts-tikken staan, moeten die aan tegengestelde kanten landen. Slaagt dat niet, dan staat er een verkeerde link- of richtingkeuze. Op alle drie de teltypes slaagt de zelftoets waar er gemengde ways zijn (pocket 2/2, auto 2/2; fiets had geen gemengde ways).

**Multi-teltype via profielen.** Het `PROFIELEN`-register heeft drie bewoners, elk met vier verantwoordelijkheden: ZIP-herkenning, waar de zijde/richting-invoer zit, welke highway-typen het prefereert, en het export-schema. De motor eronder is ongedeeld.
- **pocket-parkeren** — herkend aan `modus=parkeren`; kant wordt hier bepaald uit het richting-label; geen highway-voorkeur.
- **auto** — herkend aan `app_type=auto`; de veld-`zijde` is **grondwaarheid** (niet overschreven), de reconstructie reviseert alleen de link; highway-voorkeur naar de **rijbaan** (residential/service/…), weg van fietspaden.
- **fiets** — `app_type=fiets`; zijde is grondwaarheid; highway-voorkeur naar **fietspad/voetpad** (cycleway/footway/pedestrian), weg van de rijbaan. Dit lost het probleem op dat een fiets-teller die op het fietspad loopt anders naar de parallelle autorijbaan zou snappen.

De highway-voorkeur is een extra term in de emissiekost (`hwPref`: −2 voor geprefereerd, +4 voor vermeden), die de Viterbi naar het juiste netwerk buigt zonder topologie of geometrie te raken, en netjes degradeert (is er alleen een fietspad, dan kiest auto dat alsnog).

**Grondwaarheid bewaard.** Het originele netwerk gaat als `_netwerk_origineel.csv` mee naast het verse; voor auto/fiets gaat `_straten_origineel.csv` mee naast het herberekende `_straten.csv`. Het `_reconstructie_log.csv` legt vast welk netwerk gebruikt is (bbox, aantal ways, adjacency, matcher-parameters).

**Kaart.** Twee achtergronden — CartoDB grijs (overzicht) en PDOK luchtfoto 25 cm (parkeervakken zichtbaar), met transparantie-schuif en `maxZoom=22`/`maxNativeZoom=20` voor diep inzoomen. De GPS-trail is oranje, weglijnen blauw, tikken bezet-rood/leeg-groen met onzekere richting geel op de as. Veldgevalideerd via QGIS: de markers vallen fysiek in de parkeervakken.

**Robuust tegen incomplete ZIP's.** Ontbreekt het netwerk (Overpass faalde tijdens de telling), dan meldt de tool dat en biedt de verse fetch als enige route — de tikken dragen lat/lon, dus reconstructie kan alsnog. Ontbreekt ook `_gps.csv`, dan bouwt de tool de trajectorie uit de tik-posities zelf.

**Wat dit niet oplost.** De bocht-shuffle blijft: op een kink in de weg oscilleert snapM en is er geen stabiel "juiste" richting-antwoord — die tikken worden correct-onzeker gemarkeerd, niet geforceerd. GPS-gaten worden herkend als onderbreking, niet geïnterpoleerd. En de **bezettingsgraad in het herberekende `_straten.csv`** (`bezet`/`vrij`/`bezettingsgraad_pct`) is bewust nog niet herberekend — `goed`/`fout`/`leeg`/`spec` worden opnieuw geteld uit de gereconstrueerde links, maar de graad-kolommen komen ongewijzigd uit het origineel mee. Zie Backlog.

---

## Deel 2 — Pocket: fetch-discipline + eerste-fetch-garantie

**Aanleiding.** Een veldsessie vuurde 610 netwerk-fetches af (600 mislukt met "Load failed"). Diagnose: de `cacheLat===null`-noodpoort in `snapCheckRefresh` vuurde bij élke GPS-fix een verse fetch zolang het netwerk onbereikbaar bleef — een storm zonder rem. Screen-on bevestigd, dus dit was een connectiviteitsgat, geen iOS-achtergrond-onderdrukking.

**Drie additieve ingrepen.** (a) **In-flight guard** (`fetchInFlight`): één fetch tegelijk; een verse aanvraag tijdens een lopende wordt geweigerd. (b) **Exponentiële backoff** op de retry (`snapBackoffMs(n) = min(500·2ⁿ⁻¹, 8000)`) in plaats van onmiddellijk opnieuw vuren. (c) **Cooldown + debounce** op de null-poort: na een mislukte keten geen nieuwe fetch tot de cooldown voorbij is, en een tros GPS-fixes valt samen tot één poging. Simulatie op het faal-scenario: 610 → 132 pogingen (−78 %), nooit meer dan één tegelijk, gezond netwerk onaangetast.

**Eerste-fetch-garantie.** Een testsessie waarin Overpass 504-timeouts gaf, leverde een ZIP zónder `_netwerk.csv` — want pocket schrijft dat bestand alleen als er ways zijn opgehaald (conditie uit v2.17). Zonder eerste netwerk snapt niets en is de sessie live niet bruikbaar. Nu geldt: zolang `cacheLat===null` (nog nooit een netwerk binnen), geeft de fetch **nooit definitief op** — hij blijft proberen met oplopende backoff (`fetch_retry_first` in de trace), tot Overpass ooit antwoordt. Zodra er één keer een netwerk is, geldt de normale giveup weer (een mislukte refresh is dan niet fataal, het oude netwerk blijft). Gesimuleerd: 10× 504 gevolgd door succes → netwerk komt op poging 11 binnen, geen giveup.

**Wat dit niet oplost.** Als Overpass de héle telling onbereikbaar blijft, is er nog steeds geen live-netwerk — maar dat is nu geen stil verlies meer: de reconstructietool haalt het achteraf op uit de tik-posities (Deel 1). De trace toont bovendien `fetch_retry_first`, zodat het zichtbaar is dat het netwerk nooit kwam.

---

## Deel 3 — Static (traffic_counter.html): iOS-exportfix

**Aanleiding.** De CSV-export van de statische teller gebruikte een `data:text/csv`-download-link, die op iOS Safari niet werkt — de export "gebeurde" maar er kwam geen bestand. Alle andere tools in de suite gebruiken al het `saveBlob`-patroon (iOS → `navigator.share`, elders → download-link).

**De fix.** JSZip-CDN toegevoegd, `saveBlob` letterlijk uit pocket overgenomen, `exportCSV` verpakt de CSV nu in een ZIP en levert die via `saveBlob`. Vangnet via `lastZipBlob`/`lastZipCount` (gekoppeld aan `history.length`, zodat doortellen een verse ZIP forceert); reset wist het vangnet. md5-diff: alleen `saveBlob` (nieuw), `exportCSV` en `resetAll` gewijzigd, 21 andere functies byte-identiek. Veldgetest: export werkt nu op iPhone.

**Schema-gevolg.** Static levert nu een ZIP met de CSV erin in plaats van een losse CSV — KNIME-signaal (zie boven).

---

## Deel 4 — Richtingslaag gevalideerd

**Aanleiding.** De retrospectieve looprichting-reconstructie (schuivend-venster-regressie over snapM per aaneengesloten wayId-stuk) bestond als prototype maar de parameters waren nog niet aan de replay-bar getoetst — anders dan de stall-drempels uit v2.17.

**Validatie en vastlegging.** Getoetst tegen zes rig-sessies (`snaptest*.csv`, met snapM/aSense/outcome). Grondwaarheid `aSense = teken(ΔsnapM)`: 57/57 bevestigd. Breed plateau (fout 1,8–5,2 % over de hele parameterruimte, geen klif), 92 % eens / 4 % fout / 4 % onzeker; alle foutgevallen op bekende bocht-ways met niet-monotone snapM (definitioneel onoplosbaar). **Vastgelegde parameters:** `HALF_S=12`, `MIN_RANGE_M=3`, `HYST=1`, `GAP_S=25`. Aangevuld met **richting-overerving**: leidende nullen (stilstand aan het begin van een stretch, vóór de eerste beweging) erven de eerste bekende richting — een vangnet dat op de parkeer-ZIP 2 extra tikken redde zonder de rig-cijfers te schaden.

Deze laag draait nu in `parkeer_reconstructie.html` (Deel 1), tussen de Viterbi-hersnap en de offset.

---

## Validatie

Elke build: `node --check` op de geëxtraheerde inline-JS, HTML tag-balans (echte parser, scripts gestript), md5-diff op functieniveau tegen de v2.17-baseline, byte-identiteit van gedeelde constanten, en functionele Node/jsdom-harnesses.

- **`parkeer_reconstructie.html`** — pijplijn draait end-to-end op alle drie de teltypes (pocket 44 geplaatst, auto 77, fiets 27); profielherkenning 3/3 correct; zelftoets links/rechts slaagt op alle gemengde ways; Viterbi-constanten en `splitWayIntoSegments` byte-identiek aan pocket geverifieerd; netwerkloze én gps-loze ZIP verwerkt zonder crash. De **verse bbox-fetch en de kaart-rendering zijn bij Jay in de browser gevalideerd** (Overpass en Leaflet-rendering vallen buiten de sandbox); de map-matcher-wiskunde is offline volledig getoetst.
- **`pocket_count.html`** — md5-diff schoon (alleen `snapFetchNetwork`/`snapCheckRefresh` gewijzigd, `snapBackoffMs` nieuw, 92/95 byte-identiek); storm-simulatie 610→132 (−78 %); gezond-netwerk-gedrag intact; eerste-fetch-garantie gesimuleerd (10× 504 → succes, geen giveup).
- **`traffic_counter.html`** — md5-diff (alleen saveBlob/exportCSV/resetAll); veldgetest op iPhone.
- **Richtingslaag** — 57/57 rig-grondwaarheid; 92/4/4 met breed plateau; overerving valideert zonder rig-regressie.

---

## Backlog (bijgewerkt)

### Afgerond deze release
- Nieuwe reconstructietool met Viterbi-hersnap, node-adjacency, richtingslaag, links/rechts-offset, multi-teltype (pocket/auto/fiets), luchtfoto-kaart.
- Pocket fetch-discipline + eerste-fetch-garantie.
- Static iOS-exportfix.
- Richtingslaag gevalideerd en parameters vastgelegd.
- Post-hoc reconstructie (langlopend backlog-item uit v2.17) — nu gerealiseerd als aparte tool.

### Losse eindjes uit deze sessie (voor v2.19)
- **Bezettingsgraad-herberekening.** Het herberekende `_straten.csv` telt `goed/fout/leeg/spec` opnieuw uit de gereconstrueerde links, maar `bezet`/`vrij`/`bezettingsgraad_pct` komen nog ongewijzigd uit het origineel — binnen één straatrij kan dat inconsistent ogen (herberekende `goed` naast originele `bezet`). Beslissing bewust uitgesteld: lopen `bezet`/`vrij` mee met de herberekende types (voor auto is `goed`≈`bezet`), of blijft de graad een aparte veld-grootheid?
- **Verse-fetch veldvalidatie.** De bbox-fetch mét node-topologie en de "verschoven t.o.v. veld"-teller zijn bij Jay te bevestigen: zakt het aantal verschoven tikken naar iets plausibels zodra de adjacency aangaat, en blijven fiets-tikken op het fietspad?
- **telrapport leest de recon-ZIP.** De export is profiel-bewust gemaakt zodat auto/fiets hun eigen schema (mét `_straten.csv`) behouden en telrapport ze via het bestaande auto-pad leest. Te bevestigen: laadt een vers gemaakte `_recon.zip` correct in telrapport? (Oude recon-ZIP's met pocket-schema laden niet — opnieuw exporteren.)
- **building_passage / steps in de fetch.** De bbox-query is uitgebreid met `tunnel=building_passage` (naast `highway=steps`, dat al in `HIGHWAY_RE` zat). Te bevestigen op een route die door een doorgang of over een trap loopt.

### Grote lijn (Jay's eindplan)
- **Reconstructie als default-voorstap.** Zodra de reconstructie op alle teltypes bevestigd is, wordt "elke telling eerst door reconstruct" de standaard-handeling (desnoods later geautomatiseerd).
- **Eén snap-motor.** Daarna kan `reassignTrajectory` uit pocket (en de snap-logica uit telrapport) worden verwijderd — de reconstructietool is dan de enige snap-motor, geen drift meer. De motor is met het oog hierop al byte-identiek overgezet.
- **Vierde teltype = vierde profiel.** De profiel-architectuur is zo opgezet dat een nieuw teltype één profiel toevoegen is, geen motor-wijziging.
- **Brede telrapport-fix.** Optioneel: telrapport één universeel recon-schema laten lezen in plaats van vier teltype-paden. De profiel-export groeit nu al naar een gemeenschappelijk formaat toe (ontbrekende velden worden aangevuld), zodat deze stap later klein is.

### Winkelstraat
- `winkelstraat_rekenrig.html` (moving-observer footfall-estimator, `q = 3600·m/(L/v_voet + t)`, ratio-of-sums pooling, 7×24 grid) is als prototype meegeleverd, veldgevalideerd, maar **nog niet in de suite geïntegreerd**.

### Langere backlog (uit eerdere releases)
- Pocket drag-correctie voor sleep-modus (raakt snap_trace/segment-snap-model).
- `gebiedsnaam` in `_sessie.csv` (KNIME sign-off).
- Planning/Opdrachten download-als-vangnet.
- Viterbi-merge, capaciteit snap-port, transect-detailtabel, Moving Observer round-trip voor bidirectionele footfall.
