# Overdracht v3.46 — de simulatie op telonline.org, ijkfactor 1,03

Jay, over de passantensimulatie: "Ik vind het moeilijk om er iets van te
vinden, zonder dat ik echt inzicht heb in de details. [...] Iets waardoor ik
vertrouwen krijg in de resultaten." Daaruit groeide de simkijker, op de branch
`claude/passantensim`. Daarna, over de handleiding, drie keuzes:

- de ijking met de nieuwe simulatie;
- p/m·u tegen passanten;
- en "Verwijzen naar 'simulatieronde.html' die ook op telonline.org/simulatieronde.html
  staat, om het systeem van winkelstraat telling naar passanten te begrijpen".

En over de factor: "Naar 1,03".

## 0. Het gesprek vooraf: de simkijker

De simkijker is in stappen gebouwd, telkens als artifact.

1. **Eén ronde als tijd-wegdiagram.** Horizontaal de straat, verticaal de tijd.
   - Elke voetganger is een lijn.
   - Elke ontmoeting met de teller is gezien of gemist, met de kans en de worp.
   - Elke tik gaat naar het vak waar hij telt.
   - Daarbij de bezoeken met de gedeelde gaatjes, en de waarheid als
     stippellijn midden in elk vak.
   - Een vakkentabel, met per vak de rekensom van Passanten naast de waarheid.
2. **Een schakelaar drukte:** weinig, gemengd of veel.
3. **1.000 rondes als spreidingsdiagram** (Jay: "doe eens een stuk of 1000
   simulaties, en maak een scatter plot van werkelijk vs geteld").
   - Per ronde en per vak.
   - Klik op een stip en die ronde gaat open.
4. **p/m·u zoals telrapport** (Jay: "passages per meter per uur [...] kun je die
   ook laten zien in de grafieken"):
   - n_tellingen ÷ lengte ÷ duur_sec;
   - in de tabel, de rekensom en de wolken, met een schakelaar.
5. **Drukte "een week"** (Jay: "een mix van druk en rustig - zeg maar
   50-3000 passanten. Met uiteraard de meeste aandacht voor de aantallen die op
   een normale week zich voordoen").
   - Lognormaal tussen 50 en 3.000, met mediaan 600. Dat is het meetkundig
     gemiddelde van zes echte winkelstraattellingen, die 316 tot 1.682 per uur
     gaven.
   - Spreiding 0,75 in ln.
   - De teller loopt niet langzamer dan 0,8 m/s. De vertraging in de drukte is
     voor 300–1.600 bedoeld en zou hem bij 3.000 op 0,4 m/s zetten.
   - Daarbij een tabel per drukteklasse.
6. **Het aantal rondes is in te stellen:** 200 tot 10.000.

**Wat eruit kwam** (10.000 rondes, een week, trefkans 95%):

| drukte (/u) | rondes | F | k voor p/m·u |
|---|---|---|---|
| 50–200 | 662 | 1,03 | 18 m |
| 200–500 | 3.378 | 1,02 | 24 m |
| 500–1.000 | 3.539 | 1,03 | 28 m |
| 1.000–2.000 | 2.054 | 1,03 | 34 m |
| 2.000–3.000 | 352 | 1,02 | 41 m |

- **F is over de hele week 1,03, en per klasse even groot.** Eén ijkfactor past
  bij rustige en drukke straten.
- **De omrekening van p/m·u hangt af van de drukte.** In de drukte loopt de teller
  langzamer; p/m·u deelt door de hele aanwezigheid, Passanten door het
  ontmoetingsvenster.
- **Per ronde** zit de telling na de ijking in 8 op de 10 gevallen tussen 0,7 en
  1,3 keer werkelijk.
  - Onder de 200 per uur zit 30% van de rondes binnen 20%, boven de 2.000 94%.
  - Eén vak van één ronde is veel ruwer.

## 1. `simulatieronde.html` (nieuw, op telonline.org)

- **Verhuisd** uit `_archief/passantensim/simkijker.html` met `git mv`. De
  branch `claude/passantensim` is in deze release gemerged:
  - `sim_kern.js`, `batch.js`, `kijkercheck.js` en de README staan nu in main,
    in `_archief/` (export-ignore);
  - alleen de pagina gaat online.
- **Een gewone pagina van de suite:**
  - doctype en `lang="nl"`;
  - titel "Simulatie van een winkelstraattelling | telonline.org";
  - een description van 151 tekens en een canonical;
  - `fonts/fonts.css` in plaats van Google Fonts: geen verzoek naar buiten;
  - in de sitemap.
- **Voor wie hem zonder voorkennis opent:**
  - bovenaan links naar Passanten, de handleiding en telonline.org;
  - een stuk *Waarom deze simulatie* met de aannames (straten, voetgangers,
    groepjes, de teller, de trefkans, de gps);
  - geen "Jay" meer in de zichtbare tekst. Wel nog in de commentaren, zoals
    overal.
- **Standaard:** drukte "een week" en zaadje 68, een gewone ronde (653 per uur,
  F 0,99).
- **De ijkfactor** staat als `IJK = 1.03` in de pagina. De rekensom toont
  "met de ijking van nu (× 1,03)".
- **Draagt kopieën** van `_archief/passantensim/sim_kern.js` en van het blok
  `PASSANTEN`.
  - `kijkercheck.js --bijwerken` vervangt ze.
  - `functest_simulatieronde.js` controleert ze in de tests.
- **`sim_kern.js`** kreeg in deze reeks:
  - `run()` geeft ook de voetgangers, alle ontmoetingen (met kans en worp) en
    de gps-punten terug;
  - `qMediaan`, `qSpreiding` en `tempoMin`, standaard uit.

  Zonder die drie geven dezelfde zaadjes dezelfde rondes als voorheen;
  180 rondes vergeleken.

## 2. Passanten

- **`IJKFACTOR` = 1,03** (was 1,05), met het commentaar erbij.
- **Legenda en details:** "geijkt: × 1,03 (voorlopig, uit simulatie)". Het woord
  *simulatie* linkt naar `simulatieronde.html`; in de details in een nieuw
  tabblad.
- **De uitleg onder de kaart:** "× 1,03 geijkt: een simulatie liet zien dat de
  telling zo'n 3% te laag uitkomt [...], bij rustige en drukke straten even
  veel".

## 3. Handleiding

- **Passanten, rij *IJking*:**
  - 1,03 sinds v3.46;
  - wat de simulatie is, met de week aan drukte en 1,02–1,03 per klasse;
  - de aanname van 95%;
  - Static als latere ijking;
  - de link naar `simulatieronde.html`.
- **Passanten, rij *Hoe nauwkeurig* (nieuw):**
  - een ronde zit in 8 op de 10 gevallen tussen 0,7 en 1,3 keer werkelijk;
  - onder de 200 per uur 3 op de 10 binnen 20%, boven de 2.000 ruim 9 op de 10;
  - een los stuk is ruwer.
- **Passanten, rij *p/m·u en passanten* (nieuw):**
  - geen vaste veelvoud: ongeveer × 30, van 18 tot 41;
  - waarom (tempo, venster, stilstaanders).
- **Telrapport:** een alinea *p/m·u en passanten per uur (v3.46)* na *Te kort
  gemeten*.
- **ZIP delen:** de regel onder de bewaarknop staat in de teltools en de
  reconstructie, niet meer in telrapport. Jay haalde hem daar op 4 november weg
  ("Remove warning about sharing GeoPackage"). Dat de verzameling en de
  GeoPackage je huis kunnen tonen, staat er nog wel.
- **ZIP-referentie:** in de noot bij `dagcurve.csv` staat × 1.03.

## 4. Tests

- **`functest_simulatieronde.js`** (nieuw, 12):
  - de kopieën van `sim_kern.js` en `PASSANTEN` zijn gelijk aan het
    origineel;
  - `IJK` van de pagina = `IJKFACTOR` van Passanten = 1,03;
  - geen Google Fonts; doctype, `lang` en canonical;
  - de handleiding en Passanten verwijzen ernaar, en hij staat in de sitemap;
  - de kopieën uit de pagina draaien 300 rondes van een week: drukte 50–3.000
    met mediaan rond 600, teller niet onder 0,8 m/s, F rond de ijkfactor;
  - herhaalbaar.
- **`passantentest.py`** (93): `IJK` 1,03. De teksten "geijkt: × 1,03 (voorlopig,
  uit simulatie)" blijven gelijk, met de link erin.
- **`deeltest.py`** (25): deel C eiste nog de regel in telrapport, die Jay had
  weggehaald. Nu eist het dat hij daar weg is; de reconstructie houdt hem.

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `simulatieronde.html` | nieuw (uit `_archief/passantensim/simkijker.html`) |
| `passanten.html` | `IJKFACTOR` 1,03; links naar de simulatie; uitleg |
| `traffic_counter_help.html` | *IJking*, *Hoe nauwkeurig*, *p/m·u en passanten*; telrapport: p/m·u en passanten per uur |
| `zip_format_reference.html` | × 1.03 |
| `index.html` | versie v3.46 |
| `sitemap.xml` | `simulatieronde.html` |
| `_archief/passantensim/` | in main (README, `kijkercheck.js` naar de nieuwe plek) |
| `_archief/overpass_rig/functest_simulatieronde.js` | nieuw |
| `_archief/overpass_rig/passantentest.py`, `deeltest.py`, `valideer.py`, `README.md`, `docs/ONTWIKKELEN.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 6. Validatie

```
valideer.py                  ALLES OK — de 5 verwachte bestanden (1 nieuw)
functest_simulatieronde.js   12/12
passantentest.py             93/93
volledige ronde lokaal: zie de PR
```
