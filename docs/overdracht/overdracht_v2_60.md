# Overdracht v2.60 — eerlijker coördinaten op de kaart

Eén bestand: `telrapport.html`. Vier ingrepen plus het opruimen van dode
dubbelcode. Geen enkele marker die nu klopt verschuift.

---

## 1. Het overzicht waar dit uit voortkwam

Welk coördinaat er per telsoort op de kaart belandt, na deze release:

| telsoort | laag | coördinaat |
|---|---|---|
| auto-parkeren | tik-stip | `lat_marker` / `lon_marker` (wegpositie) |
| | clusterbol | gemiddelde `lat_marker` per (way, segment, zijde) |
| fietsparkeren | idem | idem |
| capaciteit | terreinvlak | `geometrie_wkt` POLYGON uit `_netwerk.csv` |
| | terreinlabel | `poly.getCenter()` — het zwaartepunt |
| | zonder polygoon | **geen marker** |
| | losse vakken na klik | `lat_marker` / `lon_marker` |
| pocket (4 modi) | tik-stip | `tikPositie()`: `lat_marker` indien aanwezig, anders `lat`/`lon` |
| | cluster mét netwerk | gemiddelde `lat_marker` per (way, segment, zijde) |
| | cluster zónder netwerk | gemiddelde van de groep |
| transect | tik-stip | `lat`/`lon` — dit profiel krijgt ook na reconstructie geen markerkolom |
| standstill | één pin per sessie | `GPS latitude` / `GPS longitude` uit de metakop |
| alle | GPS-spoor | `_gps.csv` `lat`/`lon` |

## 2. De gap-clusterbol staat nu op het zwaartepunt

`drawClusters` heeft twee clusterpaden. Het segmentpad middelde netjes; het
gap-pad — voor pocket zonder netwerk en voor transect — deed
`L.marker([group[0].lat, group[0].lon])`. De bol hing dus aan de tik die
toevallig als eerste in het CSV stond en verschoof mee met de volgorde van de
regels. Nu middelen beide paden.

Meegenomen omdat het in dezelfde tien regels zat: het tik-**type** werd
teruggehaald uit de tooltiptekst (`tip.getContent().split(' ')[0]`). Dat is een
weergavestring; wie de tooltip mooier maakt, breekt stil de clusterkleuren. De
markers dragen nu `_tikType`, en de sleutel van `dotLayers` is als terugval nog
steeds het type.

## 3. Het capaciteitslabel staat op het zwaartepunt

Was het midden van de bounding box. Bij een L-vormig of langgerekt terrein valt
dat punt buiten het vlak. `poly.getCenter()` is het echte zwaartepunt en kost
niets.

## 4. Geen marker meer op een verzonnen positie

Had een groep geen polygoon, dan kwam hij op het GPS-zwaartepunt van de **hele
sessie** plus `i × 0,00005°` — ruim vijf meter per volgnummer, puur om overlap te
vermijden. En zonder GPS op `52.0, 4.5`: de Noordzee voor Den Haag. Zo'n marker
ziet eruit als een meting en is dat niet.

Die groepen worden nu niet getekend. De telling zelf gaat niet verloren — hij
staat in `_capaciteit.csv` en telt mee in de statistieken — maar de
plaatsbepaling ontbreekt, en dat wordt gezegd: de sessierij krijgt
"⚠ 2 terreinen zonder geometrie" met de namen in de tooltip, in dezelfde
opmaak als de bestaande dekkingsmelding. De namen gaan ook naar de console.

## 5. Dode transect-tak eruit

In `loadZip` stond een tweede, volledige transect-tak. Onbereikbaar:
`appType === 'transect'` keert daarvóór al terug via `loadTransectZip()`.
Zesentwintig regels die nooit draaiden en net iets anders waren dan het levende
pad — precies het soort dubbelcode waarin je later één van de twee repareert.

## 6. Eén punt uit mijn analyse was fout

Ik meldde dat de standstill-pin niet afgeschermd was tegen een ontbrekende
GPS-fix. **Dat klopte niet.** `loadStandStillCsv` controleert al op regel 1228
`if (!data.start || isNaN(data.lat) || isNaN(data.lon))` en stopt daar netjes,
vóórdat er ook maar een sessie of een paletkleur wordt aangemaakt.

Ik had een tweede controle ingebouwd en die weer verwijderd — dubbele guards zijn
erger dan geen, want de volgende lezer denkt dat er een reden voor is. De test
legt nu wél vast dat de bestaande controle er staat en vooraan blijft; het is de
enige telsoort waar één ontbrekend coördinaat het hele laden zou breken.

## 7. Eén ding dat juist goed staat en dat ik niet heb aangeraakt

Je zou de clusterbol op de weglijn kunnen leggen — de projectie wordt in het
segmentpad toch al berekend. Maar de groepen zijn gesplitst op `zijde`, dus links
en rechts zouden dan exact samenvallen. Het gemiddelde van de markerposities
houdt ze acht meter uit elkaar, en dat is precies wat je bij een parkeertelling
wilt zien. Dat is een goede keuze, geen toeval.

## 8. Validatie

```
nieuwe test functest_coordinaten.js   29/29 OK
  A gap-cluster                       zwaartepunt, _tikType i.p.v. tooltip
  B capaciteitslabel                  getCenter(), geen bbox-midden meer
  C fallback                          geen offset, geen Noordzee, wél gemeld
  D standstill                        bestaande guard staat er, geen tweede erbij
  E transect                          dode tak weg, levend pad één keer
  + de coördinaatbron per telsoort    vastgelegd zoals in de tabel hierboven
byte-identiteit                       alleen telrapport.html
alle overige tests                    20 + 11 + 22 + 16 + 9 + 34 + 18 + 26 + 16 OK
```

De test leest de broncode. Dat is hier het juiste niveau: dit zijn stuk voor stuk
plekken waar een latere "kleine opschoning" stil een marker kan verplaatsen, en
dat wil je vastgepind hebben.

**Wat de test niet ziet:** hoe het oogt. Laad een capaciteitstelling met een
langgerekt terrein en kijk of het label nu binnen het vlak valt, en een pocket-
of transecttelling zonder netwerk om de clusterbollen te vergelijken.
