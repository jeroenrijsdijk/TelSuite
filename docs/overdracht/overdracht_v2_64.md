# Overdracht v2.64 — OSRM als tweede matcher in gpx_snap

Eén bestand: `gpx_snap.html`, +9,0 kB. OSRM staat er nu naast de eigen Viterbi.
Naast, niet in plaats van — ze geven niet hetzelfde terug.

---

## 1. Wat je kiest als je OSRM kiest

| | eigen Viterbi | OSRM |
|---|---|---|
| waar draait het | jouw browser | een server |
| netwerk ophalen | Overpass, in tegels gecached | niet nodig, die server heeft het al |
| grote sprongen | breekt op `hopClass = Infinity`, tenzij je verdicht | routeert er zelf doorheen |
| **way-id / segment-index** | **ja** | **nee** |
| straatnaam | ja | ja |
| tijdstempels gebruikt | nee | ja, in het overgangsmodel |

Die derde-van-onderen is de belangrijkste. OSRM's `tracepoints` geven een
gesnapte positie en een `name`, maar geen OSM-way-id. Wie die kolom nodig heeft
voor een QGIS-join of voor KNIME, moet de eigen Viterbi gebruiken.

Daarom staat de motor ook **in de uitvoer**: `<tel:motor>osrm</tel:motor>` of
`viterbi`. En bij een OSRM-match laat ik `<tel:osm_way_id>` gewoon weg in plaats
van hem leeg te schrijven — een lege kolom doet alsof er iets stond.

## 2. Wat OSRM juist wél oplost

Precies het probleem van v2.63: bij grote sprongen breekt onze Viterbi omdat
`hopClass` voorbij twee hops `Infinity` geeft. OSRM routeert tussen je punten en
heeft dat probleem niet. De **verdicht-schuif is daarom uitgeschakeld** zodra je
OSRM kiest (hij dimt zichtbaar) — tussenpunten zouden daar alleen ruis zijn.

**Verdunnen blijft wél aan, en is hier zelfs nodig:** de demo-server accepteert
100 coördinaten per aanvraag. Jouw dagloggerspoor van 2.377 punten wordt met de
standaardinstelling 210 kernpunten, en dat zijn drie aanvragen in plaats van 24.

## 3. Drie dingen die ik bewust zo heb gedaan

**De waarschuwing staat in de UI, niet in dit document.** Kies je OSRM, dan
verschijnt er in geel: *"Je coördinaten gaan naar deze server. De rest van de
suite werkt zonder dat er data weggaat; dit is de uitzondering."* Dat is de
eerlijke plek voor die mededeling. De lokale motor blijft de standaard.

**Het serveradres is een invoerveld.** De publieke demo-server is bedoeld om uit
te proberen, niet voor dagelijks gebruik, en draait alleen het auto-profiel.
Draai je ooit een eigen OSRM, dan vul je dat adres in en werken fiets en voet
ook. Zonder dat veld zou de tool vastzitten aan andermans server.

**`gaps=split`.** Een gat van zes minuten in je spoor — en die zitten erin, tot
351 seconden — wordt niet met een verzonnen route overbrugd maar als twee losse
stukken behandeld. Anders krijg je een gladde lijn door de stad waar je in
werkelijkheid met de trein zat.

Verder: tijdstempels gaan mee als de GPX ze compleet en oplopend heeft (OSRM
gebruikt ze in het overgangsmodel), `radiuses` komen uit de `acc` per punt
begrensd op 50 m, blokken overlappen 10 punten zodat de randen context hebben,
en er zit 250 ms tussen aanvragen — het is andermans server.

## 4. Over mijn vorige antwoord

Ik schreef gisteren dat ik OSRM niet zou doen omdat het de "niets verlaat je
browser"-belofte breekt. Dat argument klopt nog steeds — maar het is jouw
afweging, niet de mijne, en jij noemde dit expliciet een zijspoor. Wat ik had
moeten doen is het als keuze aanbieden mét die waarschuwing, in plaats van de
keuze voor je te maken. Dat is nu wat er staat.

## 5. Validatie

```
nieuwe test functest_osrm.js   41/41 OK
  blokindeling                 1 blok tot 100, daarna opgeknipt met overlap;
                               elk punt door precies één blok geleverd
  tijdstempels                 oplopend -> unix; ontbrekend of dalend -> weglaten
  de aanvraag                  lon,lat-volgorde, gaps=split, overview=false,
                               radiuses begrensd, adres uit het veld
  terugvertaling               positie en straatnaam over, geen verzonnen wayId
  randgevallen                 NoMatch, HTTP-fout, null-tracepoint blijft null
  uitvoer                      motor vastgelegd, geen lege way-id-kolom bij OSRM,
                               viterbi levert wél way-id en segment
  UI                           waarschuwing aanwezig, lokaal is standaard,
                               serveradres instelbaar, opties verborgen
functest_gpxsnap.js            39/39 OK   (ongewijzigd)
functest_grofspoor.js          30/30 OK   (ongewijzigd)
JS-syntax, byte-identiteit, gedeelde blokken, encoding    alles OK
```

De server is in de test nagebootst, dus er gaat geen verkeer de deur uit. Wat de
test daarmee **niet** dekt: of de echte demo-server hetzelfde antwoordt, of hij
je aantal aanvragen accepteert, en of het auto-profiel op een wandelspoor
zinnige uitkomsten geeft. Dat laatste vermoed ik van niet — een wandeling over
een fietspad of door een park heeft in het `driving`-profiel vaak geen weg om op
te vallen. Voor voetsporen blijft de eigen Viterbi waarschijnlijk beter, juist
omdat die `HIGHWAY_RE` gebruikt met voetpaden erin.

## 6. Voor de hand liggend vervolg

- **Beide motoren naast elkaar tonen.** Nu kies je er één. Ze allebei draaien en
  de twee sporen over elkaar leggen zou laten zien waar ze het oneens zijn, en
  dat is precies waar je moet kijken.
- **Way-id's alsnog uit OSRM.** Met `annotations=nodes` geeft OSRM de
  OSM-node-id's per stukje route. Daar zijn way-id's uit af te leiden, maar dat
  vraagt een node→way-tabel, en die haal je weer bij Overpass. Dan ben je de
  eenvoud kwijt die OSRM juist opleverde.
