# Overdracht v3.51 — Passanten: de dagcurve 3 keer zo snel

Jay, na de snelheidswinst in telrapport: "is er in passanten.html ook nog iets
te versnellen?" Na de meting en het voorstel: "die mag je maken".

## 0. De meting

Twee gemaakte sets winkelstraattellingen in één centrum: een raster van
straten met stukken van 40 m. Elke telling loopt vier straten heen en terug,
met gps elke 2 s, tikken en bezocht. De tellingen zijn verspreid over juni
tot oktober, 9 tot 17 uur.

| | 150 tellingen, 100 stukken | 300 tellingen, 250 stukken |
|---|---|---|
| ZIP's laden | 1,1 s | 2,3 s |
| dag of uur kiezen, stukken kiezen, weekoverzicht, CSV's | 10–30 ms | 10–30 ms |
| de dagcurve uitrekenen (`dagcurveVan`) | 1,6 s | 2,9–3,6 s |

Alleen de dagcurve doet er dus toe. Volgens het CPU-profiel zat de tijd in de
marge: dezelfde schatting nog 200 keer, op trekkingen van de tellingen (v3.43).
Elke trekking bepaalt opnieuw wat te scheiden is (`dcGroepen`, union-find).

- **De union-find** werkte met tekst als sleutel ('u5003:2|A', 'm4:13'). De
  functie `wortel` alleen was al 16% van alle tijd.
- **De nummering in `dcSchat`** zocht per trekking elke waarneming op met
  tekst.

## 1. De wijziging

- **`dcIds(obs)`** geeft elke waarneming één keer vaste nummers, en bewaart ze
  op de waarneming zelf:
  - `ui` voor stuk|richting;
  - `mi` voor weekdag:uur;
  - `ki` voor het vakje (dagtype:uur).

  De nummers komen uit `DC_ID`. De trekkingen gebruiken dezelfde
  waarnemingen steeds opnieuw, dus daarna is het alleen nog rekenen met
  getallen.
- **`dcVereniging(n)`**: union-find op een `Int32Array`, met padhalvering zoals
  voorheen.
- **`dcGroepen`**:
  - stap 1: stukken 0 … U−1, en daarna de momenten;
  - stap 2: werkdagen 0–4, en daarna de uren.

  De groepen en de volgorde zijn dezelfde, dus ook de grootste groep.
- **`dcSchat`** nummert de stukken en vakjes per trekking via
  `Int32Array`-tabellen. De volgorde is dezelfde als voorheen (volgorde van
  eerste voorkomen), dus het rekenwerk is precies hetzelfde.

De uitkomst is byte voor byte gelijk aan v3.50: index, marges, aantallen, de
dagcurve van een keuze, en `dagcurve.csv`. In de browser gecontroleerd op beide
sets (de JSON van `dagcurveVan`), en in de test hieronder.

## 2. Resultaat

| | v3.50 | v3.51 |
|---|---|---|
| 150 tellingen | 1,6 s | 0,54 s |
| 300 tellingen | 2,9–3,6 s | 0,8–1,0 s |
| `functest_dagcurve.js`, 100 tellingen (Node) | 1,2 s | 0,2 s |

Wat overblijft, is voor de helft het schatten zelf (iterative proportional
fitting). Dat kan alleen sneller met minder trekkingen of een grovere
stopregel, en dan veranderen de marges. Dat is daarom niet gedaan.

## 3. Tests

**`functest_dagcurve.js`: 46 (was 39).** De test zet de oude versie ernaast
(`dcGroepen` op tekst en de oude nummering in `dcSchat`, als tekst in de test)
en eist dezelfde dagcurve, dagcurve van een keuze en `dagcurve.csv`. Dat
gebeurt op twee sets:

- de 100 tellingen van de test;
- een set met zondag en een losse straat (die niet te scheiden is).

## 4. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `passanten.html` | `DC_ID`, `dcId`, `dcIds`, `dcVereniging`; `dcGroepen` en de nummering in `dcSchat` |
| `index.html` | versie v3.51 |
| `_archief/overpass_rig/functest_dagcurve.js` | de vergelijking met de oude versie |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 5. Validatie

```
valideer.py            ALLES OK — de 2 verwachte bestanden
functest_dagcurve.js   46/46
volledige ronde lokaal: zie de PR
```
