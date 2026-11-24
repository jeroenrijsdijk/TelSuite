# Overdracht v3.64 — Telplanning: een deel van een weg plannen

Jay: "in telplanning kun je alleen een compleet osm link selecteren. Wat komt
erbij kijken om maar een deel van een link te kunnen plannen?" Over waar je
knipt: "Alleen op een knoop - dat is bijna altijd een logisch zichtbare grens
buiten. zo hou je elke volgende klus daar vergelijkbaar met de vroige
tellingen", en "Alleen knopen die de weg deelt met een andere weg".

## 0. Wat er niet verandert

- **Het planlink-formaat** (`w:[[id,naam,highway,lijn]]`, versie 1). Een stuk is
  een kortere lijn met dezelfde `osm_way_id`. Het gedeelde blok planlink is
  byte-gelijk.
- **De telapps.** Ze gebruiken de planning alleen om de geplande lijn in paars
  te tekenen en het gebied vooraf op te halen. Snappen gaat over het volledige
  OSM-net, en in de ZIP komt niets van de planning. KNIME en de ZIP-schema's
  merken er dus niets van.

## 1. Wat je ziet

- **✂ Knippen** onder de selectieknoppen, met een korte uitleg als hij aan staat.
- In knipmodus een **open stip** op elke knoop binnen een weg die die weg deelt
  met een andere opgehaalde weg (kruising, inrit, pad).
- **Klik op de weg bij een open stip**: daar is hij geknipt, en de knip is een
  **zwarte stip** (ook buiten knipmodus te zien, in Maken). Klik bij een zwarte
  stip: de knip is weg en de stukken zijn één, gekozen als een van beide gekozen
  was.
- **Knipmodus uit**: een klik op een stuk kiest of zet uit, zoals een hele weg.
- **Het overzicht** zegt "4 wegen zichtbaar, in 6 stukken" en telt gekozen stukken.
  De legenda per wegtype telt wegen.

## 2. Code (`telplanning.html`)

- **Elk element van `ways` is een stuk** `van`..`tot` (knoopnummers) van zijn hele
  weg `heel = {id, coords, nodes, wkt, segments, cum}` (`heelVan`). Zonder knip
  is het 0..n−1, met `wkt` en `segments` van de hele weg, dus zoals voor v3.64.
  Selectie, stijl, zichtbaarheid en de bulkknoppen werken ongewijzigd op de
  stukken.
- **`knoopTel`**: per knoop-id in hoeveel opgehaalde wegen hij zit
  (`telKnopen`). De Overpass-vraag was al `out body geom`, dus de knopen kwamen al
  mee. **`knipbaar(heel, i)`**: niet het begin of eind, en `knoopTel > 1`.
- **`knipBij(w, latlng)`**: de dichtstbijzijnde knip-of-plakplek op het stuk
  binnen `KNIP_PX` (18 px). `knip` → twee stukken (`maakStuk`, `vervangStukken`);
  `plak` (een eind dat een knip is) → samen met de buur.
- **`stukBij(latlng)`**: bij een kruising liggen de klikzones (18 px) over
  elkaar, en de bovenste is niet per se de bedoelde straat. In knipmodus kiest
  telplanning het stuk waarvan de lijn het dichtst bij de klik ligt.
  - De test vond dit: een klik 9 px naast een kruising op de Langestraat knipte
    de Zijstraat.
- **`tekenKnippen`**: eerst de open stippen (`.knip-kan`), dan de zwarte knippen
  (`.knip-punt`) erover. Niet in Dekking.
- **De planning**: `planStukken` voegt per weg de gekozen stukken samen die aan
  elkaar liggen. Een stuk dat de hele weg is, krijgt de originele WKT
  (byte-gelijk); een deel krijgt `coordsWkt`. `n_wegen` = het aantal regels.
- **Een link of hertelling** heeft geen knopen:
  - `el.deel` laat in `processWays` twee stukken van dezelfde weg toe;
  - komt de weg later van Overpass (de omgeving na het openen, of een getekende
    contour), dan legt `herstelUitOverpass` elk stuk op de knopen van de echte
    weg (`knoopIndex`, binnen 3 m; de link heeft 5 decimalen, ±1 m);
  - de rest van de weg komt erbij als niet-gekozen stukken, de knippen staan er
    weer;
  - past een stuk niet (de weg is in OSM veranderd), dan blijft het zoals het
    was. Knippen op zo'n stuk geeft een melding.
- **Dekking**: per stuk de segmenten (±40 m) van de hele weg met hun midden in
  het stuk (`stukSegmenten`), elk precies één keer. `coverageForWay` rekent over
  de hele weg, en `updateCoverageStats` telt een geknipte weg één keer.

## 3. Handleiding

Telplanning, onder Selectie: *Een deel van een weg (sinds v3.64)*. Waar je kunt
knippen en waarom, klikken, uitzetten, een knoop in OSM toevoegen als hij
ontbreekt, en wat er in de link en de telapps gebeurt.

## 4. Tests

**Nieuw: `knipplantest.py`, 40.** Een nep-Overpass met:
- de Langestraat (500): zes knopen, waarvan knoop 13 gedeeld met de Zijstraat
  (501) en knoop 15 met een inrit (502); 12 en 14 zijn vormpunten;
- een losse straat (503).

De delen:
- **A. Open stippen** alleen op 13 en 15 van de Langestraat en op 13 van de
  Zijstraat (de inrit eindigt er).
- **B. Echte muisklikken:**
  - een vormpunt knipt niet;
  - bij 13 en 15 wel, dus drie stukken;
  - de Zijstraat blijft heel;
  - een klik kiest alleen het middelste stuk uit;
  - het overzicht en de legenda kloppen.
- **C. De planning:**
  - twee regels voor de Langestraat;
  - `n_wegen` = 5;
  - een hele weg byte-gelijk;
  - alles gekozen geeft één hele regel;
  - aangrenzende stukken worden één regel.
- **D. Een knip weghalen.**
- **E. De link heen en terug:**
  - eerst de twee stukken, daarna drie stukken op de knopen (gekozen, niet,
    gekozen), met de knopen van de echte weg en de knippen;
  - dezelfde planning;
  - een knip weghalen kan.
- **F. Overpass kapot:** de stukken uit de link blijven en gaan weer in de
  planning; knippen geeft een melding.
- **G. Dekking:** geen stippen, en elk segment in precies één stuk.
- **H. Parkeertelling** opent de link: vijf regels, twee van de Langestraat.

De test serveert `leaflet.css` zelf (de rig breekt CSS af), zodat de muisklikken
echt op de lijnen vallen.

## 5. Open

- **Pocket telt per segment van ±40 m over de hele weg.** Een geplande stuk
  loopt dus niet gelijk met de segmentgrenzen in de ZIP. Dat hoeft ook niet: de
  planning zegt waar je loopt, de ZIP wat je zag.
- **Hertelling uit een ZIP (Hertelling-vak)** maakt nog altijd een planning van
  hele wegen.

## 6. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telplanning.html` | knippen: `heel`/`van`/`tot`, `knoopTel`, `knipBij`, `stukBij`, `tekenKnippen`, `planStukken`, `herstelUitOverpass`; knop en uitleg; overzicht en legenda; dekking per hele weg |
| `traffic_counter_help.html` | *Een deel van een weg (sinds v3.64)* |
| `index.html` | versie v3.64 |
| `_archief/overpass_rig/knipplantest.py` | nieuw |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 7. Validatie

```
valideer.py           ALLES OK — de 3 verwachte bestanden; planlink byte-gelijk
knipplantest.py       40/40
planlinktest.py       ongewijzigd groen
volledige ronde lokaal: zie de PR
```
