# Overdracht v3.44 — Passanten: stukken kiezen voor de dagcurve

Jay: "Als ik de tellingen in passanten heb geladen, wil ik linkjes kunnen
selecteren om daarvan dagcurves te zien".

## 0. Het gesprek vooraf

1. **Kiezen.** Voorgesteld: per klik, met een knop of Ctrl+klik, en *hele
   straat*. Een lasso vraagt een extra bibliotheek en kan later, als klikken te
   traag blijkt. Jay: "kiezen per klik plus hele straat is goed".
2. **Rekenen.** Hetzelfde model als v3.43, alleen op de passages van de
   gekozen stukken. De curve van de keuze staat over die van alle stukken, elk
   met index 100 op het eigen werkdaggemiddelde. Zo vergelijk je het verloop,
   niet hoe druk de straat is.
3. **Bij weinig gegevens** waren er twee slimmere varianten:
   - algemene vorm × een eigen factor per dagtype;
   - de curve van de keuze naar de algemene trekken ("krimpen").

   Gekozen is de eigen curve, met streepjes waar het dun is. De eerste
   variant kan erbij als selecties vaak te dun blijken. De tweede is nu te
   complex voor wat hij oplevert.
4. **Absolute passanten per uur** voor een keuze ("een gemiddeld werkdaguur is
   hier 640"). Daarvoor moet de ophoging van één gelopen richting in het model.
   Jay: "punt 2 komt misschien later". Het staat in de backlog.

## 1. Kiezen op de kaart

- **De rij *Kies*** onder dag en uur bevat:
  - de knop **Kies stukken** (`KIES`);
  - wat er gekozen is: "8 stukken: Hoofdstraat (8)";
  - de knoppen *hele …*, *dagcurve* (naar het tabblad) en *wis*.
- **`klikStuk(seg, e)`:**
  - met de knop aan, of met Ctrl- of Cmd+klik, zet een klik het stuk aan of uit
    (`wisselKeuze`);
  - anders opent hij het weekoverzicht, zoals altijd.
- **Op de kaart:** een gekozen stuk krijgt een blauwe rand eronder
  (`KEUZE_KLEUR` `#2b59c3`, klasse `gekozen`). Dat werkt ook voor grijze en te
  kort gemeten stukken. De legenda noemt het zolang er iets gekozen is.
- **Hele straat** (`heleStraat(start, segmenten)`):
  - kiest de stukken met dezelfde naam (zonder hoofdletters) die er via elkaar
    aan vast liggen;
  - aan vast liggen betekent: een eindpunt binnen `STRAAT_GAT` = 60 m van een
    eindpunt van een stuk dat er al bij hoort;
  - dat overbrugt één ongelopen stuk van 30–45 m;
  - een Hoofdstraat in een ander dorp blijft erbuiten;
  - een stuk zonder naam is alleen zichzelf;
  - de knop verschijnt na een klik, als er nog stukken van die straat bij
    kunnen: "hele Voorstraat (+8)".
- **`herbereken()`** (nieuwe bestanden) houdt de keuze, behalve stukken die er
  niet meer zijn.

## 2. De dagcurve van de keuze

- **`dagcurveVan(filter)`:** de rekening van v3.43 voor de stukken in `filter`,
  of voor alle stukken (`null`).
  - `dagcurve()` is die voor alle stukken.
  - `dagcurveKeuze()` is die voor `KEUZE`, één keer per keuze berekend
    (`DCKEUZE`, sleutel = de gekozen stukken).
  - Het model, de schaal, de drempels en de trekkingen zijn die van v3.43, op
    alleen die passages.
- **Bovenaan het tabblad** staat "Je keuze, 2 stukken: Voorstraat (2)", met
  *wis keuze*. Zonder keuze staat er hoe je kiest.
- **Grafiek:** de keuze zoals altijd (lijn, band, punten). Alle stukken staan er
  dun gestippeld achter, in dezelfde kleur per dagtype. Een tweede
  legendaregel: *je keuze* en *alle stukken*.
- **Tabellen:**
  - per uur twee kolommen per dagtype, *keuze* (met marge) en *alle*;
  - de weekdagfactoren met een kolom *alle*;
  - *Waar gemeten is* gaat over de keuze.
- **Downloads:** naast `dagcurve.csv` en `passages.csv` ook `dagcurve_keuze.csv`
  en `passages_keuze.csv`. Die hebben dezelfde kolommen, voor de keuze; aan het
  schema verandert niets. Ze staan in de ZIP-referentie.

Aan de rekenkern `PASSANTEN`, het rekenrig en de kaartwaarden verandert niets.

## 3. Bekeken

- **Jay's zes tellingen:**
  - de Hoofdstraat (twf) aangeklikt met de knop;
  - *hele Hoofdstraat (+7)* gaf 8 stukken met een blauwe rand;
  - het weekoverzicht bleef dicht.
- **Gemaakte tellingen** (101; tien straten met een later verloop gekozen): de
  curve van de keuze piekt zichtbaar later dan de gestippelde van alle stukken.
- **Op 390 px:**
  - de rij *Kies* past;
  - de tabel met de extra kolommen schuift in zijn kader.

## 4. Tests

- **`functest_dagcurve.js`** (39, was 27):
  - Twee groepen straten met een eigen verloop. De keuze van groep X geeft
    precies X terug (piek om 12 uur), met zijn eigen aantallen en
    weekdagfactoren. Alle stukken samen liggen daartussenin.
  - `dagcurveKeuze()`: niets zonder keuze, één keer gerekend, opnieuw bij een
    andere keuze.
  - De keuze-CSV's: alleen de gekozen stukken, dezelfde kolommen.
  - `heleStraat`:
    - beide kanten op, ook over een gat van 40 m, ook met een kleine letter;
    - niet 100 m verder, niet in een ander dorp, niet een andere straat;
    - zonder naam: alleen het stuk zelf.
- **`passantentest.py`** (93, was 76), deel DC *Kiezen*, met echte muisklikken
  op de kaart:
  - de knop, een klik (gekozen, weekoverzicht dicht, blauwe rand, legenda);
  - *hele Voorstraat (+8)*: 1001, 1004 en 1005, ook de andersom getekende, en
    niet de Kerkstraat;
  - nog eens klikken, *wis*, Ctrl+klik zonder knop;
  - een gewone klik opent nog steeds het weekoverzicht;
  - `herbereken()` houdt de keuze;
  - de dagcurve van de keuze (1001/0 en 1001/1): werkdag 11 los nagerekend in
    Python op alleen die passages, met een andere uitkomst dan alle stukken;
  - de tabel, beide downloads en *wis keuze*;
  - op 390 px de rij en de dagcurve met keuze.

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `passanten.html` | rij *Kies*; blok *Kiezen* (`klikStuk`, `wisselKeuze`, `heleStraat`, `tekenKeuzeRij`); blauwe rand en legenda; `dagcurveVan(filter)`, `dagcurveKeuze`; grafiek met alle stukken erachter; tabellen; keuze-CSV's; CSS |
| `traffic_counter_help.html` | Passanten: rij *Stukken kiezen*, *Klik op een stuk* |
| `zip_format_reference.html` | Passanten exports: `dagcurve_keuze.csv`, `passages_keuze.csv` |
| `index.html` | versie v3.44 |
| `_archief/overpass_rig/functest_dagcurve.js`, `passantentest.py`, `valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 6. Validatie

```
valideer.py            ALLES OK — precies de 4 verwachte bestanden gewijzigd
functest_dagcurve.js   39/39
passantentest.py       93/93
volledige ronde lokaal: zie de PR
```
