# Overdracht v2.51 — pocket-parkeren op de wegpositie

Eén bestand, één functie, drie plekken. `telrapport.html`, +1.313 bytes.

## Wat er aan de hand was

Telrapport heeft twee laders die het niet met elkaar eens waren.

De auto/fiets/capaciteit-lader tekent op `lat_marker/lon_marker` — de positie op
de weg. Daar zie je die strakke rijtjes dus al. `loadPocketZip` tekende op
`lat/lon`, de rauwe GPS, óók bij een **gereconstrueerde pocket-parkeertelling**
waar `lat_marker` sinds v2.18 gewoon in `_telregels.csv` staat, ongebruikt. Een
parkeertelling in pocket kwam daardoor als GPS-wolk op de kaart in plaats van
als de rijtjes langs de straat.

De data was er al. Geen schemawijziging, geen her-export, geen KNIME.

## Wat er nu gebeurt

Nieuwe helper `tikPositie(r)` kiest de wegpositie waar die er is, anders de
GPS-positie. Hij wordt op drie plekken in `loadPocketZip` gebruikt: bij het
vullen van `telData` (dat voedt `drawClusters`), bij het tekenen van de stippen,
en daarmee ook bij de plaatshouder-geometrie voor segmenten zonder netwerkrij.

| ZIP | verandert er iets? |
|---|---|
| pocket rauw (geen markerkolom) | nee — terugval op `lat/lon` |
| pocket wandelprofielen (transect / winkelstraat / simpel) | nee — die kennen geen markerkolom, by design sinds v2.19 |
| pocket-parkeren gereconstrueerd | **ja** — stippen en clusters op de wegpositie |
| auto / fiets / capaciteit | nee — die deden dit al |

## `zijde` moest mee

Dit is de toevoeging die het plan nodig had. `drawClusters` groepeert op
`` `${wayId|segIdx}|${zijde}` ``. De auto-lader zet de rauwe rijen in `telData`,
dus daar komt `zijde` vanzelf mee. De pocket-lader bouwt een eigen object en liet
`zijde` weg.

Zonder `zijde` projecteren links en rechts op dezelfde positie langs de lijn en
klappen ze samen tot één clusterbol. Op GPS-coördinaten viel dat niet op, omdat
de wolk toch al door elkaar liep. Op wegcoördinaten wél: je zou twee nette rijen
van vier meter uit elkaar zien staan met één bol ertussen. `telData` draagt
`zijde` nu mee, dus links en rechts blijven gescheiden clusters.

## Correctietool

Niet geraakt, en dat hoefde ook niet. De tool is gepoort op
`appType === 'auto' || 'fiets'` (r.4559) en koppelt `_telregel` alleen in die
lader (r.3588). Pocket-stippen zijn niet versleepbaar, dus er is geen risico dat
je een GPS-stip versleept en daarmee stil een wegpositie overschrijft. Zou de
tool ooit naar pocket uitgebreid worden, dan is dát het moment voor die grendel.

## Naamgeving

In de code en het commentaar staat nu **GPS-positie** tegenover **wegpositie**,
niet "origineel" tegenover "gereconstrueerd". Bij een rauwe parkeer-ZIP is
`lat_marker` namelijk geen reconstructie maar de live 4 m-offset die de telefoon
zelf zette. GPS versus weg blijft in alle gevallen kloppen.

## Validatie

```
JS-syntax (node --check)                        15/15 OK
HTML-tagbalans, vergeleken met v2.50            geen afwijking
byte-identiteit                                 alleen telrapport.html gewijzigd
gedeelde blokken byte-identiek                  6 groepen OK
functionele test tikPositie + clustergroepering  9/9 OK
functionele test telrapport (Overpass)          16/16 OK
functionele test parkeertelling                 34/34 OK
functionele test pocket_count                   18/18 OK
```

Nieuw in de rig: `_archief/overpass_rig/functest_tikpositie.js`.

**Wat de tests niet dekken:** hoe het er in het echt uitziet. Laad een
gereconstrueerde pocket-parkeer-ZIP en kijk of de rijtjes kloppen en of links en
rechts als aparte clusters verschijnen.

## Als je later alsnog een knop wilt

De basis ligt er nu: één functie bepaalt de positie. Een schakelaar zou
`tikPositie` een modus meegeven, per stip beide paren onthouden (`m._pos`),
bij omschakelen `setLatLng()` doen in plaats van opnieuw bouwen, en
`drawClusters` opnieuw draaien. Twee dingen om dan op te lossen: het
wayData-clusterpad projecteert op segmenten en beweegt niet vanzelf mee, en de
correctietool moet in GPS-stand op slot. Niet nu nodig.

## Backlog

Ongewijzigd t.o.v. v2.50, behalve dat de pocket-inconsistentie eraf is:

**Klein / afgebakend**
- `zoekTerreinen` ontdubbelen op afstand tot het vorige zoekcentrum.
- Veiligheidsblok-kop in de handleiding: `<h1>` → `<h4>`.
- Engelse variant van `over.html`.

**Meetkunde (vraagt veldtest)**
- Fetch-radius en verversafstand losser zetten (nu 69% overlap per fetch).
- Gebied vooraf ophalen vanuit `telplanning.html`.

**Uitrollen als het bevalt**
- Audio-feedback en dekkingskaart naar de andere tel-modi.

**Groter / vraagt ontwerp**
- Parkeren uit pocket halen naar een eigen modus/tool.
- Schakelaar GPS-positie ↔ wegpositie in telrapport (zie hierboven).
- Plakkerigheid-kernel als winkelstraat-gegate punt-laag naar telrapport.
- %bezet per dag×uur-cel.
- QGIS-loader: optionele join op `_straten.csv` / `_bezocht.csv`.
