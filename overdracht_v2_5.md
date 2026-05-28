# TrafficCounterSuite v2.5 — Overdracht

Een release met drie kleine, geïsoleerde uitbreidingen: stand-still telling als kaartbare telsoort, dag-filter in de tijdbalk, en tweetalige voorpagina. Geen breaking changes, geen dataformaat-wijzigingen, geen aanpassingen aan bestaande laders.

## Hoogtepunten

- **Stand-Still als telsoort in telrapport**: traffic_counter.html CSVs worden direct geaccepteerd, verschijnen als pin op de kaart met klik-popup. Pin-grootte schaalt met passages/uur. Popup toont samenvattingstabel (per voertuigtype × richting) plus tijdreeks (stacked bars per type, x = tijd, y = passages per bucket).
- **Dag-filter in tijdbalk**: pill-rij Alle/Werkdagen/Za/Zo combineert met het bestaande uurvenster (AND-logica). Sessies buiten de dag-categorie tonen als dot op de juiste uurpositie — bestaan zichtbaar maar verborgen op kaart.
- **Voorpagina tweetalig**: NL/EN toggle rechtsbovenin index.html. Browser-detect (begint met `nl` → Nederlands), keuze blijft sticky via localStorage. Andere pagina's nog Engels.

## Per bestand

### telrapport.html

**CSV-acceptatie naast ZIP.** Dropzone-input `accept=".zip,.csv"`. Nieuwe wrapper `loadFile(file)` routeert op extensie naar `loadStandStillCsv` of de bestaande `loadZip`. Multi-select met gemengde types werkt zonder verdere logica.

**Parser** (`parseStandStillCsv`) is een drie-state machine: metadata key-value, samenvattingstabel (na `Vehicle Type;` header), timestamp-log (na `Time;Vehicle;Direction` header). Richtingen worden dynamisch uit de samenvattings-header gelezen — vrije-tekst namen ("Van Abbenbroek naar Poortugaal", "North", etc.) werken automatisch.

**Vehicle-lookup tolerant.** Map `SS_VEHICLE_LOOKUP` herkent zowel emojis (🚗, 🚛, 🏍, 🚲, 🚶 — oude CSVs van vóór de v2.4 vehicle-type-tekst-fix) als labels (Car, Truck, Motorcycle, Bicycle, Pedestrian). Beide formaten matchen op dezelfde type-code.

**Sessie-id constructie**: `ss_` + compacte ISO-timestamp van `Start time` (`ss_20260522_165752`). Stabiel — herladen van dezelfde CSV geeft dezelfde id, dus duplicate-detectie via `if (sessions[sid]) return;` werkt automatisch.

**Marker**: `L.circleMarker` met sessiekleur, radius `clamp(8 + √(perHour) × 1.2, 8, 28)`. Bij `accuracy >= 25m` wordt een gestreepte `L.circle` toegevoegd met de accuracy als radius — visuele eerlijkheid over GPS-betrouwbaarheid.

**Popup**: header (locatie + datum + duur + GPS-accuracy ± reliable-flag) + samenvattingstabel + tijdreeks. Tabel toont alleen voertuigtypes met `>0` tellingen, eindigt met `geteld` en `per uur` rijen. De per-uur rij gebruikt de in de CSV opgenomen extrapolatiefactor — niet het simpele `total × 3600/durSec` — zodat de waarde matcht met de getoonde getallen in traffic_counter.html.

**Tijdreeks** (`renderStandStillTimeline`): inline SVG, stacked bars per voertuigtype. Bucket-grootte adaptief: 30s bij <25 min, 60s bij 25-45 min, 120s bij 45-90 min, 300s daarboven. Eén event in de timestamp-log per tap, plaatsing in bucket op basis van offset vanaf `start`. Y-as op nette gehele waarden (multiples van 5 boven de 5, exact daaronder). Middernacht-passage wordt correct gehandeld via dag-erbij-logica als log-timestamp `< start`.

**Visibility-tak**: `applySessionVisibility` krijgt early return voor `appType === 'standstill'` die alleen marker + ring toggle't. `applyTimeFilter` en `toggleTimeFilter` krijgen dezelfde tak voor consistentie met andere telsoorten.

**Sessions-lijst**: standstill-sessies krijgen 📍-icon. `renderSessions` bestaande code werkt verder ongewijzigd — bestaande `n_waarnemingen` veld in pseudo-meta vult de aantal-kolom.

### telrapport.html — dag-filter

**State**: `currentDayFilter` ∈ `{'all', 'weekday', 'saturday', 'sunday'}`, default `'all'`.

**HTML**: pill-rij in de timebar tussen header en track. Vier knoppen `<button class="day-pill" data-day="...">`. Bestaande slider en dot-canvas ongewijzigd.

**Helpers**:
- `sessionDow(sid)`: parse `meta.datum` (YYYY-MM-DD of YYYYMMDD), `new Date().getDay()`, returnt 0-6 of `null` bij parse-falen.
- `sessionInDayFilter(sid)`: `currentDayFilter==='all'` → true; `null` dow → true (graceful fallback voor sessies zonder geldige datum); anders match op dow.
- `sessionInTimeWindow(sid)`: hergebruik van het bestaande uur-venster-logica.
- `sessionInWindow(sid)`: AND van beide. Alleen actief als `timeFilterActive`.

**AND-logica**: een sessie is zichtbaar in venster als hij in *beide* filters past. Zaterdag-sessies bij Werkdagen+9-11 verdwijnen, en hun dot blijft zichtbaar op de timebar-canvas — visueel signaal "deze bestaat, valt buiten je keuze".

**Sticky**: dag-keuze wordt niet gereset bij timebar uit/aan. Geen localStorage — sessie-leven.

### telrapport.html — niet-stukmaken-belofte

Geraakte regio's (diff `@@`-headers):
- Nieuwe CSS regio (modal + day-pills): regels 196 en 244-298 (CSS-blokken)
- Dropzone tekst + accept: regel 302
- Nieuwe stand-still constants/parser/loader/popup/timeline: regel 690 e.v. (~390 nieuwe regels vóór `loadTransectZip`)
- Standstill icon in renderSessions: één regel-set
- Standstill-tak in applySessionVisibility: vier regels toegevoegd
- Day-filter helpers in sessionInWindow: vier regels toegevoegd
- Day-pill click handler: vier regels in DOM-init
- Standstill in applyTimeFilter en toggleTimeFilter-uit-tak: tien regels

Niet aangeraakt: `loadZip`, `loadPocketZip`, `loadCapaciteitZip`, `loadTransectZip`, `wayData`-mutaties, `clusterLayers`, `dotLayers`, `wayLayers`, `gpsLayers`, `drawClusters`, weekprofile-popup-logica, `APP_CONFIG`. Een v2.3-ZIP gedraagt zich precies zoals in v2.4.

### index.html

**Toggle-UI**: `position: fixed` rechtsbovenin, twee buttons `NL | EN` met onderstreepte actieve taal. Geen branding-toggle of dropdown — bewust minimaal.

**Detectievolgorde**:
1. `localStorage.getItem('tc_lang')` — eerdere keuze wint altijd
2. `navigator.language` — begint met `nl` → Nederlands
3. EN als laatste vangnet

**Mechaniek**: één `i18n` object met `en` en `nl` keys. Elk vertaalbaar element heeft `data-i18n="key"`. `setLanguage(lang)` loopt door alle `[data-i18n]` elementen, vult via `innerHTML` (vanwege `<br>` in titels), update `document.title` en `<html lang>`, toggle't active-class op de buttons.

**Private-mode tolerant**: `localStorage` reads/writes in try/catch. Bij failure: silent fallback op browser-detect.

**Scope**: alleen index.html. Andere pagina's (traffic_counter.html, pocket_count.html, parkeertelling.html, etc.) blijven in hun huidige taal. `traffic_counter_help.html` is bewust niet aangeraakt — die pagina is een tweetalige mengelmoes (secties 1-10 Engels, 11-37 Nederlands, 38 Engels) en vergt structureel werk dat te groot is voor v2.5.

**Default in de bron**: HTML staat in het Engels. JavaScript runt synchroon na DOM-parse en switch direct naar NL als detect dat zegt. Geen flash-of-untranslated-content in praktijk.

### README.md

Versie-string bijgewerkt naar v2.5 met korte release-samenvatting. Rest ongewijzigd.

### overige

- `traffic_counter.html`, `traffic_counter_transect.html`, `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html`, `pocket_count.html`, `kruispunttelling.html`, `telplanning.html`, `traffic_counter_help.html`: ongewijzigd in v2.5.
- `build_bezocht.py`: ongewijzigd. Niet meer nodig voor nieuwe pocket-tellingen (sinds v2.3 schrijft pocket_count zelf segment-aware ZIPs); blijft beschikbaar voor het upgraden van v2.2-archief.
- `zip_format_reference.html`: ongewijzigd.

## Datastructuren toegevoegd

| Variabele | Plaats | Doel |
|---|---|---|
| `standStillData[sid]` | telrapport.html | Parsed CSV per sessie |
| `standStillMarkers[sid]` | telrapport.html | L.circleMarker per sessie |
| `standStillRings[sid]` | telrapport.html | L.circle accuracy-ring (alleen bij >=25m) |
| `currentDayFilter` | telrapport.html | Active dag-filter pill |
| `i18n` object | index.html | Vertalingen NL + EN |

## Helpers toegevoegd

| Functie | Plaats | Doel |
|---|---|---|
| `loadFile(file)` | telrapport.html | Routing op extensie (.csv → standstill, .zip → bestaand) |
| `parseStandStillCsv(text)` | telrapport.html | 3-state CSV parser |
| `ssBuildSid(start)` | telrapport.html | Compact stabiel sessie-id uit start-Date |
| `loadStandStillCsv(file)` | telrapport.html | Async loader: parse + marker + ring + sessie-registratie |
| `openStandStillPopup(sid)` | telrapport.html | Popup-overlay opbouwen + DOM injecteren |
| `renderStandStillTimeline(data, types)` | telrapport.html | Inline SVG timeline met adaptieve buckets |
| `escapeHtml(s)` | telrapport.html | HTML-escape voor user-input (street, notes, richting-namen) |
| `sessionDow(sid)` | telrapport.html | Dag-van-week uit `meta.datum`, robuust tegen formats |
| `sessionInDayFilter(sid)` | telrapport.html | Dag-filter toepassen |
| `sessionInTimeWindow(sid)` | telrapport.html | Uur-venster toepassen (was inline) |
| `detectLanguage()` | index.html | Eerste-hit-wint detectie |
| `setLanguage(lang)` | index.html | DOM bijwerken + active-class + document.title |

## Constanten (toegevoegd)

| Constante | Waarde | Plaats | Doel |
|---|---|---|---|
| `SS_VEHICLE_LOOKUP` | map | telrapport.html | Voertuigtype-herkenning (emoji + label) |
| `SS_TYPE_ORDER` | array | telrapport.html | Volgorde car/truck/moto/bike/ped |
| `SS_TYPE_LABEL` | map | telrapport.html | NL-labels in popup-tabel |
| `SS_TYPE_COLOR` | map | telrapport.html | Kleuren per type in tijdreeks |

## Edge cases & beslissingen

**Standstill: pin-positie bij dubieuze GPS.** Marker zit altijd op de gemelde lat/lon, ook bij accuracy >100m. De gestreepte ring toont onzekerheid; de gebruiker beslist hoe dat te interpreteren. Geen automatische verberg-logica — better visible-and-uncertain than hidden.

**Standstill + weekprofiel-popup**: stand-still sessies hebben geen visit-data, dus hun klik opent altijd de standstill-popup, niet het weekprofiel. Geen conflict want andere popup-codepath.

**Standstill + dag-filter**: een stand-still sessie heeft een geldige `meta.datum` (uit Start time), dus de dag-filter werkt automatisch. Geen edge case.

**Tijdreeks-event verdeling**: één tap = één event in de log = één increment in één bucket. Geen verdeling-over-buckets zoals bij visit-data (die hebben duur, taps hebben dat niet). Methodologisch correct: een tap is een momentopname.

**Tijdreeks-eenheid**: passages per bucket, niet passages per uur. Bewust — de bucket-grootte staat in het tijdreeks-titel niet expliciet, gebruikers leiden de schaal af uit de X-as labels. Wijzigen naar passages/uur zou cijfers groter maken maar afgeleide eenheden introduceren waar geen behoefte aan is.

**Dag-filter + sessie zonder datum**: graceful pass-through. Zou niet mogen voorkomen (alle telsoorten schrijven `datum` in sessie.csv) maar als het ooit gebeurt wordt zo'n sessie niet weggefilterd.

**Dag-filter + weekprofiel-popup**: bekende inconsistentie. Als gebruiker Werkdagen kiest in de timebar en daarna een weekprofiel-popup opent, zijn de Za/Zo-kolommen leeg omdat `buildWeeklyHeatmap` op `visible` filtert. Technisch consistent ("ik filter alles wat onzichtbaar is weg"), conceptueel raar ("ik open een 7×24 om alle dagen te zien"). Aanvaardbaar voor v2.5; mogelijke fix in v2.6 is `buildWeeklyHeatmap` de dag-filter laten negeren.

**i18n + flash-of-untranslated-content**: niet waargenomen omdat het script aan het einde van `<body>` synchroon draait. Mocht het op trage devices voorkomen, kan met inline-script in `<head>` opgelost worden, maar dat is voortijdig.

**i18n + andere pagina's**: bewust geen scope. Een NL-gebruiker klikt op een tegel en komt op een Engels-georiënteerde pagina. Acceptabel omdat de telpagina's vooral knoppen en korte labels hebben (waar Engelse woorden in NL gangbaar zijn).

**i18n + apostrofs in NL-strings**: opgelost door dubbele quotes te gebruiken (`"auto's"`) in plaats van escapen. Consistente regel: enkele quotes tenzij apostrof in de string.

## Vervolgstappen (niet in v2.5)

**Uit v2.4-overdracht doorgeschoven:**
- *Adaptieve segmentlengte*. Voor zeer lange highways (>1km tertiary) zou een groter `SEGMENT_TARGET_M` aangenamer kunnen zijn. Voorlopig één globale waarde — eenvoud wint.
- *Segment-koppeling met capaciteit*. Capaciteits-datamodel is fundamenteel anders dan pocket-flux.
- *Afwijkende-waarden filter in telplanning*. Nu er een 7×24 baseline per segment bestaat is "wat hoort hier normaal op dinsdag-10u?" een goed gedefinieerde vraag. Twee ontwerpkeuzes openstaand: wat is de baseline (alle sessies vs glijdend gemiddelde vs sessie-vs-sessie) en wat is afwijkend (procentueel vs z-score, met minimum-mediaan-drempel tegen ruis).
- *"Nu"-knop in telplanning-matrix*. Auto-cel-selectie op basis van actuele tijd. Eén-regel logica, niet gebouwd.
- *IndexedDB-estafette pocket → telrapport*. Eenvoudiger model dan BroadcastChannel: expliciete "klaarzetten voor telrapport"-knop in pocket, telrapport toont bij openen een "ZIP uit estafette laden?" prompt als er iets klaarstaat.
- *Weekprofiel-popup ververst niet automatisch bij sessie-visibility-toggle*. Klein UX-puntje.
- *Weekprofiel-knop verschijnt soms niet bij gemengde data*. Vereist soepelere logica.

**Nieuw uit v2.5-overwegingen:**
- *Snap-bug in pocket_count*. Tikken worden gesnapt op dichtstbijzijnde way binnen `TAP_SNAP_M` (50m); in dichte voetgangerszones zoals Spijkenisse Centrum kan een tik op een verkeerde naburige way landen terwijl het gelijktijdige GPS-punt op een andere way snapt. Voorbeeld: ZIP 20260520_145913_txb_pkt, nrs 28,29,44,45 op way 130419432 (Nieuwstraat-west) i.p.v. 136079346 (Centrumpassage). Mogelijke richting: tap-snap dwingen om dezelfde way te kiezen als het naburige (in tijd) GPS-punt, of strenger globaal-vs-existing arbitrage in build_bezocht.py.
- *traffic_counter_help.html structureel tweetalig maken*. De pagina is al een mengelmoes (Engels secties 1-10 + 38, Nederlands 11-37). Aanpak: twee complete `<div lang="...">` blokken naast elkaar, één wordt verborgen door dezelfde toggle-mechaniek als index.html. ~600 regels content per taal; aparte chat-scope.
- *Stand-still aggregatie over locaties*. Twee tellingen op dezelfde plek op verschillende dagen worden nu twee aparte pins die over elkaar liggen. Pas relevant als plek herhaaldelijk geteld wordt — bouw dan spatial-merge met 25m-buffer en weekprofiel-achtige popup.
- *Stats-paneel uitbreiding voor stand-still*. Eén pill "totaal passages/u" voor alle zichtbare standstill-sessies samen.
- *Dag-filter + weekprofiel-popup inconsistentie*. Heatmap-popup negeert dag-filter en toont alle dagen. Klein.

## Verifieerbaar via

- Sleep een traffic_counter.html CSV op telrapport → pin verschijnt op kaart, klik opent popup met tabel en tijdreeks.
- Sleep mix van .csv en .zip tegelijk → beide worden geladen, geen interferentie.
- Open dezelfde CSV twee keer → tweede keer geen wijziging (sessie-id stabiel = duplicate-detectie via `if (sessions[sid]) return;`).
- Timebar aanzetten → dag-pills verschijnen. Klik "Werkdagen" met weekend-sessie geladen → die sessie verdwijnt van de kaart, dot blijft op uurpositie in timebar-canvas.
- Schakel dag-pills → uur-slider behoudt positie, kaart reageert.
- Open index.html met NL-browser → pagina verschijnt in het Nederlands, NL-pill onderstreept.
- Klik EN-pill → pagina switcht naar Engels, blijft Engels bij refresh (localStorage).
- Open index.html in private/incognito → detect werkt, switch werkt, voorkeur wordt niet onthouden over sessies (verwacht gedrag).

## Bestanden gewijzigd t.o.v. v2.4

| Bestand | Type wijziging |
|---|---|
| telrapport.html | stand-still CSV-loader, popup, timeline; dag-filter pills |
| index.html | tweetalige toggle, i18n-mechaniek |
| README.md | versie-string |
| overdracht_v2_5.md | NIEUW |

Geen wijzigingen aan `build_bezocht.py`, `zip_format_reference.html`, of enige andere telpagina. v2.5 is een interpretatie- en presentatie-laag bovenop bestaande dataformaten — een v2.4-ZIP blijft een v2.5-ZIP, en de traffic_counter.html CSV-export uit v2.4 wordt zonder migratie geaccepteerd.
