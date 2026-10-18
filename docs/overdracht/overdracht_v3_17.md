# Overdracht v3.17 — backlog opgeruimd

Jay, uit de backlog: "wil je deze 5 oppakken":
1. metadata voor `zip_format_reference.html`;
2. oude terugvalcode in telrapport en telplanning opruimen;
3. een tegenstrijdig commentaar in capaciteitstelling;
4. `zoekTerreinen` vuurt bij elke kaartpan een Overpass-verzoek;
5. `probeBbox` voor verzamelingen.

## 1. Metadata voor de ZIP-referentie

De pagina had sinds v3.6 al een titel, een description en een canonical. Nu
komen daar bij:
- **Open Graph**, zoals op de handleiding. `og:locale` is `nl_NL`, met `en_US`
  als alternatief: titel en description zijn Nederlands, de pagina zelf is
  Engels.
- **Een TechArticle in JSON-LD**, met `inLanguage: en`.

`valideer.py` controleert dat `og:title` gelijk is aan de titel zonder
" | telonline.org".

## 2. Terugvalcode in telrapport en telplanning

In `overdracht_v2_53.md` §6 stonden vijf plekken. Per plek bekeken. Het
resultaat: **geen enkele is dood**. Er is niets weggehaald, alleen het
commentaar klopt nu.

| plek (v2.53) | wat het is | besluit |
|---|---|---|
| telrapport, pocket-lader | **haalt via Overpass de geometrie op** als een geteld segment niet in `_netwerk.csv` staat; volgens het commentaar voor pocket-ZIP's van vóór v2.1 | **blijft.** Zie hieronder: ook een huidige pocket-ZIP kan zonder `_netwerk.csv` zijn. |
| telrapport, `segment_index` ontbreekt → 0 | parse-standaard, `+(x \|\| 0) \|\| 0` | **blijft.** Kost niets en beschermt ook tegen NaN. Commentaar bijgewerkt. |
| telrapport, `confBorder` → null zonder kolom | een tik zonder `conf_level` krijgt geen rand | **blijft.** Is gewoon robuust. |
| telrapport, `pmuForKey`: tikken uit `wayData` als de bezoeken geen tikken hebben | vangt het geval op dat `_bezocht.csv` en `_telregels.csv` een tik aan verschillende segmenten toekennen | **blijft.** Weghalen zou zo'n segment zijn kleur laten verliezen. Het commentaar noemde het "backward compat"; dat klopte niet. |
| telplanning, `segKey`: zonder `segment_index` → 0 | `_bezocht.csv` van pocket vóór v2.3; de hertelling leest het netwerk van parkeer-ZIP's (zonder segmenten) op dezelfde manier | **blijft.** Commentaar bijgewerkt. |

**Wat de tests lieten zien.** Mijn eerste versie haalde de Overpass-terugval
weg en liet telrapport een pocket-ZIP zonder `_netwerk.csv` weigeren. Daarop
faalde `logicatest` B1: de echte pocket-ZIP uit die test, gemaakt na
Doortellen, heeft geen `_netwerk.csv`.

De oorzaak zit in pocket:
- pocket schrijft `_netwerk.csv` alleen als de snap-motor bij Stop een netwerk in
  het geheugen heeft;
- de noodkopie bewaart dat netwerk niet;
- na Doortellen is het netwerk dus leeg tot er weer een is opgehaald. Stop je
  daarvoor, dan ontbreekt het bestand, terwijl de tikken van vóór de
  onderbreking wél een way-id dragen.

Telrapport vangt dat op met de Overpass-terugval. Die is teruggezet, met
commentaar dat zegt waarvoor hij echt dient. De oorzaak in pocket staat op de
backlog: het netwerk in de noodkopie bewaren of na Doortellen meteen ophalen.

`haalWayGeometrie` heeft dus nog drie gebruikers:
- de pocket-terugval hierboven;
- het losse transect-formaat `_trn` (gaat mee met het besluit over `_trn`);
- capaciteitsterreinen zonder geometrie in `_netwerk.csv`.

## 3. Commentaar in capaciteitstelling

`exportZip()` zei dat `_terrein.csv` een eigen schema heeft (osm_id+osm_type,
geen zijde). Dat klopte niet. `buildTerreinCsvString()` schrijft bewust dezelfde
kolommen als `_capaciteit.csv` (osm_way_id, zijde `nvt`), en zo staat het ook in
de ZIP-referentie. Alleen het commentaar is aangepast; de code is niet veranderd.

## 4. Parkeerterreinen zoeken met geheugen

**Tot v3.17:**
- elke kaartpan (na 600 ms rust) gaf een nieuw Overpass-verzoek, ook bij een
  paar meter;
- elk antwoord wiste de terreinen van het vorige;
- een geteld terrein verloor zijn donkere rand bij de volgende pan;
- de zoekvraag liep langs een eigen lijst met servers, zonder `ovpKeur`.

**Nu:**
- **Geheugen.** De app onthoudt de plekken waar hij met succes zocht
  (`terreinZoekPlekken`, straal 400 m) en alle gevonden terreinen
  (`terreinGevonden`).
- **Geen verzoek als het niet hoeft.** Ligt het nieuwe zoekpunt binnen 150 m
  van een eerdere zoekplek of van het verzoek dat nog loopt, dan gaat er geen
  verzoek uit. Alles binnen 250 m is dan al bekend.
- **Elk terrein één keer getekend.** Terreinen blijven op de kaart staan. Een
  geteld terrein houdt zijn donkere rand, ook als het pas later getekend wordt.
- **Netwerk zonder dubbelen.** Tijdens een sessie komen de polygonen binnen
  400 m van het zoekpunt in het netwerk voor `_netwerk.csv`, zoals voorheen,
  maar zonder dubbelen. De export ontdubbelde al; het geheugen nu ook.
- **Antwoorden door `ovpKeur`** (gedeeld OVP-blok, ongewijzigd):
  - een afgebroken of verouderd antwoord: de volgende server;
  - een rate-limit: ophouden, en de tweede server niet ook belasten.
- **Mislukt zoeken wordt niet onthouden.** Een volgende pan op dezelfde plek
  probeert het opnieuw.
- **Inzoomen** gebeurt alleen na een nieuw antwoord en als je niet zelf aan het
  pannen bent, op de terreinen rond het zoekpunt.

De grens van 150 m staat in `TERREIN_HERGEBRUIK_M`, de straal in
`TERREIN_ZOEK_M`. De handleiding (Module 2) noemt het.

## 5. Bbox-filter voor verzamelingen

`probeBbox` zocht in een verzameling naar `_netwerk.csv` en `_gps.csv`. Die
staan in de tel-ZIP's erbinnen, niet in de verzameling zelf. Hij gaf dus `null`,
en het filter liet een verzameling altijd door.

**Nu:**
- **Bbox van alle tellingen samen.** Een verzameling krijgt de bbox van alle
  tellingen uit haar manifest (`bboxVerzameling`). De bbox van één tel-ZIP komt
  uit `bboxUitZip`; daar is de oude code naartoe verhuisd.
- **Als geheel.** Een verzameling is een bewaarde kaart, geen stapel losse
  tellingen. Ligt één van haar tellingen in beeld, dan laadt de hele
  verzameling. De bewaarde weergave wint daarna, zoals al sinds v2.55.
- **Bij twijfel meenemen.** Is van één telling de bbox niet te bepalen, of is
  het manifest kapot, dan gaat de verzameling mee, net als een los bestand
  waarvan de bbox onbekend is. Een lid dat in het manifest staat maar
  ontbreekt, telt niet mee. `loadVerzameling` slaat het ook over.

De tooltip van het vinkje en de handleiding (*ZIPs laden*) noemen het.

## 6. Tests

**`functest_bbox.js`** (nieuw, 11 tests, Node + jszip + papaparse). Het knipt
het bbox-filter uit telrapport en controleert:
- de bbox van een tel-ZIP: uit het netwerk, anders uit het GPS-spoor, anders
  geen bbox;
- de bbox van een verzameling: alle tellingen samen;
- de randgevallen: een telling zonder bbox, een kapot manifest, een ontbrekend
  lid, een lege verzameling;
- het filter zelf: een verzameling ver buiten beeld valt weg, een die deels in
  beeld ligt niet.

Tegen v3.16 faalt hij bij de verzameling.

**`onderhoudtest.py`** (nieuw, 17 tests, Chromium).
- *A, telrapport:*
  - een pocket-ZIP zonder netwerk (zoals na Doortellen) laadt, zonder melding;
    de geometrie van de getelde way komt met één Overpass-verzoek;
  - een pocket-ZIP mét netwerk laadt zonder één Overpass-verzoek.
- *B, capaciteitstelling:*
  - 100 m en 140 m verder geen verzoek, 400 m verder wel, en het eerste terrein
    blijft staan;
  - terug naar het begin: geen verzoek en niets dubbel;
  - in een sessie: het netwerk zonder dubbelen;
  - een geteld terrein houdt zijn rand;
  - een rate-limit bij server 1 belast server 2 niet;
  - na een mislukte poging wordt dezelfde plek opnieuw geprobeerd.

Deel A legt vast wat v3.16 al deed. De test moet voorkomen dat iemand de
terugval later alsnog weghaalt. Tegen v3.16 faalt deel B: het geheugen bestaat
daar niet.

## 7. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `zip_format_reference.html` | Open Graph en TechArticle |
| `telrapport.html` | `probeBbox` → `bboxUitZip` + `bboxVerzameling`; tooltip van het vinkje; commentaar bij de terugvallen (de code zelf ongewijzigd) |
| `telplanning.html` | commentaar bij `segKey` |
| `capaciteitstelling.html` | commentaar `_terrein.csv`; `zoekTerreinen` met geheugen (`onthoudTerrein`, `verwerkTerreinen`) |
| `traffic_counter_help.html` | Module 2 (zoeken met geheugen), *ZIPs laden* (het vinkje en verzamelingen) |
| `index.html` | versie v3.17 |
| `_archief/overpass_rig/functest_bbox.js`, `onderhoudtest.py` | nieuw |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 8. Validatie

```
valideer.py           ALLES OK — 6 verwachte bestanden gewijzigd; gedeelde blokken (ook OVP-blok) ongemoeid en OK
functest_bbox.js      11/11 (nieuw)
onderhoudtest.py      17/17 (nieuw)
logicatest.py         30/30 (B1 faalde op de eerste versie, zie §2)
laadtest.py           45/45
hersteltest.py        133/133
statictest.py         24/24
opruimtest.py         139/139
robuusttest.py        87/87
planlinktest.py       51/51
gpkgtest.py           80/80
functests             alle 18 groen
test_zipref.py        referentie sluit aan op de code
check_encoding.py     alles geldige UTF-8
```
