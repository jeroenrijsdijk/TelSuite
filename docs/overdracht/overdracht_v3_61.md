# Overdracht v3.61 — Telrapport: van een bol naar zijn wegvak

Jay: "In de laatste versie van telrapport.html liggen de linkjes onder de
stippen en de lokatie cluster bollen. Daarom kan ik de link niet meer
aanklikken."

## 0. Nagemeten

Op de gemaakte set met veld-app-ZIP's (222 getelde wegvakken) heb ik per wegvak
5 punten langs de lijn genomen. Per punt heb ik met `document.elementFromPoint`
gekeken wat er bovenop ligt, met `leaflet.css` erbij.

| zoom | kliklijn | stip | bol |
|---|---|---|---|
| 16 | 3 | 0 | 117 |
| 17 | 31 | 0 | 69 |
| 18 | 29 | 0 | 11 |

**v3.45, v3.49, v3.50 en v3.60 geven precies hetzelfde.** Er is dus niets
veranderd:

- **De stippen** (pane `clusters`, z 550) liggen onder de kliklijnen (`wayhit`,
  560).
- **De bollen** (`cluster-badges`, 620) liggen erboven. Een bol ligt op zijn
  wegvak, en bij parkeren liggen ze in een rij over de straat.

Wat wel veranderd is: sinds v3.50 reageren grijze wegvakken (geen telling,
geen bezoek) niet meer op klikken. Jay: "De grijze vakken hoef ik niet aan te
kunnen klikken."

**Waarom de bollen niet onder de wegvakken:** de bollen liggen precies op de
lijn. Een kliklijn van 16 px erboven maakt ze onbereikbaar.

## 1. De oplossing

Voorgesteld en goedgekeurd ("Je voorstel bij 2 is erg slim, maak maar!"):

- **Het paneel van een bol** (`showClusterDetail`) begint met een knop
  "wegvak: <straat> →" (`wegvakKnop`). Die opent `showWegvakDetail` voor het
  wegvak onder de bol.
- **De sleutel** komt uit het segmentpad van `drawClusters`, dat al per wegvak
  en zijde groepeert (`groups[gkey].k`).
- **Het "0"-bolletje** (bezocht, niets geteld) had geen klik. Het opent nu het
  wegvak direct.
- **Een bol uit het gap-pad** (pocket zonder wegvakken) heeft geen wegvak en
  dus geen knop.
- **De klik op de knop** gaat via één luisteraar op `#detail-body`.

## 2. Tests

**`tijdfiltertest.py`: 41 (was 39).** Nieuw deel K, op de
pocket-parkeertelling:

- een bol klikken geeft de knop, met een wegvak van die telling;
- de knop opent de details van dat wegvak.

`functest_shiftsolo`, `functest_coordinaten`, `functest_kort` en
`functest_verzameling` (die stukken van `drawClusters` knippen) zijn
ongewijzigd groen.

## 3. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telrapport.html` | `wegvakKnop`; `showClusterDetail(…, k)`; de sleutel in het segmentpad; de klik op het "0"-bolletje; CSS `.bol-wegvak` |
| `traffic_counter_help.html` | *Van een bol naar zijn wegvak (v3.61)* |
| `index.html` | versie v3.61 |
| `_archief/overpass_rig/tijdfiltertest.py` | deel K |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 4. Validatie

```
valideer.py           ALLES OK — de 3 verwachte bestanden
tijdfiltertest.py     41/41
volledige ronde lokaal: zie de PR
```
