# Overdracht v2.63 — ondergrondkiezer en grove sporen

Eén bestand: `gpx_snap.html`, +5,7 kB. Twee vragen beantwoord, en de tweede
bleek de interessantste.

---

## 1. Ondergrondkiezer

Drie lagen rechtsboven: **Carto donker** (start), **OpenStreetMap** en
**Carto licht**. Donker blijft de startlaag omdat de gesnapte lijn daar het
beste tegen afsteekt, maar bij twijfel over een match wil je de gewone
OSM-kaart: die toont straatnamen, huisnummers en padsoorten, en dat is precies
wat je nodig hebt om te beoordelen of de matcher de goede weg koos.

---

## 2. Wat er met jouw grove GPX aan de hand is

`20240729.gpx` is geen rit maar een **dagloggerspoor**: 2.377 punten, 6,01 km,
en **23 uur 59 minuten**. Dat zie je terug in de spreiding:

| | waarde |
|---|---|
| mediaan afstand tussen punten | **0,0 m** |
| p75 | 2,1 m |
| p95 | 10,1 m |
| max | 101,1 m |
| mediaan tijd tussen punten | 31 s (max 351 s) |
| punten met `<hdop>` | 5 van de 2.377 |

Meer dan de helft van de punten ligt op dezelfde plek: je stond stil. En waar je
wél bewoog, zit er 31 seconden tussen twee fixes.

**Twee verschillende problemen, dus twee verschillende oplossingen.**

### Stilstand

Honderden fixes in een tuin of woonkamer snappen allemaal naar de
dichtstbijzijnde straat en leveren een klont op waar niets gebeurde. Dat is geen
matchprobleem maar ruis.

**Verdunnen** houdt er één van over. Elk weggelaten punt krijgt in de uitvoer
het resultaat van zijn vertegenwoordiger — dat mag, want het ligt er per
definitie binnen de drempel vandaan. De uitvoer-GPX houdt dus gewoon alle 2.377
punten; alleen de matcher ziet er minder.

### Te grote sprongen — en waarom dat stiller misgaat dan je denkt

Dit is de kern, en het zat verstopt in `hopClass`:

```js
function hopClass(adj, a, b) {
  if (a === b) return 0;              // zelfde way
  if (adj[a] && adj[a][b]) return 1;  // buur
  if (adj[a]) { … return 2; }         // buur van buur
  return Infinity;                    // bestaat niet
}
```

En in de transitielus: `if (!isFinite(hc)) continue;`. Een overgang van meer dan
twee hops is **onmogelijk**. Bij 31 seconden tussen fixes leg je zo honderd meter
af, en in een stratennet met ways van 30 à 80 meter zijn dat drie of vier hops.

Dan blijft de Viterbi-kolom leeg, en de matcher herstart met alleen
emissiekosten (`back = null`, de *stuksgewijze backtrack*). Het klapt dus niet —
maar op dat punt is het gedegradeerd tot "dichtstbijzijnde way", precies wat
map-matching zou moeten voorkomen. Zonder deze release zou je dat niet zien: de
uitvoer ziet er hetzelfde uit.

**Verdichten** zet tussenpunten op de rechte lijn, zodat elke sprong onder de
drempel blijft en de ketting heel blijft.

---

## 3. Waarom die tussenpunten geen verzonnen data zijn

Ze krijgen bewust `acc = 30` (`STEIGER_ACC`), ruim onder `SR = 40` maar groot
genoeg om de emissiekost `0,5·(d/σ)²` **vlak** te maken. Met een grote sigma
kost het een tussenpunt nauwelijks iets welke kandidaat het kiest — dus het
trekt de route niet naar zich toe. Het houdt alleen de ketting heel en laat de
topologie (`HOP1`/`HOP2`) het werk doen. Precies de rol die je wilt: steiger,
geen waarneming.

Loopt de echte route om een hoek, dan valt het tussenpunt in een huizenblok en
vindt het geen kandidaat binnen `SR`. Dan breekt de ketting daar alsnog — net
zoals zonder tussenpunt. **Slechter wordt het dus nooit.**

En ze komen niet in de uitvoer-GPX. Steigers zijn steigers.

---

## 4. Wat het oplevert op jouw bestand

Gemeten met `_archief/overpass_rig/meet_grofspoor.js`:

```
instelling                kern  steiger  fixes   med(m)   p95(m)   max(m)   >60m
alles uit (v2.62-gedrag)  2377        0   2377      0.0     10.1    101.1     12
alleen verdunnen 5 m       210        0    210     12.4     62.3    101.1     12
alleen verdichten 25 m    2377       89   2466      0.0     17.9     24.8      0
standaard (5 / 25)         210       89    299     15.9     23.7     24.8      0
strenger (10 / 15)         128      186    314     12.5     14.5     14.9      0
```

Met de standaardinstelling: **2.377 fixes worden er 299**, acht keer minder werk,
en de twaalf sprongen boven de 60 meter — de plekken waar de ketting brak — zijn
weg. De twee knoppen versterken elkaar: verdunnen alléén maakt het zelfs erger
(p95 van 10 naar 62 m), want je haalt punten weg zonder de gaten te dichten.

Defaults: verdunnen 5 m, verdichten 25 m. Allebei op 0 = uit, dus het
v2.62-gedrag blijft bereikbaar.

---

## 5. Over OSRM

Je had gelijk. Niet zozeer omdat het ingewikkeld is — OSRM heeft een `/match`-
endpoint dat hier precies voor bedoeld is — maar omdat het een externe dienst
is. De hele suite draait in je eigen browser zonder dat er data weggaat, en één
tool die daarvan afwijkt is een uitzondering die je moet blijven uitleggen. Je
zou er bovendien een tweede matcher naast de eigen krijgen, met eigen aannames
en eigen versies.

Twee schuiven die de invoer fatsoeneren lossen hetzelfde op binnen de code die
er al staat.

---

## 6. Validatie

```
nieuwe test functest_grofspoor.js   30/30 OK
  afstandM                          111,32 m per 0,001° breedte, nul bij gelijk punt
  verdunnen                         200 identieke punten -> 1 kern, drempel gerespecteerd,
                                    0 = uit, kernVan is dan de identiteit
  verdichten                        ceil-1 (niet floor), drempel precies/net erboven,
                                    steiger-acc 30, echte punten houden hun acc,
                                    absurde sprong afgekapt op 24, 0 = uit
  hdop                              aan/uit, terugval op de schuif
  terugvertaling                    elk origineel punt krijgt het resultaat van zijn kern
  ondergronden                      drie lagen, OSM zonder sleutel, donker als start
functest_gpxsnap.js                 39/39 OK (ongewijzigd)
JS-syntax, byte-identiteit, gedeelde blokken, encoding   alles OK
alle overige tests                  27+24+29+20+11+22+16+9+34+18+26+16 OK
```

Twee dingen die de test ving en ik anders niet had gezien: `floor` zette
stelselmatig één tussenpunt te veel, en een sprong van precies de drempel kwam
er door drijvendekomma-ruis uit als 100,00000000000001 en kreeg daardoor alsnog
een tussenpunt. Nu `ceil(d/maxGat − 1e-9) − 1`.

**Wat de test niet ziet:** of de match op jouw spoor ook echt beter wordt. De
meting laat zien dat de ketting niet meer breekt, niet dat hij de juiste weg
kiest. Gooi het bestand erin, zet de ondergrond op OpenStreetMap en kijk op een
paar kruispunten.

---

## 7. Voor de hand liggend vervolg

- **Stilstand als iets zinnigs.** Nu gooien we stilstandsclusters weg. Je zou ze
  ook kunnen gebruiken: een cluster van 200 fixes over 40 minuten op dezelfde
  plek is een *verblijf*, en dat is voor een dagloggerspoor waarschijnlijk
  interessanter dan de 6 km ertussen. Dat is een ander gereedschap, geen knop.
- **Ketting-breuken tonen.** De matcher weet waar hij herstart (`back = null`)
  maar vertelt het niet. Die plekken op de kaart zetten zou laten zien waar je de
  uitkomst niet moet vertrouwen. Klein werk, en het maakt de kwaliteit zichtbaar
  in plaats van dat je hem moet geloven.
