# Overdracht v2.62 — gpx_snap.html: een GPX op het wegennet leggen

Nieuw bestand `gpx_snap.html` (49 kB), plus 115 bytes in `telreconstructie.html`
(twee commentaarregels hersteld, zie §5). Losse tool, **niet gelinkt** vanaf
`index.html` — het is geen telling, en jij noemde het zelf een zijstapje.

Eén GPX erin, netwerk erbij, GPX eruit waarvan de punten op de weg liggen.

---

## 1. Waarom dit weinig werk was

De rekenkern van `telreconstructie.html` stond al als twee zelfstandige modules,
met een kop die het letterlijk zegt: *"Zuiver rekenwerk, geen DOM, geen fetch.
Zo testbaar in Node én herbruikbaar in de browser-tool."* En `MATCHER` heeft
precies het contract dat je nodig hebt:

```
matchTrajectory(net, adj, fixes, segCounter)
  fixes = [{lat, lon, acc}]  chronologisch
  → per fix {wayId, segIdx, plat, plon} of null
```

`plat`/`plon` ís het gesnapte punt. Dat is de uitvoer-GPX.

## 2. Wat er letterlijk is overgenomen

Byte-identiek uit `telreconstructie.html`, ruim 750 regels:

| blok | regels |
|---|---|
| `RECON` (geodesie, projectie, richting) | 143 |
| `MATCHER` (Viterbi, adjacency, hopClass) | 164 |
| segmentatie (`splitWayIntoSegments`) | 41 |
| `HIGHWAY_RE`, `dataIsVers`, OVP-blok, `overpassFetch` | 114 |
| `OSMCACHE` + `liveFetchWays` + `cacheGefetchteRoute` | 161 |

**Alle vijf staan nu in `valideer.py`.** Dat was de voorwaarde om dit zo te
bouwen: twee kopieën van een Viterbi-matcher die uit elkaar lopen zie je pas
maanden later terug, in de data. De groepslijsten in `valideer.py` zijn meteen
definitief gemaakt, zodat ze niet meer per release met de hand hoeven.

Nieuw geschreven: GPX lezen en schrijven, route opdelen, de kaartweergave en het
lijmwerk — ongeveer 300 regels. Niet meegenomen: het hele profielsysteem, ZIP,
de CSV-schema's, de correctietool, zijde en offset, de aggregaties en alle
sessiesemantiek.

## 3. Drie keuzes in het ontwerp

**Lange ritten worden opgeknipt.** Eén bbox om zestig kilometer is grotendeels
leeg en loopt tegen `TEGEL_PLAFOND` (4000) aan. `routeStukken()` knipt het spoor
in opeenvolgende stukken van hoogstens 0,04° met 300 m marge, en haalt per stuk
op. De tegel-cache zorgt dat overlappende stukken geen tweede keer over de lijn
gaan. Getest: een rit van 66 km wordt 14 stukken, elk ruim onder het plafond.

**Niet-geplaatste punten blijven staan.** Een punt dat de matcher niet kwijt kan
houdt zijn originele coördinaat en krijgt `<tel:matched>false</tel:matched>`.
Weggooien zou de tijdreeks breken en over de dekking liegen: je zou een spoor
terugkrijgen dat gladder lijkt dan de werkelijkheid. Op de kaart zie je ze als
rode puntjes, en de gesnapte lijn wordt daar onderbroken in plaats van
doorgetrokken.

**De ruis is instelbaar.** GPX kent geen `acc`, en zonder dat valt `sigma` terug
op `SIG_MIN = 5` m — te streng voor een recreatief spoor. Er zit een schuif voor
(3–30 m, standaard 8) en een vinkje om `<hdop>` te gebruiken waar het toestel dat
schrijft (× 2,5 als ruwe omrekening). Dat is de knop om aan te draaien als de
matcher te vaak een parallelweg kiest.

## 4. De uitvoer

GPX 1.1 met twee tracks: eerst het gesnapte spoor, daarna het originele (uit te
zetten). Per punt blijven `<ele>` en `<time>` behouden, plus extensies in een
eigen namespace:

```xml
<extensions>
  <tel:osm_way_id>142108527</tel:osm_way_id>
  <tel:segment_index>2</tel:segment_index>
  <tel:street>Voorstraat</tel:street>
  <tel:highway>residential</tel:highway>
  <tel:matched>true</tel:matched>
</extensions>
```

Twee tracks in één bestand betekent dat je in elke GPX-viewer — of in QGIS — de
correctie direct naast het origineel ziet.

## 5. Een drift die dit blootlegde

Het commentaar boven `splitWayIntoSegments` in `telreconstructie.html` zegt
"byte-identiek aan pocket_count.html". Dat was het **niet**: pocket had twee
commentaarregels die de reconstructor miste. De code was gelijk, dus er is nooit
iets misgegaan — maar een belofte die niet klopt is precies wat een
md5-controle waardeloos maakt. De twee regels zijn hersteld, en nu bewaakt
`valideer.py` het over drie bestanden.

## 6. Validatie

```
nieuwe test functest_gpxsnap.js   39/39 OK
  leesGpx                         trkpt, rtept, tijd/ele/hdop, en drie nette weigeringen
                                  (losse waypoints, onzin-XML, één punt)
  routeStukken                    kort spoor één stuk, 66 km → 14, elk onder het plafond
  matchen                         recht stuk weg, spoor 6 m ernaast → alles op de wegas
  GPX schrijven                   namespace, twee tracks, extensies, parseerbaar,
                                  origineel uit te zetten, XML-escaping
  niet-geplaatst                  blijft staan, matched=false, eigen coördinaat, tijd intact
  rekenkern                       RECON/MATCHER/OVP/OSMCACHE/segmentatie identiek
JS-syntax, HTML-tagbalans          OK
byte-identiteit                    alleen gpx_snap.html (nieuw) + telreconstructie.html
gedeelde blokken                   10 groepen OK
alle overige tests                 27+24+29+20+11+22+16+9+34+18+26+16 OK
```

De test heeft `@xmldom/xmldom` nodig om de uitvoer echt te parseren:

```
npm install @xmldom/xmldom
node _archief/overpass_rig/functest_gpxsnap.js
```

**Wat de test niet dekt:** een echt spoor tegen echt OSM. Gooi er een rit in die
je kent en kijk of de matcher de goede kant van een parallelweg kiest. Als hij te
vaak naast zit, is de ruis-schuif het eerste wat je probeert.

## 7. Wat ik bewust heb laten liggen

- **Batch.** Je zei één per keer met kaart, dus dat is het geworden. De pijplijn
  is een enkele functie; een maplus-versie zonder kaart is later klein werk.
- **Decimeren.** Een spoor van 1 Hz over vier uur is 14.000 punten. Dat draait
  (de Viterbi is seconden), maar de kaart wordt traag. Boven 20.000 punten komt
  er een melding; een "minimale afstand tussen punten"-knop is de logische
  volgende stap als je dat tegenkomt.
- **Richting.** `RECON.reconstructDirection` zit in het bestand maar wordt niet
  gebruikt. Voor een spoor is de looprichting al de volgorde van de punten. Als
  je ooit per punt de wegrichting wilt weten, ligt het er klaar.
