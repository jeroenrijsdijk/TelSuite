# Overdracht v3.33 — Archief: overzicht van alle tellingen

Jay, na v3.32: "Ik heb inmiddels honderden tellingen dus misschien moeten we gaan
eens denken vanuit een data-architectuur: Een moedermap, daarin alle tellingen
gerubriceerd naar soort. Toch iets van een database?"

## 0. Het gesprek vooraf

1. **Mijn eerste voorstel:** de map is de database, de ZIP is het record, en
   een catalogus is de index. De mappen ordenen op één ding (de soort); een
   catalogus die altijd opnieuw te maken is; later misschien *Kies uit je
   archief* in telrapport. Geen databaseserver en geen IndexedDB.
2. **Jay maakte het kleiner:** "De catalogus is puur bedoeld als 'wanneer en
   waar' zijn er tellingen gedaan. Ik wil kunnen checken op dubbele bestanden.
   Ik wil kunnen zen of er bestanden zijn zonder _recon versie."
3. **Ik stelde een GeoPackage voor**, met twee lagen.
4. **Jay:** "Ik zit toch te denken of het geintegreerd kan in de html van
   ordenen - een kaartje, een overzicht. Met als basis een csv of iets anders
   dat ook in tekst te bekijken is."
5. **Het plan:** `catalogus.csv` met 15 kolommen, een tabblad *Overzicht* met
   kaart, filters en tabel, de route bij een klik, en de pagina heet *Archief*.
   In twee stappen; het alleen bijwerken wat nieuw is, komt in stap 2. Jay:
   "Goed plan! Ga maar bouwen."
6. **Tijdens het bouwen:** "eingelijk is Archief nu een soort Verkenner over
   alle tellingen, in telrapport maak je de plaatjes/rapportage." Dat staat nu
   zo op de pagina, op de voorpagina en in de handleiding. De naam bleef
   *Archief*.

Aan de ZIP's en het schema van de pijplijn verandert niets. `catalogus.csv` is
een nieuw bestand naast de ZIP's. De kolommen zijn met Jay afgesproken en staan
in de ZIP-referentie.

## 1. De pagina

`telarchief.html` heet nu *Archief* (titel, kop, voorpagina). Na het lezen zijn
er twee tabbladen:
- **Overzicht** opent eerst;
- **Ordenen** is wat er sinds v3.31 stond, met een eigen melding
  (`#plan-melding`). De melding bovenaan gaat nu over het lezen en de catalogus.

## 2. De catalogus (`ORDENEN.catalogus`, los getest)

Eén regel per telling of verzameling. Andere ZIP's (geen telling) krijgen geen
regel; die staan bij Ordenen onder *blijft liggen*.

| kolom | waar het vandaan komt |
|---|---|
| `sessie_id`, `datum`, `start_tijd`, `eind_tijd`, `n_waarnemingen` | `_sessie.csv`; zonder dat bestand de datum uit de naam |
| `soort` | de mapnaam van Ordenen (`Autoparkeren` … `Verzamelingen`) |
| `weekdag` | `ma` … `zo`, uit de datum |
| `recon` | `ja`, `nee`, `zelf` of `n.v.t.` (Static, capaciteit, verzameling) |
| `dubbel_van` | bij precies dezelfde inhoud: het pad van het bestand dat blijft, gekozen zoals Ordenen kiest |
| `lat`, `lon` | per coördinaat de mediaan van `_gps.csv`; anders de telplek uit `_sessie.csv` (Static), dan de tikken; anders leeg |
| `pad`, `bytes`, `gewijzigd`, `sha256` | het bestand zelf |

- **Waarom de mediaan:** begint de opname thuis, dan ligt het punt toch in het
  telgebied, want daar liggen de meeste punten. Het gemiddelde zou naar huis
  trekken.
- **Zelfde telling, andere inhoud:** twee originelen, of twee reconstructies,
  met dezelfde sessie-id en een andere vingerafdruk. Dat staat niet in de CSV
  (geen kolom afgesproken); wel op de pagina.
- **`plan()`** onthoudt nu bij een dubbel welk bestand blijft (`dubbelVan`).

## 3. `catalogus.csv`

- **Waar:** in de moedermap.
- **Wanneer:** na elk lezen en na elke keer *Uitvoeren* wordt hij opnieuw
  gemaakt. Hij is afgeleid, dus overschrijven mag, anders dan bij de ZIP's en
  de logboeken.
- **Elders dan Chrome en Edge:** de knop *Download catalogus.csv*. Die knop
  staat er ook in Chrome.
- **De kop** is één letterlijke string in de code. `test_zipref.py` kijkt nu
  ook in `telarchief.html`, en de referentie heeft een sectie *Archive
  catalogue*.

## 4. Het overzicht

- **Tellers** bovenaan: hoeveel tellingen (en verzamelingen), van welke maand
  tot welke. Daarnaast wat aandacht vraagt:
  - dubbel;
  - zelfde telling, andere inhoud;
  - zonder reconstructie;
  - zonder plek.

  Een teller aanklikken filtert daarop, nog eens klikken laat weer alles zien.
- **Kaart:** Leaflet 1.9.4 met CARTO Positron, zoals telrapport.
  - Tellingen in hetzelfde vak van 40 px worden een bol. Dat is het gedeelde
    blok `clusterbol` uit telrapport, een taart per soort met het aantal in
    het midden, byte-identiek en bewaakt door `valideer.py`.
  - Een bol aanklikken zoomt in. Liggen ze op één plek, of kan het niet
    verder, dan komt er een lijstje om er een te kiezen.
  - Zonder Leaflet (offline) werken de tabel en de catalogus gewoon.
- **Filters:** soort (met kleur en aantal, *alle* en *geen*), periode van en tot
  en met, en *laat zien*: alles, zonder reconstructie, dubbel (de kopie en het
  origineel), zelfde telling, zonder plek. De kaart, de tabel en de tellers
  volgen.
- **Tabel:** de nieuwste bovenaan, met merkjes voor dubbel, zelfde telling en
  zonder plek. Een rij aanklikken zet de kaart erop, met de gegevens en de
  route.
- **Route:** pas bij een klik leest de pagina `_gps.csv` uit de ZIP zelf, dus
  de catalogus blijft klein en de ZIP blijft de bron.
  - De route loopt mee vanaf thuis als de opname daar begon. Het is je eigen
    scherm.
  - Werkt ook in *alleen bekijken*: de pagina houdt de gekozen bestanden vast.
- **Na Uitvoeren:** elk verplaatst item wijst naar zijn nieuwe plek (`verhuisd`):
  pad, naam, map en handle. Het overzicht, de catalogus en de route kloppen
  dan zonder opnieuw te lezen.
- **Kleuren per soort:** de vijf apps zoals in de ZIP-referentie; de vier
  pocket-modi elk een eigen kleur (parkeren magenta, simpel bruin, transect
  zeegroen, winkelstraat rood).

## 5. Elders bijgewerkt

- **`index.html`:** *Archief* / *Archive*: "al je tellingen op een kaart,
  gecontroleerd en geordend"; versie v3.33.
- **`over.html` en `about.html`:** Archief als verkenner; de plaatjes en de
  rapportage in telrapport.
- **Handleiding (`#ordenen`):** *Je archief: overzicht en ordenen*, met een tabel
  voor het overzicht en de oude voor Ordenen.
- **Privacyverklaring (NL en EN):**
  - `catalogus.csv` in de gekozen map;
  - de ZIP's gaan het netwerk niet op;
  - de kaart haalt tegels bij CARTO.
- **`zip_format_reference.html`:** sectie *Archive catalogue (catalogus.csv,
  Archief)*.
- **`docs/ONTWIKKELEN.md`:** de rij van `telarchief.html`.

## 6. Bewust nog niet (stap 2)

- **Alleen nieuwe of veranderde ZIP's lezen,** met `catalogus.csv` als geheugen.
  Daar zijn `bytes` en `gewijzigd` al voor.
  - Let op: na een verplaatsing met `move()` blijft de wijzigdatum gelijk;
    na de kopieerweg niet.
  - Eerst bij Jay meten hoe lang het lezen van zijn archief nu duurt.
- **Een maandstrook** boven de tabel.
- **Plaatsnaam of wijk:** dat vraagt het netwerk. In QGIS is het één
  ruimtelijke join op de CSV.

## 7. Tests

- **`functest_ordenen.js`** 50 (was 35):
  - de plek (mediaan; thuis telt niet; lege en kapotte waarden);
  - de weekdag;
  - recon ja, nee, zelf, n.v.t.;
  - `dubbel_van` en `heeftDubbel`;
  - zelfde telling;
  - de datum uit de naam van een verzameling;
  - de volgorde;
  - de CSV: de kop, een volledige regel, een puntkomma in een waarde, 15
    velden, de slotregel.
- **`archieftest.py`** (nieuw, 42), in Chromium op echte bestanden (OPFS), met
  een spoor dat thuis begint:
  - **A.** `catalogus.csv`: de kop en een regel per telling. Ook de waarden:
    recon, `dubbel_van`, de plek als mediaan, Static op zijn telplek, de
    verzameling, zonder plek, en `bytes` en `sha256` van het bestand. De CSV
    is gelijk aan wat de pagina toont.
  - **B.** De tellers, en de tabel met de nieuwste bovenaan.
  - **C.** De kaart:
    - alle 10 tellingen met een plek staan erop;
    - origineel, kopie en reconstructie samen in één bol van 3;
    - helemaal ingezoomd geeft de bol een lijstje, en daaruit kiezen werkt.
  - **D.** De filters: de tellers, *dubbel*, *zelfde telling*, een soort uit en
    een periode.
  - **E.** De route: een klik op een rij tekent het spoor (24 punten) in de
    kleur van de soort.
  - **F.** Na Uitvoeren:
    - de nieuwe paden in `catalogus.csv`;
    - `dubbel_van` wijst naar de nieuwe plek;
    - de route van een verplaatst bestand werkt nog.
  - **G.** Alleen bekijken: de download is dezelfde CSV, op de wijzigdatum na,
    en de route werkt.
  - **H.** Op 390 px: niets breder dan het scherm, en de kaart staat boven de
    filters.
- **`ordenentest.py`** 58 (gelijk):
  - eerst naar het tabblad *Ordenen*;
  - de melding van Ordenen staat in `#plan-melding`;
  - na *Logboek schrijven* volgt *Catalogus bijwerken*;
  - deel G hangt niet meer van de klok af. Tot nu toe bezette de test de
    logboeknamen van de komende 15 seconden. In de volledige ronde, met een
    tweede browsertest ernaast, duurde het één keer langer, en kreeg het
    logboek een vrije naam. Nu ligt de naam van die ronde vast (via
    `ORDENEN.logboekNaam`), en staat dat bestand er al.
- **`test_zipref.py`:** `telarchief.html` doet mee; de kop van `catalogus.csv`
  sluit aan.
- **Bekeken:** het overzicht op 1300 en 390 px, met een route open.
  - Op 390 px bleken de datums in de tabel af te breken. Nu blijft elke cel op
    één regel, en schuift de tabel in zijn kader.

## 8. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telarchief.html` | Archief: tabbladen, overzicht, kaart, filters, tabel, route, `catalogus.csv`; `ORDENEN.catalogus`; blok `clusterbol` |
| `index.html` | *Archief* / *Archive*; versie v3.33 |
| `over.html`, `about.html` | Archief als verkenner |
| `traffic_counter_help.html` | *Je archief: overzicht en ordenen* |
| `privacy.html` | `catalogus.csv` en de kaarttegels (NL en EN) |
| `zip_format_reference.html` | sectie `catalogus.csv` |
| `_archief/overpass_rig/archieftest.py` | nieuw |
| `functest_ordenen.js`, `ordenentest.py`, `test_zipref.py`, `valideer.py`, `README.md`, `docs/ONTWIKKELEN.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 9. Validatie

```
valideer.py            ALLES OK — precies de 7 verwachte bestanden gewijzigd; gedeelde blokken OK,
                       nieuw: clusterbol (telrapport, telarchief); titel 61, description 151
functest_ordenen.js    50/50
archieftest.py         42/42 (nieuw)
ordenentest.py         58/58 (één keer FOUT in deel G onder belasting; nu zonder klok, daarna 2× groen)
test_zipref.py         REFERENTIE SLUIT AAN OP DE CODE (met catalogus.csv)
alle overige browsertests en de 21 functests groen; check_encoding OK
```
