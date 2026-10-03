# TrafficCounterSuite v2.7 — Overdracht

Een release met drie onafhankelijke verbeteringen: een fundamentele revisie van het tap-snap-model in pocket_count (taps erven het GPS-anker in plaats van zelfstandig te snappen), een zekerheids-heuristiek met live visuele feedback, en twee infrastructurele bugfixes die ervoor zorgen dat het netwerk-overzicht in telrapport nu compleet is voor alle app-types.

## Hoogtepunten

- **Taps erven het GPS-anker** (`snapProjectOnto`). Een tap roept niet langer `snapNearestWay()` aan maar projecteert zich loodrecht op de anker-way die het GPS-algoritme heeft gekozen. Één bron van waarheid: GPS stuurt, taps volgen. Voorkomt inconsistentie tussen GPS-fixes en taps bij snelle beweging of kort na een anker-wissel.
- **Jitter-debounce op anker-wissel** (`SWITCH_CONFIRM = 2`). Het anker klapt pas om naar een buur als diezelfde buur twee GPS-fixes op rij substantieel dichterbij is. Één GPS-uitschieter veroorzaakt geen anker-wissel meer. Nieuwe snap-paden: `d1_switch`, `d1_pending`, `d1_switch_noanchor`.
- **Zekerheids-heuristiek + live stip**. Per GPS-fix wordt een zekerheid in [0,1] berekend uit drie signalen: marge tot de runner-up way, afstand tot de gekozen way, en GPS-accuracy. Laagste wint (zwakste schakel). EMA-gesmoothed. UI: gekleurde stip (groen/oranje/rood) met huidige OSM-straatnaam onder de teller. Taps erven de live zekerheid als `conf` + `conf_level` in `_telregels.csv`.
- **Cumulatieve netwerk-accumulatie in parkeertelling + fietsparkeren**. `osmNetworkElements` werd bij elke Overpass-fetch overschreven; nu wordt cumulatief bijgehouden (zoals pocket al deed). Gevolg: `_netwerk.csv` bevat nu alle doorkruiste wegen van de hele sessie, niet alleen de laatste 250m-cirkel. Telrapport toont daardoor kleur op alle getelde wegen, inclusief service-ways en grote doorgaande straten die vroeg in de sessie zijn bezocht.
- **Volledig netwerk als achtergrondlaag in telrapport bij pocket-sessies**. Alle ways uit `_netwerk.csv` worden nu als grijze achtergrondlijnen getekend, precies zoals bij auto/fiets. Getelde ways kleuren via `recolorAll()`. Trappen, corridors en niet-getelde ways zijn nu zichtbaar.
- **Fetch-events in snap_trace**. Bij elke Overpass-fetch wordt een `fetch`-event geschreven in `_snap_trace.csv` met het fetchpositie-coördinaat en `n_el:N|n_segs:M` in de `snap_path`-kolom. Maakt het diagnostisch traceerbaar wanneer `snapSegs` werd vervangen en vanwaar.
- **Zekerheidsring op markers in telrapport**. `confBorder()` vertaalt `conf_level` uit telregels naar een randkleur: groen = witte rand (standaard), amber = oranje rand, rood = rode rand. Zichtbaar op pocket-, transect- en capaciteit-markers. Tooltip vermeldt ook de snap-zekerheid.

## Per bestand

### pocket_count.html

**Tap-snap model herzien**. Taps roepen niet langer `snapNearestWay()` aan. In plaats daarvan:
1. Als er een anker is → `snapProjectOnto(lastLat, lastLon, snapAnchorWayId)`: projecteer het GPS-punt loodrecht op de anker-way (read-only, geen anker-mutatie).
2. Als de anker-way buiten het huidige fetch-venster valt (geen geometrie beschikbaar) → erf metadata van `snapElements[snapAnchorWayId]`, marker blijft op ruwe GPS-punt.
3. Cold start (nog geen anker) → `snapNearestAny()`: dichtstbijzijnde way overall, read-only.

Twee nieuwe read-only helpers die het anker nooit muteren: `snapProjectOnto(lat, lon, wayId)` en `snapNearestAny(lat, lon)`.

**Jitter-debounce**. Nieuw global `snapChallenger = {wayId, count}`. Bij depth-1-pad: als de gekozen way verschilt van het anker én de drempel haalt, wordt niet meteen omgeklapt maar `snapChallenger.count++`. Pas bij `count >= SWITCH_CONFIRM` vindt de omklap (`d1_switch`) plaats. Zolang nog niet bevestigd: `d1_pending`, anker blijft staan. Challenger wordt gereset op elke niet-incrementele anker-wijziging (bootstrap, reset, depth-2, hold).

**Zekerheids-heuristiek**. Drie functies: `_ramp(v, lo, hi, up)`, `snapComputeConfidence(bestPerWay, chosenWayId, chosenD, acc, path, pending)`, `renderSnapConf()`. Constanten: `CONF_MARGIN_LO/HI = 6/20m`, `CONF_DIST_LO/HI = 10/40m`, `CONF_ACC_LO/HI = 10/30m`, `CONF_GREEN = 0.66`, `CONF_AMBER = 0.33`, `CONF_EMA = 0.5`. Globals: `snapConfScore`, `snapConfLevel`, `snapConfName`. UI: `#snap-conf` div met `#snap-dot` (CSS-klassen `green`/`amber`/`red`) en `#snap-name`.

**`conf` + `conf_level` in telregels.csv**. Twee extra kolommen achteraan — achterwaarts compatibel; telrapport leest op header-naam. Elke tap erft de live `snapConfScore`/`snapConfLevel` op het moment van tikken.

**Fetch-events in snap_trace**. Bij elke succesvolle Overpass-fetch wordt een `fetch`-record toegevoegd aan `snapTrace` met `event='fetch'`, `lat`/`lon` van de fetchpositie en `snap_path = 'n_el:N|n_segs:M'`.

**snap_trace.csv schema uitgebreid**:
| Kolom | Inhoud |
|---|---|
| conf | Gesmoothed zekerheid [0..1] (2 decimalen), leeg bij fetch/retro |
| conf_level | `green` / `amber` / `red` / `none` |

**Nieuwe snap-paden** (toegevoegd aan bestaande set):
| Pad | Betekenis |
|---|---|
| `d1_switch` | Bevestigde anker-wissel naar buur (na SWITCH_CONFIRM fixes) |
| `d1_pending` | Buur is dichterbij maar nog niet bevestigd — anker blijft |
| `d1_switch_noanchor` | Omklap zonder anker-terugvalpunt (randgeval) |
| `inherit` | Tap erft anker via snapProjectOnto |
| `inherit_nogeo` | Tap erft anker-metadata, geometrie niet beschikbaar |
| `tap_bootstrap` | Cold-start tap via snapNearestAny |
| `retro_nearest` | Retro-snap via snapNearestAny (pending-queue) |
| `fetch` | Overpass-fetch event |

**Pocket_debug.html**. Ongewijzigd — blijft een kopie van een eerdere pocket_count-versie met alleen een andere titel. Functioneel overbodig: alle trace-functionaliteit zit in pocket_count.

### telrapport.html

**Volledig netwerk als achtergrondlaag bij pocket-sessies**. Na het inladen van `_netwerk.csv` worden alle `netKeys` als grijze polyline (`color:'#3a3d42'`, weight:2, opacity:0.5) op de kaart gezet, vóór de telregels-verwerking. Getelde ways krijgen later via `recolorAll()` kleur. Niet-getelde ways (inclusief trappen, corridors, fietspaden) blijven grijs — diagnostisch nuttig.

**Zekerheidsring op markers** (`confBorder(row)`). Leest `conf_level` uit een telregel-row. Retourneert `{color, weight}` voor amber/rood, `null` voor groen/leeg. Toegepast op pocket-, transect- en capaciteit-markers. Tooltip vermeldt ook `· snap amber/red`. Ontbrekende kolom (oudere ZIPs) → `null` → geen effect.

### parkeertelling.html

**Cumulatieve netwerk-accumulatie**. Regel (voorheen): `osmNetworkElements = data.elements`. Nu: per fetch worden nieuwe elements toegevoegd aan de bestaande array; bekende `el.id`'s worden overgeslagen. LocalStorage-opslag volgt dezelfde logica.

### fietsparkeren.html

Identieke fix als parkeertelling.html — zelfde codepatroon, zelfde locatie in de fetch-callback.

### overige

- `pocket_debug.html`: ongewijzigd (onbedoeld achtergebleven als verouderde kopie — zie Vervolgstappen).
- `parkeertelling.html.bak`: archiefbestand van pre-v2.7-versie — niet deployen.
- Alle overige bestanden: ongewijzigd t.o.v. v2.6.

## Datastructuren toegevoegd

| Variabele | Plaats | Doel |
|---|---|---|
| `snapChallenger` | pocket_count.html | Uitdager-debounce `{wayId, count}` |
| `snapConfScore` | pocket_count.html | EMA-gesmoothed zekerheid [0,1] |
| `snapConfLevel` | pocket_count.html | `'green'` / `'amber'` / `'red'` / `'none'` |
| `snapConfName` | pocket_count.html | OSM-naam van huidige gekozen way |

## Helpers toegevoegd

| Functie | Plaats | Doel |
|---|---|---|
| `snapProjectOnto(lat, lon, wayId)` | pocket_count.html | Read-only loodrechte projectie op één way |
| `snapNearestAny(lat, lon)` | pocket_count.html | Read-only dichtstbijzijnde way overall (cold-start) |
| `_ramp(v, lo, hi, up)` | pocket_count.html | Lineaire ramp voor zekerheidsberekening |
| `snapComputeConfidence(...)` | pocket_count.html | Driesignaal-zekerheid + pending-cap |
| `renderSnapConf()` | pocket_count.html | Stip + naam bijwerken in UI |
| `confBorder(row)` | telrapport.html | conf_level → randkleur voor circleMarker |

## Constanten (toegevoegd)

| Constante | Waarde | Plaats | Doel |
|---|---|---|---|
| `SWITCH_CONFIRM` | 2 | pocket_count.html | Fixes vereist voor anker-wissel |
| `CONF_MARGIN_LO/HI` | 6 / 20 | pocket_count.html | Marge-ramp (m) |
| `CONF_DIST_LO/HI` | 10 / 40 | pocket_count.html | Afstands-ramp (m) |
| `CONF_ACC_LO/HI` | 10 / 30 | pocket_count.html | Accuracy-ramp (m) |
| `CONF_GREEN` | 0.66 | pocket_count.html | Drempel groen |
| `CONF_AMBER` | 0.33 | pocket_count.html | Drempel amber |
| `CONF_EMA` | 0.5 | pocket_count.html | EMA-smoothingfactor |

## Edge cases & beslissingen

**Taps erven anker, niet zelfstandig snappen**. Argument: GPS-fixes en taps deelden dezelfde `snapNearestWay()`-aanroep maar konden bij snelle beweging of een net-veranderd anker een andere way kiezen dan het GPS-algoritme had gekozen. Dat gaf inconsistentie in de trace: GPS op way A, tap op way B. Oplossing: de GPS-keten is de enige schrijver van het anker; taps lezen alleen. `snapProjectOnto` is read-only by design — de signatuur muteert geen globals.

**Jitter-debounce waarde 2**. Eén uitschieter-fix laat de challenger-count niet vollopen. Bij twee opeenvolgende fixes substantieel dichterbij is de kans op echte verplaatsing hoog genoeg. Waarde 1 = oud gedrag (direct omklappen), hogere waarden geven meer stabiliteit maar ook meer vertraging bij echte verplaatsing. Instelbaar via `SWITCH_CONFIRM`.

**Zekerheid als minimum van drie signalen**. Alternatief was gewogen gemiddelde. Gekozen voor minimum (zwakste schakel) omdat een hoge accuracy + kleine marge + grote afstand tóch een slechte snap oplevert; gemiddelde zou dat wegmasseren. Het minimum is conservatief maar eerlijk.

**EMA-factor 0.5**. Halfwaardetijd van 2 fixes (~4 seconden bij normale GPS-frequentie). Snel genoeg om veranderingen te tonen, traag genoeg om niet te flikkeren bij één afwijkende fix.

**Netwerk-achtergrond voor pocket**. Auto/fiets hadden dit al; pocket niet, omdat pocket losse passages telt en "hoeveel wegen onbezocht" minder relevant leek. In de praktijk bleek het ontbreken van de achtergrondlaag diagnostisch een probleem: niet-gesnapped ways (trappen, service-wegen) waren onzichtbaar in telrapport, wat het moeilijk maakte om te beoordelen of de snap correct had gewerkt. Symmetrie met auto/fiets is nu hersteld.

**Cumulatieve netwerk-accumulatie**. Pocket had dit al correct (`if (!snapElements[el.id])`); parkeertelling en fietsparkeren overschreven bij elke fetch. In de praktijk zag je dan in telrapport geen polylines voor wegen die vroeg in de sessie zijn bezocht — ze stonden niet in de laatste fetch en dus niet in `_netwerk.csv`. Fix is identiek aan de pocket-aanpak.

## Vervolgstappen (niet in v2.7)

**Doorgeschoven uit v2.6** — ongewijzigd van prioriteit:
- *Stand-still aggregatie over locaties*, stats-paneel uitbreiding, dag-filter inconsistentie, weekprofiel-knop verschijnt soms niet, weekprofiel-popup ververst niet.
- *Adaptieve segmentlengte* en *segment-koppeling met capaciteit*.
- *Afwijkende-waarden filter en "Nu"-knop in telplanning*.
- *IndexedDB-estafette pocket → telrapport*.

**Nieuw uit v2.7-bevindingen:**

- *snapSegs-verlies bij re-fetch*. De structurele oorzaak van "trap niet gesnapped": `snapSegs` wordt bij elke fetch vervangen door de nieuwe 250m-cirkel. Ways die net buiten de fetch-radius lagen op het moment van de volgende fetch vallen weg als kandidaat, ook al staan ze in `snapElements`. Fetch-events in de trace maken dit nu diagnostisch zichtbaar. Oplossing (nog niet gebouwd): bij re-fetch de vorige en nieuwe `snapSegs` samenvoegen met recency-afstandsfilter, zodat recente kandidaten niet abrupt wegvallen.
- *pocket_debug.html opruimen*. Het bestand is een verouderde kopie van een pre-v2.7 pocket_count — alle trace-functionaliteit zit al in pocket_count. Kandidaat voor verwijdering of update in v2.8.
- *Snap-fix migreren naar parkeertelling, fietsparkeren, capaciteitstelling, transect*. Adjacency-snap, hysterese en debounce bestaan nog alleen in pocket_count. Migratieplan in `snap_methodology.html` sectie 9. Netwerk-accumulatie is al gemigreerd (v2.7); adjacency-logica volgt.
- *Help-doc bijwerken*. `conf`/`conf_level` kolommen in `_telregels.csv` nog niet gedocumenteerd in `zip_format_reference.html`. Nieuwe snap-paden (`d1_switch`, `d1_pending`, `inherit`, etc.) nog niet in `snap_methodology.html`.
- *SWITCH_CONFIRM veldtest*. Waarde 2 is een aanname — na een paar veldtesten met de trace evalueren of 2 voldoende is of bijgesteld moet worden.

## Verifieerbaar via

**Zekerheids-stip (pocket_count.html)**:
- Open de app → stip is grijs vóór eerste GPS-fix, groen na stabiele snap, amber/rood bij GPS-twijfel of ambigu netwerk.
- Loop langs een drukke kruising → stip gaat kortstondig naar amber, keert terug naar groen als het anker stabiel is.
- Bekijk `_snap_trace.csv` na sessie → `conf` en `conf_level` per event aanwezig.

**Jitter-debounce (pocket_count.html)**:
- Sta stil bij een way-grens → anker blijft stabiel (geen `d1_switch` in trace bij stilstand).
- Loop door naar de andere way → na twee opeenvolgende fixes verschijnt `d1_switch`.
- Filter trace op `snap_path = "d1_pending"` → debounce-momenten zichtbaar.

**Fetch-trace (pocket_count.html)**:
- Wandel een route van >150m → `_snap_trace.csv` bevat `event=fetch` rijen met de fetchpositie en `n_el:N|n_segs:M`.

**Netwerk-achtergrond (telrapport.html)**:
- Laad een pocket-ZIP → alle wegen uit `_netwerk.csv` verschijnen als grijze lijnen, inclusief trappen en service-wegen.
- Getelde wegen kleuren; niet-getelde blijven grijs.

**Zekerheidsring (telrapport.html)**:
- Laad een pocket-ZIP gegenereerd met v2.7 → amber/rode markers hebben een gekleurde rand.
- Laad een oudere ZIP (zonder `conf_level`-kolom) → geen effect, witte rand standaard.

**Cumulatief netwerk (parkeertelling / fietsparkeren)**:
- Maak een sessie van >500m met meerdere re-fetches → `_netwerk.csv` bevat wegen van het begin én het eind van de route.
- Laad in telrapport → alle bezochte straten hebben kleur.

## Bestanden gewijzigd t.o.v. v2.6

| Bestand | Type wijziging |
|---|---|
| pocket_count.html | Tap-snap model (snapProjectOnto), jitter-debounce, zekerheids-heuristiek + UI-stip, fetch-events in trace, conf/conf_level in telregels/trace |
| telrapport.html | Netwerk-achtergrondlaag voor pocket-sessies, zekerheidsring op markers (confBorder) |
| parkeertelling.html | Cumulatieve osmNetworkElements accumulatie |
| fietsparkeren.html | Cumulatieve osmNetworkElements accumulatie |
| overdracht_v2_7.md | **NIEUW** |

Geen wijzigingen aan `pocket_debug.html`, `index.html`, `snap_methodology.html`, `zip_format_reference.html`, `traffic_counter_help.html`, `traffic_counter.html`, `traffic_counter_transect.html`, `capaciteitstelling.html`, `telplanning.html`, `build_bezocht.py`, `README.md`.
