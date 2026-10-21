# Overdracht v3.20 — de tegelcache hersteld

Jay, de ochtend na v3.19: "Er vallen sinds kort rare gaten in het gedownload of
bewaarde netwerk — niet alle links worden gedownload. Waardoor ook de tikken
niet op de juiste link terecht komen." Bij zijn melding zaten een plaatje uit
telrapport en twee ZIP's: een fietstelling (`_fts`) en de reconstructie ervan
(`_recon`). Die telling was in Chrome geopend via een planning-link uit WhatsApp.

## 1. Wat de ZIP's lieten zien

- **Het netwerk is compleet.** De H de Lintweg (way 1478876715, cycleway) staat
  er helemaal in, van de Nieuwstraat tot de Gorsstraat, en alle 9 tikken staan
  erop: in de app en in de reconstructie.
- **De gaten zitten in telrapport.** De reconstructor knipt elke weg in stukken
  van ~40–60 m (`segment_index`), zoals pocket. Telrapport leest een fiets- of
  autotelling per hele weg en pakt van een gereconstrueerde ZIP alleen het
  eerste stuk. Gemeten in Chromium, H de Lintweg:

  | ZIP | punten van de H de Lintweg | tikken in een cluster |
  |---|---|---|
  | origineel | 5 | 9 van 9 |
  | `_recon` | 3 | 5 van 9 |

  De 4 tikken op het tweede stuk staan los, zoals op het plaatje. Dit zit er al
  lang in. Jay ziet het nu omdat hij sinds kort reconstrueert, en telrapport bij
  een paar standaard de `_recon` laadt (sinds v2.74). Jay koos **B: telrapport
  per stuk**, zoals pocket. Dat wordt v3.21; zie §6.
- **Het netwerk was veel te groot: 1926 ways (250 kB)** voor een fietstelling
  van vijf minuten. Uit de cache komt de inhoud van hele tegels, en sinds het
  gebied vooraf (v3.19) komt elke fetch uit de cache. Zie §3.
- De reconstructie draaide op het netwerk uit de ZIP
  (`netwerk_bron;origineel uit ZIP (geen topologie)`, `adjacency_ways;0`). De
  fout van §2 raakte deze reconstructie dus niet.

## 2. Knooppunten in de tegels (fout uit v3.19)

**De fout.** Pocket en de reconstructor bouwen uit de knooppunten van een weg
(`nodes`) welke straten op elkaar aansluiten. Het gebied vooraf (v3.19) haalde
op met de zoekvraag van de parkeer-apps, `out tags geom`, en die levert geen
knooppunten. In het hele geplande gebied stonden dus wegen zonder knooppunten
in de cache:
- **pocket** zag geen aansluitingen. Een tik bleef aan de vorige straat hangen
  tot de loper 50 m verder was;
- **de reconstructor** kon na *Netwerk ophalen* niet van straat naar straat
  routeren ("0 met buren").

De parkeer-apps schreven al sinds v2.43 zulke tegels. Die raakten maar zelden
compleet, dus het viel niet op.

**De reparatie.**
- **Overal `out body geom`:**
  - in het gebied vooraf (gedeeld blok `gebied vooraf`);
  - in `fetchRoads` van de drie parkeer-apps (gedeeld blok
    `fetch-discipline`);
  - pocket en de reconstructor deden het al.
- **Tegelschema 3:** een tegel draagt wegen met knooppunten.
  - `leesTegels` (vier veld-apps), `gebiedNodig` en `tegelVers` in de
    reconstructor tellen een tegel van een lager schema als ontbrekend. De
    cache geneest zichzelf; Jay hoeft niets te legen.
  - `tegelVers` keek tot nu toe niet naar het schema.
- **Geen knooppunten in het eigen netwerk van de parkeer-apps.** Die gebruiken
  ze niet. `pasNetwerkToe` laat ze weg, zodat noodkopie en `_netwerk.csv` niet
  groeien.
- **Geen tegel van een weg zonder knooppunten.** Een tegel met zo'n weg gaat de
  cache niet in (`cacheWaysInTiles`, `gebiedBewaar`).

## 3. Alleen de cirkel uit de cache

`leesTegels` gaf alle wegen van alle tegels die de fetch-cirkel raken. Een
tegel is ~1,1 × 0,7 km, de cirkel 300 m. Nu laat `wegInCirkel` alleen de wegen
door waarvan een punt of segment binnen de cirkel ligt, wat Overpass met
`around` ook had gegeven. Het netwerk na een cache-treffer is daarmee zo groot
als na een verzoek. Jay: "Punt is goed."

## 4. Twee oudere zwaktes in het schrijven van tegels

Ze vielen pas op nu de cache veel vaker gelezen wordt. Allebei zitten ze in
`cacheWaysInTiles` (gedeeld blok, vier veld-apps).

- **Hele cellen.** Een tegel is compleet als zijn 8×8 cellen gedekt zijn door
  de cirkels van de sessie. Een cel telde als gedekt als zijn **midden** in een
  cirkel lag. Aan de rand van het gelopen gebied kon een tegel dan als compleet
  de cache in, terwijl de hoek van een cel buiten elke cirkel lag. Een weg daar
  ontbrak dan. Nu telt een cel pas als alle vier zijn hoeken binnen één cirkel
  liggen.
- **Toewijzing per segment.** Een weg hoorde bij de tegels waarin een **punt**
  van de weg lag. Een lang segment dat een tegel doorsnijdt zonder er een punt
  te hebben, ontbrak in die tegel. Nu bepaalt `tegelsVanWeg` de tegels per
  segment (de tegels onder zijn bbox). Dezelfde regel geldt in `gebiedBewaar` en
  in `wayTileKeys` van de reconstructor.
- **Erbij.** Na het wegschrijven van een tegel brak de toewijzing bij een
  volgende fetch die die tegel raakte stil af (een TypeError in de `try`). Daarna
  schreef de app in die sessie geen tegels meer. Opgelost.

`functest_tegelcache.js` toont het met de code van v3.19 aan. Een cirkel van
600 m rond het midden van een tegel raakt alle celmiddens maar niet alle
hoeken. Toch ging de tegel als compleet de cache in, zonder de lange weg die
hem doorsnijdt.

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `parkeertelling.html`, `fietsparkeren.html`, `capaciteitstelling.html` | `out body geom` in `fetchRoads`; `pasNetwerkToe` zonder knooppunten; blokken `cacheWaysInTiles` en `leesTegels` (zie hieronder) |
| `parkeertelling.html`, `fietsparkeren.html`, `pocket_count.html` | blok `gebied vooraf`: `out body geom`, `tegelsVanWeg`, geen tegel zonder knooppunten |
| alle vier de veld-apps | `cacheWaysInTiles` (hele cellen, `tegelsVanWeg`, knooppunten, geen afbreken na wegschrijven); `leesTegels` (schema 3, `wegInCirkel`) |
| `telreconstructie.html` | `TEGEL_SCHEMA` 3, `tegelVers` kijkt naar het schema, `wayTileKeys` per segment; `RECON_VERSIE` v3.20 |
| `index.html` | versie v3.20 |
| `_archief/overpass_rig/functest_tegelcache.js` | nieuw |
| `functest.js`, `functest_pocket.js`, `functest_gebied.js`, `gebiedtest.py` | bijgewerkt (schema 3, cirkel, deel F) |
| `valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt; de groep `cacheWaysInTiles` begint nu bij het commentaar, zodat `tegelsVanWeg` meedoet |

Het ZIP-schema verandert niet. Een `_recon` draagt nu `reconstructie_versie` v3.20.

## 6. Telrapport per stuk (v3.21, nog te bouwen)

Jay koos B: een gereconstrueerde fiets- of autotelling in telrapport per stuk
van ~50 m, met de aantallen uit de telregels en gelopen stukken zonder tikken
zichtbaar, zoals bij pocket.

Daar zit nog één vraag aan vast. Telrapport telt sessies op dezelfde straat
samen per sleutel: per weg of per stuk.
- **B1:** alleen de `_recon` per stuk. Een straat met originelen en
  reconstructies heeft dan twee lijnen over elkaar, en de bezettingsgraad
  middelt niet meer over alle sessies.
- **B2:** ook originelen per stuk, met hetzelfde knippen als de reconstructor
  en tikken ingedeeld naar hun plek langs de weg. Consistent, maar groter: de
  GeoPackage-export en de correctietool moeten mee.

Voorstel: B2.

## 7. Validatie

```
VALIDATIE
```
