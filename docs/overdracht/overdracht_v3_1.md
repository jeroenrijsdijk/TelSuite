# Overdracht v3.1 — kaart bewaren als GeoPackage voor QGIS

Jay: "De QGIS-route is aantrekkelijk, maar na het importeren volgt er nog
allerlei werk. Kan telrapport een kant-en-klare GeoPackage maken, inclusief
opmaak, die in één keer goed op het scherm staat?" Ja, en dit is stap 1.

---

## 1. Wat er nieuw is

Onder *Kaart* in telrapport staat **bewaar kaart als GeoPackage (QGIS)**. Dat
geeft één bestand, `telrapport_<jjjjmmdd>_<uumm>.gpkg`. Sleep het in QGIS,
kies de lagen, en elke laag staat er opgemaakt:

| laag | wat | opmaak in QGIS |
|---|---|---|
| `waarnemingen` | elke stip, op de plek waar hij op de kaart staat | per type, kleuren van telrapport, legenda per categorie |
| `clusters` | de clusterbollen (zwaartepunt), telling per type | **taartdiagram**, even groot als hier, totaal als wit label |
| `wegvakken` | de wegvakken met hun klasse | de kleur van de kaart, legenda in woorden (*Druk (30–60 p/m·u)*, *30–60 % bezet*, …); bezocht-zonder-tellingen gestreept, overig wegennet dun grijs |
| `route` | het GPS-spoor per telling | gestreept, in de kleur van de telling, legenda met datum en teller |
| `sessies` | alle geladen tellingen (tabel) | — |
| `export_info` | instellingen van de export (tabel) | — |

## 2. Ontwerpkeuzes

**Wat je ziet, gaat mee.** Ik had voorgesteld: alles wat geladen is, met
filterkolommen. Bij het bouwen bleek dat niet consistent te krijgen. De
clusterbollen en de wegvak-kleuren rekent telrapport alleen uit voor wat
zichtbaar is, en de bollen hangen ook af van de clusterafstand. Voor
uitgezette tellingen zou er dus een tweede rekenpad nodig zijn. En in QGIS kun
je bollen niet herberekenen. Daarom: de export volgt de kaart. Wie alles wil,
zet alles aan. De tabel `sessies` noemt wél elke geladen telling, met
`op_kaart` = 0 voor de verborgen.

**Geen tweede rekenpad.** De lagen worden gelezen uit wat telrapport al
getekend heeft: `dotLayers`, `clusterLayers`, `wayLayers` en `gpsLayers`, met
`map.hasLayer()` als toets. Wat er op de kaart staat en wat er in het bestand
staat, kan dus niet uit elkaar lopen. De test controleert dat tot op de
coördinaat.

Daarvoor waren drie kleine, additieve tags nodig:

- `m._cluster = { counts, total }` op elke clusterbol (twee plekken in
  `drawClusters`);
- `m._rij = r` op pocket- en transectstippen, voor tijdstip, straat, zijde en
  richting.

**Waarom `_rij` en niet `_telregel`:** de correctiemodus maakt elke stip met
een `_telregel` versleepbaar. Met die naam zouden pocket-stippen ongemerkt
bewerkbaar worden. De test bewaakt dat ze dat niet zijn.

**Opmaak in de GeoPackage zelf.** Een GeoPackage mag een tabel
`layer_styles` hebben. Staat daar per laag een stijl met `useAsDefault` = 1,
dan past QGIS die bij het inladen toe. De stijlen zijn minimale QML: alleen
symbolen, labels en het diagram, een paar honderd tekens per laag. QGIS vult
de rest zelf in. Kleuren en categorieën komen uit `APP_CONFIG` en
`INTENSITEIT`, dezelfde bron als de kaart. De legenda toont alleen wat er in
het bestand staat.

**QGIS 3 én 4.** De QML heeft de vorm van QGIS 3.34. QGIS 4 leest die. Eén
valkuil vermeden: vet zetten gaat via de stijlnaam (`namedStyle="Bold"`), niet
via `fontWeight`. Dat getal betekent in Qt5 (QGIS 3, 75 = vet) iets anders dan
in Qt6 (QGIS 4, 700 = vet).

**Taartgrootte als hier.** Telrapport: diameter = 10 px + 5,6 px · √totaal.
QGIS schaalt "op oppervlak" (de wortel uit de waarde) lineair tussen 0 en het
maximum. Met 2,65 mm bij 0 en 2,65 + 1,48 · √max mm bij het maximum komt
precies dezelfde formule eruit.

**Labels.** Wit, vet, 8 pt, met een rand van 0,15 mm. Een dikkere rand (0,6 mm)
maakte het cijfer bij deze maat zwart; zonder rand verdwijnt het op lichte
bollen (grijs *leeg*, geel *fout*).

**Twee zichtbare verschillen met telrapport** (naast elkaar gerenderd op
hetzelfde kaartbeeld):

1. Telrapport tekent bollen kleiner dan 26 px als vlakke bol in de meest
   voorkomende kleur (v2.61: piepkleine taartpunten zijn niet af te lezen).
   QGIS tekent altijd een taart. In QGIS zoom je in en print je op A3, en dan is
   ook een kleine taart leesbaar. Bij een gelijkspel (1 leeg, 1 bezet) is de
   taart bovendien eerlijker dan een willekeurige "dominante" kleur. Bewust zo
   gelaten. Kan ook anders, met een regelgebaseerd symbool plus een
   diagram-voorwaarde, als Jay dat wil.
2. Overlappende bollen: telrapport legt de bovenste bol over het cijfer van de
   onderste, QGIS tekent beide cijfers (je ziet dan "11"). Dat speelt alleen als
   twee tellingen op precies dezelfde plek liggen.

**SQLite in de browser.** sql.js 1.14.2 van cdnjs. Dat domein stond al in de
privacyverklaring; de bibliotheek is aan de lijst daar toegevoegd. Hij wordt
pas geladen bij de eerste export, dus telrapport start niet trager. Mislukt
het laden (offline), dan meldt de knop het, en probeert de volgende klik het
opnieuw.

**Coördinaten in WGS84** (EPSG:4326), net als de ZIP's. QGIS projecteert zelf
naar RD New als het project dat is.

**Geweigerd in de correctiemodus.** Daar staan de stippen tijdelijk vervangen
door sleepmarkers. De knop zegt: sluit eerst de correctiemodus af.

## 3. Nog niet in deze stap

- **Capaciteitsterreinen en Static.** Staan ze op de kaart, dan meldt de
  export dat ze niet meegaan, en `export_info` noemt ze.
- **Het ingebouwde QGIS-project** (stap 2): ondergrond, laagvolgorde, RD New,
  een printopmaak met titel, legenda, schaalstok en noordpijl. Bij het slepen
  van de GeoPackage in QGIS kies je nu zelf de lagen, en de volgorde volgt die
  keuze. Eerst moet getest worden hoe QGIS de lagen terugvindt als het project
  in hetzelfde bestand zit en je dat bestand verplaatst.

## 4. Tests

Nieuw: `gpkgtest.py`, **54 tests**, met `gpkg_qgis.py` als helper voor de
QGIS-kant.

- **A.** Maakt echte tellingen met de veld-apps: parkeertelling,
  pocket-parkeren en pocket-winkelstraat, met nagebootste GPS langs een straat
  en een nep-wegennet.
- **B.** Laadt ze in telrapport en exporteert.
- **C.** Controleert het bestand met SQLite:
  - `application_id` en `user_version`, integriteit, de verplichte
    referentiesystemen, `gpkg_contents` en `gpkg_geometry_columns`;
  - elke geometrie (GP-kop, EPSG:4326, soort);
  - waarnemingen = de stippen op de kaart tot op 1e-7 graad;
  - clusters = de bollen met hun totaal, en per bol tellen de typekolommen op
    tot het totaal;
  - wegvakken en routes = de lijnen op de kaart;
  - de omhullende;
  - per kaartlaag één standaardstijl die elke categorie in de data dekt;
  - de taartkleuren = die van telrapport.
- **D.** Een telling uitzetten: die verdwijnt uit alle kaartlagen en uit de
  legenda, en staat in `sessies` met `op_kaart` = 0.
- **E.** De correctiemodus: de export weigert, en pocket-stippen zijn niet
  versleepbaar.
- **F.** Als PyQGIS er is, opent QGIS het bestand:
  - elke laag is geldig en heeft het juiste aantal objecten;
  - de categorie-opmaak wordt toegepast, met de bedoelde waarden, labels en
    kleuren;
  - clusters hebben het taartdiagram met een punt per typekolom, geen stip
    eronder, en het totaal als label;
  - de kaart wordt naar een PNG gerenderd.

  Zonder PyQGIS wordt dit deel overgeslagen, en dat wordt gemeld.

Gedraaid tegen **QGIS 3.34.4** (Ubuntu, zonder scherm). QGIS 4 was hier niet te
installeren. Die controle doet Jay (stand van zaken §4).

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telrapport.html` | knop onder *Kaart*; blok GeoPackage-export (sql.js-lader, `GPKG`-schrijver, `GPKG_QML`, `gpkgLagen`, `exportGeoPackage`); tags `_cluster` en `_rij` |
| `traffic_counter_help.html` | sectie *Kaart bewaren als GeoPackage (QGIS)* |
| `zip_format_reference.html` | sectie *GeoPackage export from telrapport* (lagen en kolommen) |
| `privacy.html` | sql.js bij de bibliotheken van cdnjs |
| `index.html` | versie v3.1 |
| `.gitignore` | `*.gpkg`, `*.qgz`, `*.qgs` (die kunnen tellingen bevatten) |
| `_archief/overpass_rig/gpkgtest.py`, `gpkg_qgis.py` | nieuw |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/ONTWIKKELEN.md`, `OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 6. Validatie

```
valideer.py        ALLES OK — 5 verwachte bestanden gewijzigd; 12 groepen gedeelde blokken OK
gpkgtest.py        54/54 (QGIS-deel tegen QGIS 3.34.4)
opruimtest.py      52/52
hersteltest.py     133/133
laadtest.py        46/46
statictest.py      24/24
functests          alle 13 groen
test_zipref.py     referentie sluit aan op de code
check_encoding.py  alles geldige UTF-8
```
