# TrafficCounterSuite v2.9 — Overdracht

Release rond drie thema's: **veldleesbaarheid & signaalvertrouwen** in Pocket (straatnaam in fel licht, een tweede stip voor GPS-stabiliteit, een batterij-indicator), **een slimmere trajectorie-reconstructie** (een echte bug in de backtrack gefixt, een koers-term toegevoegd), en **harmonisatie + opschoning van de parkeer-apps** (de volledige scan-lijst opgelost, twee structurele snap-/GPS-fixes, en de laatste verstopte domein-keuze expliciet gemaakt). Daarnaast een interne opschoning: de snap-state in Pocket zit nu in één namespace-object i.p.v. losse globals.

---

## Gewijzigde bestanden

| Bestand | Status | Kern van de wijziging |
|---|---|---|
| `pocket_count.html` | ✦ bijgewerkt | straatnaam-leesbaarheid + stip, GPS-stabiliteitsindicator (+ CSV-kolommen), batterij-indicator, piecewise backtrack-fix, koers-term, `snap`-namespace |
| `parkeertelling.html` | ✦ bijgewerkt | scan-lijst (10 + neefje), cumulatieve snap, off-by-one, `FORCE_CYCLE_TO_ROAD`-vlag |
| `fietsparkeren.html` | ✦ bijgewerkt | idem parkeertelling, voor zover van toepassing |
| `snap_methodology.html` | ✦ bijgewerkt | §7 herschreven (reassign + koers-term + piecewise backtrack), §1/§5/§8 correcties, §3 candidate-accumulatie, mechanisme in gewone taal |
| `zip_format_reference.html` | ✦ bijgewerkt | `conf`/`conf_level` (v2.8) en `gps_stab`/`gps_level` (v2.9) gedocumenteerd, trajectorie-correctie-noten |
| `traffic_counter_help.html` | ✦ bijgewerkt | extern herschreven versie overgenomen als suite-versie, 7 gaten gevuld, "twee stippen"-uitleg |

Ongewijzigd: `capaciteitstelling.html`, `telplanning.html`, `telrapport.html`, `telrapport_viterbi.html`, `snaptrace.html`, `traffic_counter*.html`, `build_bezocht.py`, `index.html`, `README.md`, `planningen/*`.

---

## pocket_count.html

### 1 · Leesbaarheid in fel licht
De straatnaam onder het telgetal viel weg in zonlicht (half-transparant wit, klein, geen rand).
- Straatnaam: `clamp(17px, 5vw, 26px)`, vol-wit, gewicht 600, donkere `text-shadow`-omlijning zodat hij tegen elke achtergrondkleur leesbaar blijft. Container 80→88vw zodat lange namen niet vroeg afkappen.
- Snap-stip vergroot (13→18px) met witte ring; rood/amber iets verzadigder voor beter onderscheid.

### 2 · GPS-stabiliteitsindicator (tweede stip)
Naast de snap-stip (welke straat) staat nu een **open ring** die de signaalkwaliteit toont, los van de straatkeuze.
- `gpsUpdateStability(lat, lon, acc, tsMs)` draait op élke fix. Venster van 15 s (`GPS_WIN_MS`), mediaan + MAD.
- **Zelf-kalibrerend**: een "sprong" = snelheid > mediaan + `GPS_JUMP_K`·MAD (= 3.5) over het venster — geen vaste m/s-drempel, dus fietsen telt niet als sprong.
- Zwakste-schakel van drie deelscores: sprong, koers-consistentie (`GPS_TURN_DEG`), gerapporteerde nauwkeurigheid (`GPS_ACC_GOOD/BAD`). EMA-gesmoothed; grijs tot ≥3 fixes; gecachete dubbele fixes worden overgeslagen.
- Per tik weggeschreven als `gps_stab`/`gps_level` in `_telregels.csv` (beide tap-paden) en als extra kolommen in `_snap_trace.csv` — telkens áchteraan, dus oudere lezers blijven werken. Geverifieerd: fietsen→groen, sprong→amber, zigzag/slechte acc→rood.

### 3 · Batterij-indicator
Klein staafje (andere vorm dan de stippen) in dezelfde rij. Event-gedreven via `getBattery()` + `levelchange`/`chargingchange`. Groen >30%, amber 15–30%, rood <15%, amber-vloer + bliksem bij opladen. iOS-veilig: verborgen als de API ontbreekt.

### 4 · Piecewise backtrack in `reassignTrajectory` (bugfix)
Bij een onderbreking (een kolom zonder topologisch verbonden kandidaat — een GPS-sprong of een gat in de OSM-dekking) deed de Viterbi een harde reset met `back=null`. De backtrack cascadeerde die `null` daarna helemaal terug naar fix 0, waardoor **alles vóór de eerste onderbreking ongecorrigeerd terugviel op de live-snap**.
- Opgelost met een stuksgewijze backtrack: bij een segment-grens (`back==null`) start een nieuwe backtrack vanaf de beste staat van de bovenliggende kolom (`bestStateOf`), in plaats van de hele voorgeschiedenis weg te gooien.
- Bewezen: synthetisch herstelt OUD 2/7 fixes, NIEUW 7/7 (exact de grondwaarheid). Op veldsessie `20260520_145913_txb_pkt` liet OUD 3 fixes zonder way; NIEUW 0, tikken 131/131 behouden.

### 5 · Koers-term in `reassignTrajectory` (v2.9)
De transitie had alleen een magnitude-check (`γ·|projStep − gpsStep|`), geen richting. Toegevoegd: per kandidaat `β·w·(Δ/90°)`, met Δ = hoek (mod 180°, ways zijn richtingloos) tussen de GPS-stap-koers en de lokale way-koers op het projectiepunt, `w = min(1, gpsStep/10 m)` (korte ruizige stappen tellen nauwelijks), en `β = 2` — bewust kleiner dan de single-hop-kost (4), zodat koers gelijkwaardig-verbonden kandidaten kan scheiden maar de topologie-hiërarchie nooit omverduwt.
- Vooronderzoek op de ZIP toonde dat ~89/121 ambigue fixes een top-2 met ≥30° koersverschil hebben → reële winst.
- Geverifieerd vóór porten: 3/123 fixes kantelen, alle drie in een overgang waar de wandelaar onmiskenbaar op de nieuwe way liep, juist tijdens een stuk met acc 29–49 m waar afstand niets meer zegt. Tikken 131/131 behouden, junction-tikken 28/29/44/45 ongewijzigd. In-file versie diff-identiek aan de geteste harnas-versie.
- Helpt niet bij een echte gedeelde-knoop-junction (alle ways gaan door hetzelfde punt) — dat blijft de irreducibele rest.

### 6 · `snap`-namespace (interne opschoning, Vorm 2)
Alle 19 losse mutable snap/GPS-state-globals zitten nu in één benoemd `snap`-object (`snap.elements`, `snap.adjacency`, `snap.anchorWayId`, `snap.confScore`, `snap.gpsStabScore`, `snap.trace`, …). ~200 gebruikssites meegehernoemd. Constanten blijven gewone globals; functies houden hun `snap*`-prefix. Geen gedrag gewijzigd — Viterbi- en stabiliteitstests identiek na de hernoeming. Bewust géén closure/getters (verbergen levert voor een één-auteur-veldtool weinig op en is het risicovolle deel).

---

## parkeertelling.html & fietsparkeren.html

Beide apps zijn nu structureel identiek (68 gedeelde functies; enige unieke functie is `loadCapNetwerk` in auto). Alle onderstaande fixes zijn in beide doorgevoerd tenzij anders vermeld.

### Scan-lijst (10 punten + neefje)
1. **Auto-download bij scherm-uit/app-switch weg.** `safetyDownload()` slaat nu alleen op (`saveSession`); geen `exportCSV()`/`exportMapCanvas()` meer die downloads triggerde én de herstelkopie wiste. `beforeunload`-waarschuwing blijft.
2. **Share wist de back-up niet meer te vroeg.** `clearSession()` + vlaggen zitten nu in `finalizeExport()`, dat pas draait ná een geslaagde `navigator.share` (`.then`) of ná de fallback-download (`.catch`/non-share).
3. **GPX `<n>` → `<name>`** (3 plekken per app; was ongeldig GPX).
4. **Kantel-crash.** Parkeren-default `'goed'` i.p.v. ongeldig `'fiets'`; vangnet `if (!counts[type]) return;` in `addEntry` (beide).
5. **prev/current off-by-one** (zie structureel, hieronder).
6. **Cumulatieve snap** (zie structureel, hieronder).
7. **`cap_netwerk.csv`** (auto): relatief pad i.p.v. absoluut; geen `setStatus` meer bij ontbreken (alleen `console.warn`) → geen 404-ruis in de statusbalk.
8. **`!false`-scaffolding** (auto) verwijderd → zie `FORCE_CYCLE_TO_ROAD` hieronder.
9. **`saveSession` undo-tot-nul** ruimt nu de stale herstelkopie op (`removeItem(LS_KEY)`) i.p.v. te blijven staan.
10. **Klein** (visited-highlight niet persisted; dubbele snap per fix; aggregatie op geocode-label) — bewust niet aangeraakt, gedocumenteerd als bekend.
- **Neefje:** `exportCSV()` wist de herstelkopie niet meer (tussenexport); `clearSession()` gebeurt nu alleen bij sessiestart en bij de volledige ZIP-export.

### Structureel · cumulatieve snap-kandidaten
`roadSegs` werd per fetch herbouwd uit alleen de verse Overpass-cirkel (en zelfs vóór de accumulatie). Nu: eerst accumuleren in `osmNetworkElements` (dedup op `id`, bestond al), dan `roadSegs` bouwen uit `elementsNear(lat, lon, SNAP_SEGS_RADIUS)` — alle eerder gevonden ways met een knoop binnen 480 m (`ROAD_FETCH_RADIUS × 1.6`), herprojecteerd op het huidige centrum. Spiegelt Pocket's `snapElementsNear`. Bewezen op het walk-back-geval: een weg die net buiten de verse fetch-cirkel valt blijft een snap-kandidaat (oud: viel weg, snap mislukte).

### Structureel · prev/current off-by-one
`moved` en `calcBearing` rekenden tegen `prevLat` (twee fixes terug) door de bookkeeping-volgorde. Nu tegen `currentLat`/`currentLon`, die bovenin `onPosition` juist de vorige fix vasthouden → opeenvolgende fixes. De ongebruikte `prevLat`/`prevLon` (decl, reset, lag-toewijzing) zijn schoon verwijderd.

### `FORCE_CYCLE_TO_ROAD` — verstopte domein-keuze geëxpliciteerd
Het "forceer naar rijweg"-blok stond in auto als `!false` (aan) en in fiets als `!true` (uit) — bewust verschillend (auto's parkeren op de rijweg, fietsen niet) maar verwarrend uitgedrukt. Vervangen door een benoemde vlag `var FORCE_CYCLE_TO_ROAD = true;` (auto) / `false` (fiets) en de symmetrische conditie `if (FORCE_CYCLE_TO_ROAD && …)`.

### Bedoelde verschillen auto vs. fiets (ter referentie)
Teltypes (`goed/fout/leeg/spec` vs `fiets/brommer/breed/wrak`), snap-voorkeur (`snapWeight(…,false)` rijwegen vs `(…,true)` fietspaden), `FORCE_CYCLE_TO_ROAD`, `loadCapNetwerk` (alleen auto), identiteit (titel/`LS_KEY`/GPX-naam/bestandsprefix/zip-suffix `_car`/`_fts`), accentkleur (paars vs oranje).

---

## snap_methodology.html

- §7 (Offline trajectory reassignment) bevat nu de **koers-term** (β/HEAD_REF_M, mod-180°, weging) en de **piecewise backtrack** (met de 3-herstelde-fixes-bevinding). §8 legt uit waarom koers de gedeelde-knoop-junction alsnog niet redt.
- Het **mechanisme is herschreven in gewone taal** (stap-voor-stap, geen pseudocode/Viterbi-jargon), met een aparte alinea "waarom offline beter is dan real-time".
- Eerdere correcties: §1 (de `20260520`-ZIP is een junction-convergentie, geen disconnected-ways-geval), §5 (`SNAP_RESET_M` = 50 m, `SNAP_SEGS_RADIUS` toegevoegd), §3 (cumulatieve candidate-accumulatie).

## zip_format_reference.html
`_telregels.csv` gedocumenteerd met `conf`/`conf_level` (v2.8) en `gps_stab`/`gps_level` (v2.9), plus de trajectorie-correctie-noten op telregels/gps/bezocht. `telrapport.html` leest header-gebaseerd (Papa Parse `header:true`) — extra kolommen breken niets (geverifieerd).

## traffic_counter_help.html
Extern herschreven versie overgenomen als suite-versie. Zeven gaten gevuld (Planning & Rapportage-kaart, telprotocol, plaats/start-einde, keuzes-intro + lijst, twee waarnemers) en de foutparkeren-markup opgeschoond. De Pocket-helpkaart "De twee stippen & de straatnaam" legt snap-stip én GPS-ring uit met kleurtabellen en de CSV-verwijzing.

---

## Afgehandeld / gesloten

- **Oude snap-bug** (tikken 28/29/44/45 op way 130419432, ZIP `20260520_145913_txb_pkt`): geherclassificeerd als **knooppunt-ambiguïteit** en gesloten. Faithful nadraai toonde dat de drie kandidaat-ways binnen sub-meter samenkomen (0.7 m « GPS-acc 8–19 m) — geen mis-snap maar een irreducibel gedeelde-knoop-geval.

## Backlog (open)

- **Harmonisatie**: `saveBlob`-download en de `snap`-namespace (Vorm 2) nog doortrekken naar `parkeertelling`/`fietsparkeren`/`capaciteitstelling`/`traffic_counter`; capaciteitstelling-header-bug.
- **README**: `kruispunttelling.html` is uit de suite — verwijzingen opschonen.
- **Hoogtesignaal**: `altitude`/`altitudeAccuracy` voor roltrap/trap-detectie (de enige uitweg uit de verticale-samenval-grens).
- **Vlak-snappen** voor open pleinen (`area`/`pedestrian`-polygonen i.p.v. lijnen) — grotere architectuur-vraag.
- **`wid`/`wayId`-naamgeving** consistent maken.
- Kleinere parkeer-punten uit de scan (#10): visited-highlight persisteren, dubbele snap per fix, aggregatie op `osmName` i.p.v. geocode-label.
- Losse `exportCSV`-`clearSession` is al weg; geen open data-kritische punten meer in de parkeer-apps.
