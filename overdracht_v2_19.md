# TrafficCounterSuite v2.19 — Overdracht

Deze release draait volledig om `parkeer_reconstructie.html`: de reconstructor uit v2.18 is uitgegroeid van een parkeer-nabewerker tot een **volwaardige nabewerker voor alle teltypes**, met een aantal grote nieuwe mogelijkheden. In het kort: **(1)** het `_straten.csv`-schema is profiel-bewust gemaakt (fiets-schemagat gedicht); **(2)** alle vier de pocket-modi (parkeren, transect, winkelstraat, simpel) hebben nu een reconstructieprofiel, waarbij transect/winkelstraat/simpel als moving-observer-wandelingen op de link zelf worden geplaatst; **(3)** stipkleuren en legenda passen zich aan het teltype aan; **(4)** `_bezocht.csv` wordt herbouwd uit de Viterbi-route, zodat spook-"gelopen" segmenten verdwijnen; **(5)** OSM-fetches worden per tegel in IndexedDB gecachet en hergebruikt, zodat de Overpass-servers minimaal belast worden; **(6)** meerdere ZIP's tegelijk erin slepen levert een batch van losse recon's; plus knop- en auto-download-verbeteringen. Tot slot leest **`telrapport.html`** de zero-visited nu uit de herbouwde `bezocht` in plaats van uit geometrisch GPS-raden.

Alles is veldgedreven: echte transect-, winkelstraat- en simpel-ZIP's stuurden elk profiel, en de cache/batch is getoetst tegen een echte veldbatch van 56 sessies. Additief waar het bestaande logica raakt; byte-identiteit bewaakt op alle ongewijzigde bestanden.

---

## Gewijzigde en nieuwe bestanden

| Bestand | Status | Kern van de wijziging |
|---|---|---|
| `parkeer_reconstructie.html` | ✦ bijgewerkt | (1) `herberekenStraten` profiel-gedreven; (2) `wandelProfiel`-fabriek + herken-tautologie weg + plaats-op-link; (3) profiel-afhankelijk kleurregister + dynamische legenda; (4) `herbouwBezocht` uit de Viterbi-route; (5) OSM-tegelcache in IndexedDB (`OSMCACHE`, `cacheGefetchteRoute`); (6) batch-verwerking (`verwerkBatch`), gedeelde bouwstenen (`leesZipInS`/`bereidVoor`/`bouwZipBlob`); knop-re-enable + auto-download; versievlag → `v2.19` |
| `telrapport.html` | ✦ bijgewerkt | (8) Zero-visited voor recon-ZIP's uit de herbouwde `_bezocht.csv` (`n_tellingen=0`) i.p.v. `detectZeroVisited`; rauwe ZIP's houden het oude gedrag |
| `overdracht_v2_19.md` | ✦ nieuw | Dit document |

Ongewijzigd (byte-identiek): `pocket_count.html`, `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html`, `traffic_counter.html`, `telplanning.html`, `snaptrace.html`, `snap_methodology.html`, `zip_format_reference.html`, `index.html`, `README.md`, `winkelstraat_rekenrig.html`, `build_bezocht.py`, `planningen/*`, `_archief/*` en alle eerdere overdrachten.

**Schema-signalen voor KNIME.** De recon-ZIP heeft nieuwe/andere outputs die sign-off vragen vóór ze de pijplijn in gaan:
- **`_bezocht.csv` is nu een gereconstrueerd product**, herbouwd uit de Viterbi-gematchte GPS-route (zelfde schema als `pocket_count`: `sessie_id;datum;osm_way_id;segment_index;segment_count;straat;start_tijd;eind_tijd;duur_sec;n_gps;n_tellingen`). Het live-origineel blijft als `_bezocht_origineel.csv` bewaard.
- **Wandelprofielen leveren een eigen `_telregels.csv`-schema** (transect/winkelstraat/simpel), zónder `lat_marker`/`lon_marker`/`zijde` (die horen bij het parkeer-zijdenmodel) en mét `conf;conf_level;gps_stab;gps_level;recon_status`. `richting` alleen bij transect (a/b). Auto/pocket-parkeren/fiets houden hun bestaande schema.
- **Fiets levert nu een correct herberekend `_straten.csv`** (`fiets;brommer;breed;wrak;totaal`) in plaats van het foutieve auto-kopje met nullen.
- De `reconstructie`-vlag in `_sessie.csv` staat nu op `v2.19`.

---

## Deel 1 — Straten profiel-bewust (fiets-schemagat)

**Aanleiding.** `herberekenStraten` hardcodede het auto-schema (`goed;fout;leeg;spec;bezet;vrij;bezettingsgraad_pct`) op drie plekken: de teller-init, de header en de rij-opbouw. Voor fiets is dat schema fout — `fietsparkeren.html` exporteert `fiets;brommer;breed;wrak;totaal`. Een fiets-ZIP door de reconstructor leverde daardoor stil een `_straten.csv` met het verkeerde kopje en nul-tellingen in alle kolommen.

**Fix.** Een vijfde profiel-verantwoordelijkheid `straten` naast de bestaande (herkenning, zijde/richting, highway-voorkeur, telexport): `{ typen, header, rij(sid,naam,ways,agg,orig) }`. `herberekenStraten` is nu motor-neutraal — het initialiseert de teller uit `profiel.straten.typen`, schrijft de header en de rijen via het profiel. Auto telt `goed/fout/leeg/spec` opnieuw en draagt `bezet/vrij/bezettingsgraad_pct` **ongewijzigd** uit het origineel mee (herberekening daarvan wacht op de ombouw van de parkeertelling zelf). Fiets telt `fiets/brommer/breed/wrak` met `totaal` als som. De way→straat-mapping, centroïden en de uitbreiding met nieuwe ways blijven schema-neutraal en ongewijzigd.

---

## Deel 2 — Pocket-modi als reconstructieprofielen

**Aanleiding.** `pocket_count.html` kent vier modi (parkeren, transect, winkelstraat, simpel), maar er was maar één pocket-profiel — helemaal om het links/rechts-tweezijdenmodel van *parkeren* gebouwd. Erger: de herkenning van `pocket-parkeren` bevatte een tautologie (`... || segment_index !== undefined`), en die kolom bestaat altijd op een met-header geparste CSV. Daardoor werden transect-, winkelstraat- en simpel-ZIP's stil door het parkeermodel gehaald — elke tik kreeg een betekenisloze links/rechts-zijde met loodrechte offset.

**Herken ontward.** `pocket-parkeren` eist nu `modus==='parkeren'` (met een terugval op expliciete `richting ∈ {links,rechts}` voor oude ZIP's). De tautologie is weg.

**wandelProfiel-fabriek.** transect, winkelstraat en simpel zijn wezenlijk één vorm (moving observer: je loopt en tikt onderweg) en delen nu een fabriek `wandelProfiel({label, modus, metRichting})`. Ze verschillen alleen in modus-herkenning en of ze richting a/b dragen (alleen transect). Een nieuwe wandelmodus toevoegen = één regel. De motor koppelt de tik via de bestaande trajectorie-Viterbi aan de gelopen link — dat wás al de kern; wat de wandelmodi nodig hadden was vooral het *afzetten* van de parkeer-staart.

**Plaats-op-link.** Eén profielvlag `opLink:true` en een tak in `reconstrueer()`: vóór de zijde-offsetstap plaatst hij de tik op het Viterbi-snappunt `qM` zelf, zonder loodrechte verschuiving; `maakTap2` houdt de zijde op `'X'`. Richting a/b komt ongewijzigd uit het veld mee (grondwaarheid, zoals auto de veld-zijde draagt), niet geometrisch her-afgeleid. Op de echte transect-demo: 185/185 op de link, zijde overal `X`, de link-koppeling van de motor intact.

---

## Deel 3 — Profiel-afhankelijke stipkleuren en legenda

**Aanleiding.** De stipkleur was hard `bezet ? rood : groen` en de legenda statische HTML met "bezet / leeg" — voor elk teltype hetzelfde. Wandeltypes (tegemoet/stilstaand, car/truck/…, ped) zijn bovendien vrij configureerbaar en dus niet vooraf vast te leggen.

**Fix.** Eén kleurregister (`bouwTypeKleuren`) dat zowel de stippen als de legenda voedt, afgeleid uit de types die echt geplot worden. Profielen met vaste, betekenisdragende categorieën (parkeren/auto/fiets) geven een `kleuren:{type→kleur}`-map mee (bezet=rood/leeg=groen blijft identiek aan vroeger); vrije wandeltypes rouleren automatisch door `PALET`. `zetLegenda` bouwt de legenda uit datzelfde register; de "richting onzeker"-regel verschijnt alleen als er echt onzekere tikken zijn (wandelprofielen kennen die status niet). De tooltip is adaptief: richting alleen bij a/b, zijde alleen bij L/R — geen lege "· (X)" meer bij wandelingen.

---

## Deel 4 — `_bezocht.csv` herbouwd uit de Viterbi-route

**Aanleiding.** De live-snap markeerde door GPS-ruis segmenten als "gelopen" die je niet liep. Die spoken zaten in de originele `_bezocht.csv` (en werden door de reconstructor onveranderd doorgegeven) én in wat telrapport tekende.

**Fix.** `herbouwBezocht` loopt de Viterbi-gematchte GPS-fixes chronologisch langs, knipt in aaneengesloten runs per (way, segment) met dezelfde drempels als `pocket_count.buildBezochtCsv` (gap 30 s, minimaal 5 s en 3 punten), en telt de gereconstrueerde tikken per venster. Straatnamen komen uit de originele snap (het netwerk zelf draagt geen naam). De spoken staan niet in de Viterbi-route en verdwijnen zo bij de bron; het resultaat is bovendien consistent met de telregels. Het origineel blijft als `_bezocht_origineel.csv` bewaard. Op de echte winkelstraat verdween o.a. `241007779 Noordkade` (leeg) en de sub-meter-kruispuntknoop `130419432`.

---

## Deel 5 — OSM-tegelcache (minimale Overpass-belasting)

**Aanleiding.** De meeste tellingen liggen in hetzelfde gebied en haalden bij "verversen" steeds dezelfde OSM-data op.

**Fix.** Een vast tegelraster (`TILE_DEG = 0.01°` ≈ 0,7–1,1 km). Bij verversen berekent `coveringTiles` de dekkende tegels, checkt IndexedDB (`OSMCACHE`) op verse tegels (< `CACHE_TTL_MS`, 60 dagen), en haalt **alleen de ontbrekende** op — in één gebundelde Overpass-call over hun omhullende bbox (`cacheGefetchteRoute`). De rauwe elements worden genormaliseerd (`{type,id,nodes,geometry,tags:{highway}}`) en over hun tegels verdeeld opgeslagen; daarna assembleert `dedupeWays` het netwerk uit alle dekkende tegels en bouwt `verwerkOsmWays` rijen + node-adjacency. De dag-snapshot `_netwerk.csv` blijft grondwaarheid; de cache voedt alleen het verse netwerk.

**Details.** `coveringTiles` gebruikt half-open intervallen (`ceil-1`) voor de bovenrand, anders wordt bij een grens-exacte bovenrand stelselmatig een tegelrand te veel opgehaald (kostte 3× de data op een koude fetch). De IndexedDB-transacties geven alle requests synchroon uit binnen één transactie. Er is een "OSM-cache legen"-knop; zonder IndexedDB valt de tool terug op een gewone volledige fetch.

---

## Deel 6 — Batch-verwerking

**Aanleiding.** In het veld staan tientallen sessies klaar; die één voor één door de tool halen is omslachtig.

**Fix.** Meerdere ZIP's tegelijk erin slepen → `verwerkBatch` verwerkt ze **sequentieel**: laden, netwerk via de tegelcache verversen, reconstrueren, los downloaden, dan pas de volgende. Sequentieel is bewust: de eerste sessie vult de cache, elke volgende in hetzelfde gebied hergebruikt de tegels — een hele batch belast Overpass nauwelijks meer dan één telling. De kaart wordt overgeslagen (`S.batchModus`), een bestand dat faalt wordt overgeslagen met een melding, de rest loopt door. Eén bestand → gewone interactieve modus. Onder de motorkap gedeeld: `leesZipInS` (CSV's), `bereidVoor` (schaal/bbox/origineel netwerk) en `bouwZipBlob` (het ZIP-blob) worden door zowel de interactieve als de batch-route gebruikt.

---

## Deel 7 — UI: knoppen en auto-download

- **Verversen-knop weer aanzetten bij een nieuwe ZIP** — in beide takken van het laadpad wordt `fetchBtn.disabled = false` gezet; na een geslaagde verversing blijft hij bewust uit tot de volgende ZIP.
- **Knopvolgorde** — bovenaan de primaire "Herschreven ZIP downloaden", daaronder de optie "automatisch downloaden na verversen", daaronder de twee netwerk-utilities (verversen + cache legen) gegroepeerd.
- **Automatisch downloaden** (standaard aan, uitzetbaar) — gekoppeld aan *na verversen*, niet aan elke reconstructie. Bij laden draait er eerst een preview op het bestaande netwerk; het goede resultaat komt na verversen. Zo krijg je één bestand (het goede) i.p.v. een preview plus de echte.

---

## Deel 8 — telrapport: zero-visited uit de herbouwde `bezocht`

**Aanleiding.** telrapport tekende foutieve "gelopen, geen waarnemingen"-markers via `detectZeroVisited`, dat elk GPS-punt puur geometrisch naar het dichtstbijzijnde segment snapt (≥ 3 hits) en zo door GPS-ruis spooksegmenten oplevert.

**Fix.** In `loadPocketZip` haalt de zero-visited-detectie voor gereconstrueerde ZIP's (herkenbaar aan de `reconstructie`-vlag in `_sessie.csv`) de segmenten uit de herbouwde `_bezocht.csv` — visits met `n_tellingen=0` zijn de écht belopen-maar-lege segmenten. `detectZeroVisited` wordt dan overgeslagen; `addPocketZero` en de rendering blijven identiek. Rauwe ZIP's (zonder vlag) houden het oude gedrag. Chirurgische wijziging: één blok in `loadPocketZip`, verder niets aan telrapport geraakt.

---

## Validatie

Op elk build-blok:
- **`node --check`** op de geëxtraheerde inline-JS van beide bestanden — schoon.
- **HTML tag-balans** via een echte parser met scripts/styles gestript — schoon.
- **Diff tegen de v2.18-baseline** per regio-hunk; alle overige suite-bestanden **byte-identiek** (bevestigd met `cmp`).

Functioneel, headless in een Node-sandbox met echte PapaParse en de echte motor:
- **Straten-schema's** — auto (types herteld, bezet/vrij/graad ongewijzigd overgenomen, way-hertoewijzing naar de dichtstbijzijnde straat), fiets (`totaal` = som), lege-straat-edge (nul + origineel tijdvenster behouden).
- **Profielkeuze** — alle acht gevallen correct: pocket-parkeren (modus + oud), transect, winkelstraat, simpel, onbekende modus → fallback, auto, fiets.
- **Wandelprofielen** op echte transect-, winkelstraat- en simpel-ZIP's — juist profiel, alles op de link (zijde `X`), richting-kolom alleen bij transect.
- **Kleurregister/legenda** — semantische kleuren voor parkeren/auto/fiets (bezet/leeg identiek aan vroeger), dynamisch palet voor de wandeltypes; onzeker-regel alleen bij onzekere tikken.
- **`herbouwBezocht`** — transect/simpel/winkelstraat: consolidatie naar de Viterbi-route, lege spooksegmenten verdwenen; elke tik in de telregels blijft correct gekoppeld.
- **Tegelcache** met gestubde IndexedDB + Overpass — koud (1 call, exacte tegels), warm (0 calls), partiële overlap (alleen de nieuwe tegels, 1 call), dedup over tegelgrenzen, TTL-verval → refetch, fallback zonder IndexedDB.
- **Batch** op drie echte tellingen — 3 correcte `_recon.zip`-downloads met de volledige set (incl. herbouwde `bezocht` en bewaarde originelen); skip-bij-fout (2 van 3, met melding welke werd overgeslagen); `batchModus` netjes gereset.
- **telrapport** met gestubde Leaflet/DOM — recon-ZIP: `detectZeroVisited` niet aangeroepen, zero-visited uit `bezocht` matcht exact de `n_tellingen=0`-visits; rauwe ZIP: `detectZeroVisited` draait weer.

Veld: de batch is in de praktijk gedraaid — **56 sessies succesvol naar `_recon` geschreven.**

**Nog in de browser te bevestigen (niet in de sandbox toetsbaar):** de live Overpass-fetch + echte IndexedDB-persistentie tussen sessies; het daadwerkelijk los downloaden van een batch (browser vraagt eenmalig "meerdere downloads toestaan"); auto-download vlak na de verversen-klik. En op de kaart: of de forse link-herzieningen (~47 % t.o.v. de veld-snap) rond passages en de `130419432`-kruispuntknoop stuk voor stuk verbeteringen zijn, of de Viterbi ergens te plakkerig één way vasthoudt, en de naamloze way `238069263` (die de live-snap nooit gebruikte).

---

## Backlog (bijgewerkt)

### Afgerond deze release
- Fiets-`_straten.csv`-schema gedicht (profiel-gedreven `herberekenStraten`).
- Alle vier pocket-modi als reconstructieprofiel (parkeren/transect/winkelstraat/simpel); herken-tautologie opgeruimd.
- Profiel-afhankelijke stipkleuren + legenda.
- `_bezocht.csv` herbouwd uit de Viterbi-route (+ `_bezocht_origineel.csv`).
- OSM-tegelcache in IndexedDB (minimale Overpass-belasting).
- Batch-verwerking (zes losse recon's uit zes ZIP's).
- Knop-re-enable + knopvolgorde + auto-download.
- telrapport zero-visited uit de herbouwde `bezocht`.

### Losse eindjes / voor een volgende sessie
- **Link/segment-samenvatting voor wandelmodi** (tellingen per link × richting × categorie voor transect/winkelstraat/simpel) — bewust uitgesteld tot alle teltypes een profiel hadden; dat is nu zo, dus dit kan opgepakt worden. Let op: wandel-ZIP's bevatten géén `_straten.csv`, dus deze samenvatting bouw je van nul uit de gereconstrueerde tikken (ander bouwpad dan auto/fiets, die een origineel verfijnen).
- **Kaart-validatie van de link-herzieningen** (zie Validatie) — steekproef van de ~47 % verschoven tikken rond passages/kruispunten.
- **Twee kleine live-verbeteringen in pocket** (uit v2.18, nog open): `fetch_fail`-trace-events per mislukte poging, en een sequence-guard tegen out-of-order fetch-antwoorden die `cacheLat/Lon` overschrijven.

### Wacht op andere trajecten
- **Bezettingsgraad-herberekening voor auto** (`bezet`/`vrij`/`bezettingsgraad_pct`) — wacht op de ombouw van de parkeertelling zelf; nu ongewijzigd overgenomen uit het origineel.
- **`gebiedsnaam` in `_sessie.csv`** — vereist KNIME sign-off.
- **Per-categorie parallelle-link-toewijzing** (auto-tik → rijbaan, fiets/voetganger → fietspad/stoep) — expliciet buiten scope: breekt de route-consistentie van de Viterbi en de parallelle geometrie staat vaak niet apart in OSM. Wandeltikken landen op de link onder de gelopen route.

### Principes bevestigd deze sessie
- **Ontwerpen en veld-valideren vóór bouwen**; drempels en profielen tegen echte CSV-replay getoetst.
- **`wandelProfiel`-fabriek** houdt de drie moving-observer-modi DRY — één plek om te onderhouden.
- **De motor koppelde tikken al route-consistent aan een link**; wandelmodi hoefden vooral het parkeer-zijdenmodel *af* te zetten, niet een nieuwe matcher toe te voegen.
- **`bezocht` is nu een gereconstrueerd product**, net als telregels en straten — spoken verdwijnen bij de bron.
- **Tegel-cache met half-open intervallen** en één gebundelde fetch over het ontbrekende: maximaal hergebruik, minimale OSM-belasting.
- **Additief en byte-identiteit-bewaakt**; alleen de twee geraakte bestanden wijzigen, de rest van de suite blijft ongemoeid.
