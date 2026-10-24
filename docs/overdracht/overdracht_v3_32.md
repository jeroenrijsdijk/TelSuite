# Overdracht v3.32 — voortgang en een logboek per ronde in Ordenen

Jay, na v3.31: "Geeft de .csv die je maakt na ordenen even een datum+tijd in de
bstandsnaam. Voor tijdens het lezen en verplaatsen van .zips mag je een
voortgangsindicator maken."

Op de vraag van v3.31 over KNIME en submappen: "Zeker, maar dat gaat automatisch
goed in knime." Dat punt is dus dicht.

Aan de tellingen, de ZIP's en het schema verandert niets. Het logboek van
Ordenen hoort niet bij de KNIME-pijplijn; de kolommen blijven
`tijdstip;van;naar;reden;sha256`.

## 1. Een logboek per keer Uitvoeren

- **De naam:** `ordenen_logboek_<jjjjmmdd>_<uummss>.csv`, zoals in een
  sessie-id, met het moment waarop die ronde begon. Dat is hetzelfde moment
  als in de kolom `tijdstip`.
  - De naam maakt `ORDENEN.logboekNaam(datum, k)`, los te testen.
  - De tijd is de lokale tijd van de computer, net als de kolom.
- **Nooit overschrijven:** is de naam al bezet (twee rondes in dezelfde
  seconde), dan krijgt het nieuwe logboek `_2`, `_3`, enzovoort.
- **Aanvullen hoeft niet meer:** elke ronde schrijft een nieuw bestand, met de
  kop. Een `ordenen_logboek.csv` van v3.31 blijft gewoon staan.
- **De melding** na Uitvoeren noemt het logboek bij naam.
- **Opgelost:** lukte het schrijven van het logboek niet, dan verscheen er een
  melding die meteen door de eindmelding werd overschreven. Nu staat de reden
  in de eindmelding.

## 2. De voortgang

Een balk onderaan het venster (`position: fixed`), met een regel eronder.
Onderaan, omdat je bij Uitvoeren onder aan een lange tabel staat, en bij de
eerste keer lezen bovenaan de pagina: zo zie je hem allebei de keren. Dit wijkt
af van wat ik Jay vooraf schreef ("direct onder *Je archief*").

| stap | regel | balk |
|---|---|---|
| mappen doorzoeken | *Mappen doorzoeken: 57 ZIP's gevonden* · de map | zonder einde (het totaal is nog onbekend) |
| lezen | *Lezen: 37 van 120* · het bestand | 36 van 120 |
| verplaatsen | *Verplaatsen: 5 van 7* · het bestand | 4 van 7 |
| logboek | *Logboek schrijven* | vol |

- **Zolang hij bezig is** (`BEZIG`), staan *Kies je archiefmap*, *Opnieuw
  lezen*, *Uitvoeren*, *ook tonen wat al goed staat* en de vinkjes in de tabel
  uit. Zo start je niet per ongeluk een tweede ronde. Een uitgeschakelde
  *Opnieuw lezen* ziet er nu ook uit als uitgeschakeld (`button.ghost:disabled`).
- **Daarna** verdwijnen de balk en de tekst (`voortgang(null)`).
- **Alleen bekijken** (Firefox, Safari): dezelfde balk bij het lezen.
- **De oude regel** naast *Opnieuw lezen* is weg. Die stond in het plan, en dat
  is bij de eerste keer lezen nog verborgen.

## 3. Robuuster lezen

Nodig, omdat een balk die bij een fout blijft hangen erger is dan geen balk.

- **Eén bestand dat niet te openen is** (bijvoorbeeld omdat een ander
  programma het vasthoudt) stopt het lezen niet meer. Het staat in het plan
  bij *blijft liggen*, met de reden. `leesItem` krijgt daarvoor de belofte van
  `getFile()`.
- **Mislukt het doorzoeken van de map zelf**, dan komt er geen plan, maar een
  melding. Een half gelezen archief zou een verkeerd plan geven: een
  reconstructie die niet gelezen is, mist dan bij zijn origineel.

## 4. Elders bijgewerkt

- **`telarchief.html`:** de uitleg onder *Zo wordt ingedeeld* noemt
  `ordenen_logboek_<datum>_<tijd>.csv`, één per keer Uitvoeren.
- **Handleiding (`#ordenen`):**
  - een rij *Voortgang*;
  - de rij *Logboek* met de nieuwe naam.
- **`index.html`:** versie v3.32.

## 5. Tests

- **`functest_ordenen.js`** 35 (was 32): de naam van het logboek, met
  voorloopnullen en `_2`.
- **`ordenentest.py`** 58 (was 41). In het archief ligt nu ook een
  `ordenen_logboek.csv` van v3.31.
  - **F. Voortgang.** Elke aanroep van `voortgang()` wordt vastgelegd, met wat
    er daarna op het scherm staat.
    - Bij het lezen eerst *Mappen doorzoeken*, met een balk zonder einde, tot
      *11 ZIP's gevonden*. Dan *Lezen: k van 11* voor k = 1 tot en met 11, met
      het bestand en de balk op k−1.
    - Bij Uitvoeren *Verplaatsen: k van 6*, met precies de bestanden die gaan,
      daarna *Logboek schrijven*.
    - Ondertussen staan de knoppen en alle vinkjes uit. Daarna is de balk weg
      en kun je weer kiezen.
    - Bij *alleen bekijken* ook *Lezen: k van 11*.
  - **G. Het logboek.**
    - Er is één logboek, en de tijd in de naam is die van de kolom `tijdstip`.
    - De melding noemt het logboek.
    - Een tweede ronde geeft een tweede logboek. Daarvoor worden de namen van
      de komende seconden eerst bezet, dus het nieuwe logboek krijgt `_2`.
    - Het eerste logboek, de bezette bestanden en het oude
      `ordenen_logboek.csv` blijven byte voor byte gelijk.
- **Bekeken:** de balk tijdens het lezen en tijdens het verplaatsen, op 1300 en
  390 px breed. Het lezen is daarvoor halverwege stilgezet.

## 6. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telarchief.html` | voortgangsbalk, `BEZIG`, `ORDENEN.logboekNaam`, een logboek per ronde, robuuster lezen |
| `traffic_counter_help.html` | rijen *Voortgang* en *Logboek* |
| `index.html` | versie v3.32 |
| `_archief/overpass_rig/functest_ordenen.js`, `ordenentest.py` | uitgebreid |
| `valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 7. Validatie

```
valideer.py            ALLES OK — precies de 3 verwachte bestanden gewijzigd (index, telarchief, handleiding);
                       gedeelde blokken OK; titel 55, description 136; sitemap 16 adressen
functest_ordenen.js    35/35
ordenentest.py         58/58 (F: voortgang, G: logboek per ronde)
alle overige browsertests en de 21 functests groen; test_zipref en check_encoding OK
```
