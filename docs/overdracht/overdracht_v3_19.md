# Overdracht v3.19 — planning terug in telplanning, gebied vooraf, ruimer verversen

Jay, uit de backlog ("Slim lopen en planning"):
1. een link terug openen in telplanning om een planning aan te passen ("nu teken
   je opnieuw");
2. het gebied vooraf ophalen, zodat je in het veld geen Overpass-verzoeken meer
   nodig hebt;
3. fetch-radius en verversafstand ruimer zetten ("vraagt een veldtest").

Na het ontwerpgesprek koos hij:
- **1A, met omgeving:** de straten rond de planning komen er grijs bij;
- **2, automatisch:** ophalen zodra de link opent, zonder knop;
- **3, 300/220:** radius 300 m, verversen op 220 m.

## 1. Planning uit een link (telplanning)

Telplanning heeft een nieuw veld: **Of: planning uit een link**. Je plakt de
link en klikt *Openen*, of je drukt op Enter. Telplanning leest ook
`telplanning.html#plan=…` bij het openen. Een link naar parkeertelling,
fietsparkeren of pocket (`#parkeren&plan=…`) werkt alle drie; een punt of
haakje erachter (van een mailprogramma) ook.

- Het blok `planlink` pakt de link uit. Het blok zelf is ongewijzigd.
- De straten gaan, net als bij de *Hertelling* uit een ZIP, als
  pseudo-Overpass-elementen door `processWays`, allemaal gekozen. Naam, datum,
  tijd, teller en teltype komen in de velden.
- Daarna haalt telplanning de **omgeving** op: een rechthoek om de straten,
  `LINK_OMGEVING_M` (100 m) ruimer, via `fetchWaysForPolygon`, met voortgang,
  tijdslimiet en `ovpKeur` (v3.9). Een polygoon met `omgeving: true` laat
  `processWays` niets kiezen. De straten eromheen komen dus grijs in beeld, en
  met een klik erbij, zoals na het tekenen.
- *Wis alles* en *Voeg contour toe* staan aan. Na het aanpassen maak je met
  *Deel als link* een nieuwe link.
- De getekende contour zit niet in de link en komt dus niet terug. Het
  linkformaat is niet veranderd.
- Een link zonder `#plan=` of een kapotte link geeft een melding in de
  statusbalk. Wat er al stond, blijft staan.

## 2. Gebied vooraf ophalen (veld-apps)

**Waarom in de veld-app, en niet in telplanning.** De tegelcache (IndexedDB
`telsuite_osm`) staat in de browser van het toestel. Haalde telplanning het
gebied op de desktop op, dan zou het daar staan, niet op de telefoon. Het
backlogidee stamt van vóór de links. Nu gebeurt het daar waar de link opent: in
parkeertelling, fietsparkeren en pocket.

**Nieuw gedeeld blok `gebied vooraf`**, byte-identiek in die drie apps:
- **Welke tegels.** `gebiedTegels` verdicht de geplande straten tot een punt
  om de 25 m. Per punt neemt het alle tegels die `leesTegels` zou vragen voor
  een fetch-cirkel tot 50 m naast de straat (`GEBIED_MARGE_M`), met de
  fetch-radius van de app: 300 m in de parkeer-apps, 250 m in pocket.
  `functest_gebied.js` controleert dat er nergens een tegel buiten de set
  nodig is, ook midden op een lange rechte straat.
- **Wat er al is.** `gebiedNodig` slaat tegels over die korter dan 7 dagen
  geleden zijn opgehaald (de helft van de TTL van 14 dagen). Een tweede keer
  openen kost niets, en een tegel gaat na het openen zeker nog 7 dagen mee.
- **Eén verzoek.** `gebiedQuery` gebruikt de zoekvraag van het veld
  (`HIGHWAY_RE`, `building_passage`, `out tags geom`), met per rij
  aaneengesloten tegels één bbox op de tegelgrenzen, en zonder `around`.
  Overpass ziet het geplande gebied, niet je positie.
- **De cache in.** Elke gevraagde tegel is helemaal gedekt en mag dus de cache
  in (de regel van `cacheWaysInTiles`). `gebiedBewaar` schrijft ze weg, ook
  lege. Een weg hoort, net als in `cacheWaysInTiles`, bij elke tegel waarin
  een punt van de weg ligt.
- **Als het misgaat.**
  - Het antwoord gaat door `ovpKeur`.
  - Bij een rate-limit vraagt de app niet ook de tweede server.
  - Een afgebroken antwoord of een fout: dan de tweede server.
  - Lukt het nergens, of is het gebied groter dan 30 tegels
    (`GEBIED_MAX_TEGELS`, ~23 km²), dan gebeurt er niets, en werkt het veld
    zoals vroeger.
- **De regel.** `gebiedTekst` maakt een korte regel, bijvoorbeeld
  `gebied klaar (6 tegels, 830 kB opgehaald)`, `… al bewaard)`,
  `gebied niet klaargezet: Overpass is overbelast` of
  `gebied te groot om klaar te zetten (44 tegels)`.
  - Parkeertelling en fietsparkeren zetten die achter de opdracht in de
    statusregel, maar niet meer zodra je telt.
  - Pocket zet het kort in de opdrachtregel boven de telvakken
    (`gebied klaar`), met de hele tekst in de tooltip.
- **Eén kanttekening.** Opent de teller de link pas in het veld, dan kan de
  eerste fetch van het veld nog net vóór de tegels komen; pocket-parkeren
  start meteen. Dat kost één gewoon verzoek; daarna komt alles uit de tegels.
- **De servers.** Pocket noemt zijn servers `SNAP_OVERPASS`, de parkeer-apps
  `OVERPASS_ENDPOINTS`. Die gaan daarom als parameter mee, zodat het blok
  byte-identiek blijft.

## 3. Verversafstand 220 m

- **Parkeertelling, fietsparkeren, capaciteitstelling:** `ROAD_CACHE_DIST` van
  150 naar 220 m; de radius blijft 300 m. `valideer.py` bewaakt dat de waarde in
  de drie apps gelijk is (gedeelde constante `verversafstand`).
- **Pocket:** nieuwe constante `SNAP_ROAD_VERVERS_M = 170` in plaats van
  `0,6 × 250 = 150`, met dezelfde marge van 80 m.

Volgens de rekensom van v2.49 scheelt dit een derde van de verzoeken, tegen
dezelfde bytes per verzoek.

**Waarom de snap-kandidaten niet mee hoeven.** `SNAP_SEGS_RADIUS` (480 m, in
pocket 400 m) was afgeleid als fetch-radius plus de drift vóór een nieuwe
fetch. Met 220 m drift komt dat op 520 m (in pocket 420 m). Dat hoeft niet mee
omhoog. Wat tot de volgende fetch te snappen valt, ligt binnen de drift plus
de snap-afstand: 220 + 50 = 270 m (pocket: 170 + 50 = 220 m). Dat valt al binnen
de verse cirkel van 300 m (pocket: 250 m). Het commentaar in pocket zegt dat
nu.

## 4. Privacy en handleiding

**Privacyverklaring.**
- Overpass krijgt "een gebied rond je positie, of het gebied van een planning".
- De wegencache laat ook zien waarvoor je een planning hebt geopend.
- Het Engelse deel zegt hetzelfde.

**Handleiding.**
- *GPS & OSM wegsnapping*: verversen op 220 m, eerst de cache.
- *Planning als link*: twee nieuwe stukken, *Gebied klaarzetten* en *Planning
  aanpassen*. De mail bewaren verwijst nu naar *Planning aanpassen*.

## 5. Veldtest (Jay)

Pocket schrijft in `_snap_trace.csv` per fetch waar het netwerk vandaan kwam:
- `tegelcache`: uit de cache;
- `fetch` en `fetch_leeg`: van Overpass.

De parkeer-apps schrijven dat niet. Daarom met pocket-parkeren:
1. **Met een planning.** Open de link thuis. In de regel boven de telvakken
   staat *gebied klaar*. Loop de wijk. In `_snap_trace.csv` hoort na het begin
   alleen `tegelcache` te staan, geen `fetch`.
2. **Zonder planning,** een stuk dat je nog niet eerder liep (geen cache). Het
   aantal `fetch`-regels per kilometer hoort een derde lager te zijn dan in een
   pocket-ZIP van vóór v3.19 (150 m → 170 m in pocket; in de parkeer-apps
   150 → 220 m).
3. **Let op het snappen.** Komen tikken op een verkeerde straat, of zie je
   meer niet-gesnapte tikken dan vroeger? Dan is de marge te krap, en terug
   naar 150 m is één getal.

## 6. Tests

**`functest_gebied.js`** (nieuw, 22 tests, Node, geen modules):
- het blok gelijk in de drie apps;
- de tegelset dekt elke fetch-cirkel tot 50 m naast een straat, ook bij een
  lange rechte straat, een negatieve lengtegraad en een tegelhoek;
- de zoekvraag: bboxen per rij op de tegelgrenzen, de filters van het veld,
  geen `around`;
- de regel.

**`gebiedtest.py`** (nieuw, 41 tests, Chromium, nep-Overpass die bboxen echt
beantwoordt):
- *A, parkeertelling:*
  - één verzoek met bboxen;
  - precies de verwachte tegels vers in de cache, met de straat erin;
  - Start en 300 m lopen over de geplande straat: geen verzoek, en de tikken
    snappen op die straat;
  - opnieuw openen: geen verzoek, *al bewaard*.
- *B, fietsparkeren en pocket:*
  - fietsparkeren: één verzoek, *gebied klaar*;
  - pocket: kort in de regel, de hele tekst in de tooltip;
  - pocket lopen: geen verzoek, en de trace zegt `tegelcache`.
- *C, als het misgaat:*
  - een rate-limit: server 2 wordt niet gevraagd, en het veld haalt daarna
    gewoon onderweg op;
  - een remark bij server 1: server 2 levert;
  - beide servers kapot: twee pogingen, niets in de cache;
  - te groot: geen verzoek.
- *D, verversafstand:*
  - parkeertelling en capaciteit: op 200 m geen nieuw verzoek, op 240 m wel;
  - pocket: op 150 m niet, op 190 m wel.
- *E, telplanning:*
  - `#plan=` bij het openen: de velden terug, alleen de geplande straten
    gekozen, de omgeving erbij in één verzoek;
  - *Deel als link* geeft dezelfde planning, en een aangeklikte buurstraat
    komt erin;
  - plakken van een pocket-link met een punt erachter werkt;
  - een link zonder planning, of een kapotte: een melding, en niets gewist.

De bestaande `planlinktest.py` (51) blijft groen. Die opent links ook, en
haalt nu dus ook het gebied op.

## 7. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telplanning.html` | veld *planning uit een link*, `openPlanningUitLink`, `linkWaardeUit`, `linkOmgeving`; `#plan=` bij openen; `processWays` kiest de omgeving niet |
| `parkeertelling.html`, `fietsparkeren.html` | blok `gebied vooraf`; aanroep in `loadPlanFromUrl`; `ROAD_CACHE_DIST` 220 |
| `pocket_count.html` | blok `gebied vooraf`; aanroep in `laadPkPlanning`, regel en tooltip in `toonPkPlanning`; `SNAP_ROAD_VERVERS_M` 170, commentaar bij `SNAP_SEGS_RADIUS` |
| `capaciteitstelling.html` | `ROAD_CACHE_DIST` 220 |
| `privacy.html` | Overpass en de wegencache: ook het gebied van een planning |
| `traffic_counter_help.html` | *GPS & OSM wegsnapping*, *Gebied klaarzetten*, *Planning aanpassen* |
| `index.html` | versie v3.19 |
| `_archief/overpass_rig/functest_gebied.js`, `gebiedtest.py` | nieuw |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt: groep `gebied vooraf`, constante `verversafstand`, release |

## 8. Validatie

```
valideer.py           ALLES OK — 8 verwachte bestanden gewijzigd; gedeelde blokken OK (gebied vooraf nieuw: c57af75b; planlink, leesTegels, cacheWaysInTiles, OVP-blok ongewijzigd); constante verversafstand 220 in 3 bestanden
functest_gebied.js    22/22 (nieuw)
gebiedtest.py         41/41 (nieuw; drie keer gedraaid)
laadtest.py           45/45
hersteltest.py        133/133
statictest.py         24/24
opruimtest.py         139/139
logicatest.py         30/30
robuusttest.py        87/87
planlinktest.py       51/51
onderhoudtest.py      17/17
opslaantest.py        48/48
gpkgtest.py           80/80
functests             alle 19 groen
test_zipref.py        referentie sluit aan op de code
check_encoding.py     alles geldige UTF-8
```
