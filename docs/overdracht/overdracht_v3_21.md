# Overdracht v3.21 — telrapport per stuk voor fiets en auto

Bij v3.20 bleek dat telrapport van een gereconstrueerde fiets- of autotelling
alleen het eerste stuk van elke weg toonde. Jay koos uit drie routes:
- **A**: terug naar hele wegen;
- **B1**: alleen de `_recon` per stuk;
- **B2**: alles per stuk.

Hij koos B2: "de korte stukken geven een mooier beeld. Ik wil al langer meer op
segment basis werken, omdat openstreetmap wegvakken ook heel willekeurig kunnen
zijn. Met vaste lengtes breng je er wat meer systeem in."

Het ZIP-schema verandert niet. Alleen telrapport en de handleiding.

## 1. Wat er verandert

Nieuw blok **Stukken voor fiets en auto** in `telrapport.html`.

- **Knippen.** `splitWayIntoSegments` staat nu ook in telrapport, byte-identiek
  aan telreconstructie en pocket. De groep `splitWayIntoSegments` in
  `valideer.py` telt nu drie bestanden. Een weg wordt in stukken van gelijke
  lengte geknipt, zo dicht mogelijk bij 40 m; een weg korter dan 60 m blijft
  heel. Dezelfde weg geeft zo in elke app dezelfde sleutels (`way:stuk`), en
  tellingen op hetzelfde stuk tellen samen op, ook een origineel met een
  reconstructie of met pocket.
- **Laden** (`laadStukken`).
  - Een `_netwerk.csv` met `segment_index`, dus een `_recon`, levert zijn
    stukken zelf.
  - Zonder `segment_index`, dus een origineel, knipt telrapport.
  - Per weg bewaart telrapport de hele lijn (`wegGeometrie`) en het aantal
    stukken (`wegAantal`).
- **De tik** (`stukVanTik`, `tikSeg`).
  - Een tik gaat naar het stuk waar zijn marker langs de weg staat. Dat is
    dezelfde rekensom als `segIdxFor` in de reconstructor: de positie langs de
    weg, gedeeld door de stuklengte.
  - Een `_recon` neemt zijn eigen `segment_index` mee.
  - Het stuk staat in `r._seg`. Velden met `_` gaan niet mee in de export van
    de correctietool.
- **Aantallen per stuk** (`telPerStuk`) komen uit de telregels, niet meer uit
  `_straten.csv`. Die telt per straat, en verdeelde een straat met twee ways
  door de helft af te ronden.
  - Fiets: fiets, brommer, breed, wrak en het totaal.
  - Auto: goed, fout, leeg, spec. Daarbij bezet = goed + fout + spec, vrij =
    leeg, en de bezettingsgraad = bezet / (bezet + vrij), dezelfde formule als
    `buildStratenCsvString` in parkeertelling.
- **Gelopen zonder tikken** (`gelopenStukken`): bij een `_recon` uit
  `_bezocht.csv` (`n_tellingen = 0`), bij een origineel uit het GPS-spoor
  (`detectZeroVisited`, zoals pocket). Getekend gestreept in de kleur van de
  telling. Bij een origineel kan een stuk direct naast de route ook meetellen;
  bij Jays telling de dienstweg parallel aan de H de Lintweg.
- **Clusters, dekking, polygoonrapport** gebruiken `tikSeg`.
- **Correctietool.**
  - Na een verplaatsing of een zijwissel rekent `naCorrectie` het stuk en de
    aantallen opnieuw uit en tekent hij opnieuw. Tot v3.21 bleven de kleuren
    van de wegen staan na een correctie.
  - De zijwissel en de keuzelijst van wegen gebruiken de hele weg (`heleWeg`),
    niet het eerste stuk.
- **GeoPackage:** de laag `wegvakken` had al `seg_idx`; nu één rij per stuk.

## 2. Jays telling

Getoetst met Jays fietstelling en de reconstructie ervan, 21 oktober. Die ZIP's
zijn niet in de repo gezet.

| | tot v3.21 | v3.21 |
|---|---|---|
| origineel: H de Lintweg | 1 lijn, 9 fietsen | stuk 0: 5, stuk 1: 4 |
| `_recon`: H de Lintweg | alleen stuk 0 (3 punten) | stuk 0: 5, stuk 1: 4 |
| `_recon`: tikken in een cluster | 5 van 9 | 9 van 9 |
| netwerk van de `_recon` | 1926 lijnen, alleen het eerste stuk per weg | 3994 stukken, geen gaten |

Origineel en `_recon` geven nu dezelfde sleutels en dezelfde aantallen per stuk.

## 3. Gevolgen om te weten

- **Bezettingsgraad op korte stukken.** Met twee of drie plekken op een stuk
  springt hij snel (0, 50, 100 %). Dat hoort bij de fijnere maat. De
  handleiding zegt het.
- **De kaart heeft meer lijnen.** De grijze achtergrond bestaat nu uit stukken.
  Met het netwerk van vóór v3.20 (1926 ways) waren dat er 3994; sinds v3.20 is
  het netwerk weer klein.
- **`_straten.csv`** wordt voor de kaart niet meer gebruikt. De correctietool
  schrijft hem nog steeds bij een export.

## 4. Later: per stuk in de apps zelf

Jay wil meer op stukken werken. De volgende stap is dat parkeertelling en
fietsparkeren `segment_index` zelf in `_telregels.csv` en `_netwerk.csv`
schrijven, zoals pocket. Dat is een **schemawijziging voor KNIME**, dus eerst
bespreken. Telrapport rekent het stuk nu zelf uit en hoeft dan niets te
veranderen.

## 5. Tests

**`stukkentest.py`** (nieuw, 21 tests, Chromium). Drie wegen: 200 m (5 stukken),
124 m (3) en 50 m (1).
- *A, origineel (fiets):*
  - alle stukken, elk 40 m;
  - de tikken op het juiste stuk;
  - gelopen-zonder-tikken uit het GPS-spoor;
  - alle tikken in een cluster;
  - kleur, streep en grijs.
- *B, `_recon`:*
  - alle stukken uit zijn netwerk;
  - zijn eigen indeling;
  - op een gedeeld stuk tellen origineel en `_recon` samen op;
  - `_bezocht.csv` wordt gevolgd.
- *C, auto:* bezet, vrij en bezettingsgraad per stuk; het totaal bezet.
- *D, correctietool:*
  - een tik naar een andere weg: stuk en aantallen opnieuw;
  - de export zonder `_seg` en zonder `segment_index`;
  - de zijwissel gebruikt de hele weg.

## 6. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telrapport.html` | blok *Stukken voor fiets en auto* (`splitWayIntoSegments`, `laadStukken`, `stukVanTik`, `tikSeg`, `heleWeg`, `gelopenStukken`, `telPerStuk`, `naCorrectie`); laadpad fiets/auto; clusters, dekking, polygoonrapport; correctietool (`findNearestWays`, zijwissel, `applyCorrection`) |
| `traffic_counter_help.html` | *Kaartvisualisatie per type*: per stuk; nieuw kopje *Per stuk (fiets en auto)* |
| `index.html` | versie v3.21 |
| `_archief/overpass_rig/stukkentest.py` | nieuw |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt (groep `splitWayIntoSegments` met telrapport) |

## 7. Validatie

```
valideer.py            ALLES OK — 3 verwachte bestanden gewijzigd (index, telrapport, handleiding);
                       gedeelde blokken OK (splitWayIntoSegments nu 3 bestanden, 8f33fc5b)
stukkentest.py         21/21 (nieuw)
functest_telrapport 16, reconpaar 22, zijkolom 20, coordinaten 29, taartbol 24, shiftsolo 27,
segmenttabel 23, kwaliteit 33, bbox 11, verzameling 26, legezip 16, tikpositie 9, weekknop 11
gpkgtest 80, laadtest 45, logicatest 30, statictest 24, opruimtest 139, robuusttest 87,
planlinktest 51, onderhoudtest 17, opslaantest 48, gebiedtest 51, hersteltest 133
functests              alle 20 groen
test_zipref.py         referentie sluit aan op de code
check_encoding.py      alles geldige UTF-8
```

`hersteltest.py` gaf in de volledige ronde één keer 132/133. Los daarna vier
keer 133/133. Die test opent telrapport niet, en de veld-apps zijn in deze
release niet gewijzigd. Het ging dus om timing onder belasting.
