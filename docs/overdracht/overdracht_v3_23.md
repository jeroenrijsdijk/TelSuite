# Overdracht v3.23 — Static middelt de GPS

Jay, na v3.22: "Die 20m ondergrens gps preciesie zou ik nog wel wat fijner
willen, maar als je echt geen goede gps heb, wil je toch graag een keer gaan
tellen. De wachttijd mag niet te lang oplopen."

Static wacht nooit op de GPS: je telt vanaf Start, en de plek wordt ondertussen
bepaald. Daarom kan de plek preciezer worden zonder dat iemand langer wacht.
Het voorstel was blijven luisteren en middelen. Jay: "grenzen van 8m en 15m. 3
minuten luisteren is prima".

Het ZIP-schema verandert niet. Alleen Static, de handleiding en de referentie.

## 1. Hoe het was

- **Kiezen.** Binnen hooguit 30 s nam de app de beste losse positie en stopte
  hij met luisteren.
- **Betrouwbaar.** Een positie tot 20 m heette betrouwbaar. In het overzicht in
  de ZIP stond "< 25m" (gevonden bij v3.22).
- **Adres.** Eén keer opgezocht, bij het vastzetten.

## 2. Hoe het nu is

**Luisteren.** Hooguit 3 minuten (`GPS_LUISTER_MS`). De app stopt eerder:
- bij Stop;
- als de schatting na minstens 30 s ±4 m of beter is (`GPS_DOEL_M`).

Het scherm staat toch al aan, dus de extra batterij valt weg tegen het scherm.

**De schatter** (`gpsSchatting(metingen, nu)`) is een pure functie, zodat hij
los te testen is.
1. **Venster.** Alleen metingen van de laatste 2 minuten
   (`GPS_VENSTER_MS`). Wie na Start nog naar zijn plek loopt, raakt die eerste
   metingen kwijt.
2. **Uitschieters.** Er vallen metingen af die ver van de mediaan liggen.
   - *Ver* is verder dan 2× hun eigen opgegeven afwijking, én verder dan 2,5× de
     mediane afstand tot de mediaan, met een minimum van 8 m.
   - Dat tweede criterium kwam erbij tijdens het bouwen. In de stad is een GPS
     vaak te gunstig over zichzelf. Met alleen de opgegeven afwijking sneed het
     filter dan de echte spreiding weg, en leek de plek nauwkeuriger dan hij
     was. De test toont het aan: ±3 m opgegeven, ±9 m echt.
3. **Gemiddelde.** Gewogen, met gewicht 1/afwijking².
4. **Afwijking van het gemiddelde.** Typisch = de grootste van twee: de mediaan
   van de opgegeven afwijkingen, of de gewogen spreiding rond het gemiddelde.
   - GPS-fouten hangen ongeveer een halve minuut samen. Daarom geldt één
     onafhankelijke meting per 30 s (`GPS_SAMENHANG_S`).
   - De afwijking is typisch / √(halve minuten), met een ondergrens van 3 m
     (`GPS_ONDERGRENS_M`).
   - Een vaste fout, zoals weerkaatsing tussen hoge gebouwen, middel je niet
     weg. Daarom die ondergrens.

**Drie niveaus** (`gpsNiveau`):
- nauwkeurig: tot 8 m;
- redelijk: tot 15 m;
- grof: meer dan 15 m.

Ze staan in een nieuwe regel *GPS* onder *Plek*, in groen, oranje of rood.
Tijdens het luisteren staat erachter "wordt beter, nog 1:40". "GPS reliable"
in het overzicht is Yes bij 15 m of beter; de tekst noemt nu de echte grens
(`Yes (<= 15m)` / `No (> 15m, best available)`). Telrapport kijkt alleen of
er Yes staat.

**Adres** (`adresBijwerken`).
- Opgezocht zodra de plek redelijk is, of na 30 s hoe dan ook.
- Opnieuw als de schatting meer dan 15 m verschuift.
- Steeds één verzoek tegelijk.
- Na een mislukt verzoek (geen bereik) volgt 30 s pauze en dan één nieuwe
  poging, ook als de app al klaar is met luisteren. Anders zou de app
  Nominatim bij elke meting opnieuw proberen.
- De straat staat nu op z'n Nederlands: *Voorstraat 12* (was *12 Voorstraat*).
  Dat zie je ook in `straat` in de export.

**Doortellen.** Was de app nog niet klaar met luisteren, dan luistert hij
verder. De schatting van voor de onderbreking telt dan mee als eerste meting.

**Geen toestemming voor GPS.** De app stopt met luisteren; tellen gaat gewoon.
Bij een andere fout blijft hij proberen tot de 3 minuten om zijn.

## 3. Gevolgen om te weten

- **Wat de export bevat.** Positie en `nauwkeurigheid` in de export zijn het
  gemiddelde en zijn geschatte afwijking, niet meer één meting. *GPS recorded
  at* in het overzicht is de tijd van de laatste meting die meetelde.
- **Stoppen binnen 3 minuten.** Stop je eerder, dan gaat de schatting van dat
  moment mee.
- **Wat een veldtest moet uitwijzen.** Op een echte telefoon geeft de GPS
  ongeveer elke seconde een meting, ook als je stilstaat. Komt er een tijd
  geen meting, dan blijft de schatting gewoon staan. Haalt de plek op een
  goede plek binnen een minuut *nauwkeurig*? Zet het in de veldtest.

## 4. Tests

**`gpsmiddeltest.py`** (nieuw, 39 tests, Chromium, met de nep-klok van
Playwright):
- *A, de schatter los, met vaste ruis:*
  - 2 minuten ±6 m gemiddeld tot binnen 3 m;
  - een uitschieter van 72 m telt niet;
  - 40 m lopen na Start, en toch op de plek;
  - twee metingen 1 s na elkaar zijn niet beter dan één;
  - nooit beter dan 3 m;
  - een te gunstige GPS;
  - het venster;
  - de niveaus.
- *B, de app:*
  - tellen vanaf Start, zonder positie;
  - de plek wordt beter en telt af;
  - na 3 minuten klaar;
  - het gemiddelde ligt binnen zijn eigen opgegeven afwijking;
  - één adresverzoek;
  - het gemiddelde in de ZIP, met de grens van 15 m.
- *C:* een goede GPS is binnen 2 minuten klaar.
- *D:* een slechte GPS: grof, de telling loopt gewoon, "No (> 15m".
- *E:* Stop binnen de 3 minuten.
- *F:* het adres: wanneer, opnieuw na 15 m verschuiving, en de pauze na een
  mislukt verzoek.
- *G:* geen toestemming voor GPS.

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `traffic_counter.html` | GPS: luisteren en middelen (`gpsSchatting`, `gpsNiveau`, `requestGPS`, `gpsBijwerken`, `gpsKlaar`, `adresBijwerken`); regel *GPS* in het sessiepaneel; grens 15 m in het overzicht; straat als *Voorstraat 12* |
| `traffic_counter_help.html` | *GPS en plek* herschreven; intro en veldtip |
| `zip_format_reference.html` | de positie van Static is een gemiddelde; voorbeeld `Yes (<= 15m)` |
| `index.html` | versie v3.23 |
| `_archief/overpass_rig/gpsmiddeltest.py` | nieuw |
| `valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 6. Validatie

```
valideer.py            ALLES OK — 4 verwachte bestanden gewijzigd (index, Static, handleiding, referentie);
                       gedeelde blokken en constanten ongewijzigd OK
gpsmiddeltest.py       39/39 (nieuw)
herstelmeldingtest 103, hersteltest 133, statictest 24, opruimtest 139, laadtest 45, robuusttest 87,
logicatest 30, planlinktest 51, onderhoudtest 17, opslaantest 48, gebiedtest 51, stukkentest 21, gpkgtest 80
functests              alle 20 groen
test_zipref.py         referentie sluit aan op de code
check_encoding.py      alles geldige UTF-8
```
