# Overdracht v3.63 — Telrapport: de straten van een capaciteitstelling

Jay sleepte een capaciteits-ZIP met straten in telrapport: "Als ik die
capaciteits-zip in telrapport sleep, komt er niks op het scherm". Op het voorstel
(1. straat als lijn uit `_netwerk.csv`, 2. getal op het midden van de eigen
tikken, 3. de vakken als stippen): "eerst alleen 1 en 2".

## 1. Waarom er niets kwam

Nagespeeld met de echte geometrie van tien straten:

1. **Een straat werd een vlak.** `loadCapaciteitZip` tekende elke groep met
   `L.polygon`, ook een straat: de lijn werd gesloten. Een rechte straat geeft
   zo een vlak van bijna nul.
2. **Het getal stond op het zwaartepunt** (`getCenter`). Bij bijna nul
   oppervlakte rekent Leaflet een punt ver weg: in de nagespeelde telling op
   51,509 / 4,300, zo'n 38 km zuidelijker.
3. **`fitBounds` nam dat punt mee** en zoomde uit tot zoom 10. De straten waren
   kleiner dan een pixel.

Verder kwam de geometrie van een straat altijd van Overpass, terwijl de app hem
in `_netwerk.csv` meegeeft (de ZIP-referentie zei al dat telrapport hem daar
leest). Faalde Overpass, dan kwam er niets, alleen een `console.warn`.

## 2. De oplossing (`loadCapaciteitZip`)

- **`lineMap`**: de LINESTRING-rijen uit `_netwerk.csv` (`capLijnWkt`), naast de
  POLYGON-rijen in `polyMap`.
- **`g.straat`**: een groep uit `_capaciteit.csv` (rij krijgt `_straat`). Een
  groep uit `_terrein.csv`, of een straat waarvan de way-id in `polyMap` staat,
  blijft als voorheen een vlak met het getal op het zwaartepunt.
- **De tikken van een straat** (`capTikkenPerGroep`). Eerst op de way-id: valt
  de `osm_way_id` van een tik samen met die van een groep, dan hoort hij daar.
  Anders op de naam (`capTikNaam`: `(niet gesnapped)` als `snapped` 0 is, anders
  `straat`, of `(onbekend)` bij "—").
  - De way-id gaat voor omdat de app groepeert op de **OSM-naam** van de weg
    waarop een tik gesnapt is (`osmName`), en die staat niet in de telregels.
  - Bij een kruising is dat soms de dwarsstraat, terwijl in `straat` de straat
    staat die je liep. De test vond dat met de echte app (deel A).
- **`g.wegen`** (`capWegen`): de way-id van de groep plus die van zijn tikken. De
  way-id in `_capaciteit.csv` is maar één weg van de straat (de eerste onder die
  naam).
- **Tekenen**:
  - elke weg als `L.polyline` in pane `capaciteit` (paars, dikte 5, 8 bij
    hover), met een tooltip (naam, datum, teller, capaciteit) en een klik naar
    `showCapDetail`;
  - het getal op **`capMidden`**: het gemiddelde van de vakken van de eigen
    tikken. Zonder tikken: **`capLijnMidden`**, halverwege de langste lijn;
  - zonder lijn en zonder tikken: `zonderGeom`, zoals sinds v2.60.
- **Overpass** alleen voor de wegen die niet in `polyMap` of `lineMap` staan. Een
  ZIP uit de app vraagt dus niets meer op.
- **`(niet gesnapped)`**: krijgt nu een getal op het midden van zijn tikken (een
  gemeten plek, geen verzonnen). Zonder tikken: niet op de kaart, als voorheen.

## 3. Wat er anders wordt

- **GeoPackage**: de laag `terreinen` nam ook een straat mee, als gesloten vlak.
  Een straat is nu een lijn zonder `_capGroep`, dus alleen terreinen. Handleiding
  en ZIP-referentie zeggen het. Een eigen lijnenlaag voor capaciteitsstraten is
  niet gebouwd.
- **Alle naamloze wegen in één getal.** De app zet alles zonder naam onder
  `(onbekend)`, met één way-id. Telrapport tekent nu alle wegen van die tikken,
  met één getal in het midden. Op parkeerterreinen die als service-weg gesnapt
  zijn, staat dat getal tussen de terreinen in.

## 4. Niet gebouwd (punt 3 van het voorstel)

De vakken van een capaciteitstelling als stippen op de kaart, zodat een telling
zonder enige geometrie toch zichtbaar is. Ze verschijnen nog alleen na een klik
op een straat (`showCapDetail`).

## 5. Tests

**Nieuw: `capaciteittest.py`, 26.**

- **A. Een capaciteitstelling uit de app** (langs Noordstraat 3, 8 tikken):
  - één tik op de kruising staat in `_capaciteit.csv` onder Dwarsstraat 5;
  - een getal per regel (7 en 1), elk op het midden van de tikken op die weg;
  - lijnen, geen vlakken;
  - geen Overpass-verzoek;
  - zoom 15 of meer.
- **B. Een gemaakte ZIP, terwijl Overpass faalt (504):**
  - Rechtestraat over 9001 (bijna recht) en 9002;
  - een weg zonder naam;
  - twee niet gesnapte tikken;
  - een terrein.

  Uitkomst:
  - drie lijnen uit het netwerk en één vlak;
  - de getallen 10, 3 en 2 op het midden van hun tikken;
  - het terrein op het zwaartepunt;
  - de tooltip en de klik naar het detail;
  - alles in beeld.
- **C. Oud, zonder `_netwerk.csv` en zonder telregels:**
  - één Overpass-verzoek voor 9001;
  - een lijn van drie punten;
  - het getal halverwege.

**Nagespeeld:** de samengevoegde parkeertelling (vier pocket-tellingen, 833
plekken, niet in de repo). Voor v3.63 zoom 10, het midden boven Klaaswaal en
niets te zien. Nu 23 lijnen en 10 getallen op zoom 16, zonder Overpass.

## 6. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telrapport.html` | `loadCapaciteitZip`: `lineMap`, `g.straat`, `g.wegen`, de straat als lijn; `capLijnWkt`, `capTikNaam`, `capTikkenPerGroep`, `capWegen`, `capMidden`, `capLijnMidden`; commentaar bij de GeoPackage-laag `terreinen` |
| `traffic_counter_help.html` | capaciteit in de legenda van Telrapport; GeoPackage: straten niet mee |
| `zip_format_reference.html` | GeoPackage, *Capacity*: een straat is een lijn en staat niet in `terreinen` |
| `index.html` | versie v3.63 |
| `_archief/overpass_rig/capaciteittest.py` | nieuw |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 7. Validatie

```
valideer.py           ALLES OK — de 4 verwachte bestanden
capaciteittest.py     26/26
gpkgtest.py           ongewijzigd groen
volledige ronde lokaal: zie de PR
```
