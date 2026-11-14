# Overdracht v3.50 — telrapport: het kale wegennet als één laag

Na v3.49 vroeg Jay: "Meet het verschil maar even", over Leaflet met canvas.
Na de meting: "Het kale net als 1 laag zonder hover en klik lijkt me een goed
idee. Canvas met één lijn per wegvak voor alle wegvakken ook maken".

Canvas voor alle wegvakken zit er uiteindelijk niet in. Zie §1; Jay heeft het
voorstel daarover gekregen voor het bouwen.

## 0. De meting

Op de gemaakte set van v3.49: 185 tellingen, 42.550 wegvakken. Twee rondes per
variant, met `leaflet.css` erbij.

De rig breekt `leaflet.css` af. Zonder die CSS staan de panes niet absoluut en
klopt het tekenen en het raken met de muis niet. De meetscripts gaven hem
daarom zelf.

| variant | inzoomen | ver uitgezoomd | schuiven | bezig per muisbeweging | geheugen |
|---|---|---|---|---|---|
| SVG, zoals v3.49 | 1,35 s | 2,4 s | 0,6 s | 185 ms | 179 MB |
| canvas, zichtbare lijn + kliklijn | 0,95 s | 1,3 s | 0,34 s | 80–100 ms | 176 MB |
| canvas, één lijn per wegvak | 0,70 s | 0,7 s | 0,34 s | 80 ms | 126 MB |
| SVG, zonder kaal net | 0,48 s | 0,47 s | 0,36 s | 13 ms | |
| canvas één lijn, zonder kaal net | 0,42 s | 0,44 s | 0,29 s | 14 ms | |
| SVG, kaal net als één SVG-laag | 0,61 s | 0,73 s | 0,43 s | 16 ms | |
| SVG, kaal net als één canvas-laag | 0,65 s | 0,87 s | 0,42 s | 17 ms | |

- **Kaal** = een wegvak zonder telling en zonder bezoek. In de set waren dat er
  41.440 van de 42.550 (97%).
- **"Bezig per muisbeweging"**: de tijd die de hoofdthread van de browser bezig
  is, per muisbeweging over de kaart (CDP `TaskDuration`), met de echte muis van
  Playwright.

## 1. Canvas voor de klikbare wegvakken: niet gedaan

Een canvas is één vlak over de hele kaart. In de pane `wayhit` (z 560) ligt het
boven de stippen (`clusters`, 550), de routes (`overlayPane`, 400) en de
capaciteitsvlakken (350), en vangt daar alle muis-acties af, ook waar geen
wegvak ligt. Nagekeken met `document.elementFromPoint`, met de bollen uit:

| | SVG | canvas |
|---|---|---|
| midden van een capaciteitsvlak | het vlak | het canvas |
| een stip | de stip | het canvas |

Met canvas gaat het detailvak van een capaciteitsvlak dus niet open, en komt de
tooltip van een stip niet.

De andere weg was de wegvakken onder die lagen te leggen. Dat verandert wat er
bovenop ligt en wat klikbaar is.

Zonder het kale net blijven er ongeveer 1.100 losse lijnen over. Dan wint
canvas nog maar weinig: 14 tegen 13 ms per muisbeweging, 0,42 tegen 0,48 s
inzoomen. Jay kreeg dit voor het bouwen; het werd: de rest blijft SVG met
kliklijn.

## 2. Het kale wegennet als één laag

- **`vraagLijn(k, soort)`** vervangt `makeWayLine` + `attach…` op de vier plekken
  waar een wegvak een lijn vraagt. `soort` is `pocket` of `sessie`: welke klik en
  hover het wegvak krijgt.
  - Het wegvak komt in `lijnKeys`, in de volgorde van vragen.
  - Dat is ook de volgorde van de GeoPackage-laag `wegvakken`, zoals voorheen
    die van `wayLayers`.
- **`bouwLijnen()`** loopt aan het begin van `recolorAll`, en in `gpkgLagen`. Hij
  bekijkt wat in `teBouwen` staat:
  - **Kaal** (`isKaal`: geen entry in `wayData[k].sessions`, dus ook geen
    0-bezoek of gelopen stuk, en geen `bezoekenOp[k]`): het wegvak gaat in
    `kaalNet`. Had het een eigen lijn, bijvoorbeeld na een correctie, dan gaat
    die weg.
  - **Anders**: een eigen lijn met kliklijn (`maakLosseLijn`, zoals voorheen
    `makeWayLine` en `attach…`). Stond het wegvak in `kaalNet`, dan gaat het
    daar uit.
  - Zonder geometrie (die komt nog van Overpass) blijft het liggen. De
    terugroep vraagt opnieuw.
- **`teBouwen`** krijgt een wegvak:
  - bij `vraagLijn`;
  - bij `koppel` en `ontkoppel`;
  - bij een bezoek in `bezoekenOp`.

  Alleen wat veranderde, wordt dus opnieuw bekeken. In een bundel (v3.49)
  gebeurt dat één keer, aan het eind.
- **`tekenKaalLaag()`**: één `L.polyline` met een deel per kaal wegvak.
  - Hij krijgt de stijl die `recolorOne` een kaal wegvak gaf: `#3a3d42`,
    dikte 2, dekking 0,5.
  - Zonder klik en hover, in de nieuwe pane `kaalnet`: z 215, net boven de
    tegels, `pointer-events: none`.
  - Opnieuw opgebouwd als er een wegvak bijkomt of afgaat.
- **SVG, geen canvas:** als canvas was de laag even snel (§0), en SVG laat de
  rest van de kaart zoals hij was.
- **Wat je ziet:**
  - Het kale net ligt nu onder de routes, de stippen en de capaciteitsvlakken.
    Voorheen lag het erboven, in `wayhit`. Het is dezelfde grijze lijn.
  - Hover en klik op een kaal wegvak doen niets meer. Daar stond alleen de
    naam.
- **`resetAll`** leegt `kaalLaag`, `kaalNet`, `teBouwen`, `lijnKeys` en
  `lijnSoort`.
- **De GeoPackage** neemt een kaal wegvak mee als de kale laag op de kaart
  staat, met status `netwerk`, zoals voorheen.

## 3. Resultaat

Dezelfde set van 185 tellingen:

| | v3.49 | v3.50 |
|---|---|---|
| 185 ZIP's laden | 6,5 s | 3,9 s |
| inzoomen, per stap | 1,35–1,75 s | 0,67–0,78 s |
| ver uitgezoomd | 2,4–2,8 s | 0,85 s |
| schuiven, per stap | 0,6–0,9 s | 0,38–0,44 s |
| bezig per muisbeweging | 180–200 ms | 17 ms |
| geheugen (JS) | 179 MB | 68 MB |
| elementen op de pagina | 106.000 | 23.000 |

Drie rondes v3.49 en twee rondes v3.50, met `leaflet.css`. Hover en tooltip op
een geteld wegvak werken in beide versies hetzelfde.

**Gelijk gebleven.** Na het laden en na 16 acties zijn deze gelijk aan v3.49:

- de bollen;
- de stijl van elk wegvak (een kaal wegvak met de stijl van de kale laag);
- de tellers;
- het kwaliteitsrapport;
- de sessielijst;
- de stippen, de routes en het kaartbeeld;
- de GeoPackage-lagen, ook de volgorde van de wegvakken.

Gecontroleerd op 46 ZIP's (met echte ZIP's uit de veld-apps) en op 185 ZIP's.

## 4. Handleiding

Telrapport, na het weekprofiel: *Het kale wegennet (v3.50)*. De grijze wegen
zonder telling en zonder bezoek zijn één laag onder alles, en reageren niet op
klikken of aanwijzen. Een wegvak met een telling, een bezoek of een gelopen
stuk zonder tikken blijft klikbaar.

## 5. Tests

- **`snelheidtest.py`: 27 (was 22).** Nieuw deel G:
  - een wegvak heeft een eigen lijn of zit in de kale laag, nooit allebei;
  - kaal = `isKaal`;
  - de kale laag heeft een deel per kaal wegvak, is niet interactief en ligt
    in `kaalnet` zonder muis;
  - 20 tellingen erbij, in gebieden die al geladen zijn: wegvakken gaan van de
    kale laag naar een eigen lijn, en daarna klopt alles nog.
- **`gpkgtest.py`**: wat op de kaart staat, telt nu ook de kale laag mee.
- **`stukkentest.py`**: een niet gelopen stuk zit in de kale laag (grijs), niet
  in `wayLayers`.

## 6. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telrapport.html` | pane `kaalnet`; `vraagLijn`, `heeftLijn`, `isKaal`, `bouwLijnen`, `maakLosseLijn`, `tekenKaalLaag`; `koppel`, `ontkoppel`, `bezoekenOp` markeren; export en reset |
| `traffic_counter_help.html` | *Het kale wegennet (v3.50)* |
| `index.html` | versie v3.50 |
| `_archief/overpass_rig/snelheidtest.py`, `gpkgtest.py`, `stukkentest.py` | zie §5 |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 7. Validatie

```
valideer.py           ALLES OK — de 3 verwachte bestanden
snelheidtest.py       27/27
vergelijking          v3.49 = v3.50 op 46 en 185 tellingen
volledige ronde lokaal: zie de PR
```
