# Overdracht v3.57 — Passanten: Laad dagkrommen

Jay vroeg of er een algemeen aanvaarde dagkromme voor winkelgebieden bestaat.
Die is er in Nederland niet openbaar: Locatus publiceert geen uurprofiel. Wel
zijn er buitenlandse open data (hystreet, Bonn, St. Gallen, Melbourne).

Daarna stuurde hij "7 dagkrommen ... van de belangrijkste winkelstraat. Je kunt
deze aanhouden als onderliggende dagkromme". De eerste versie had het uur
verkeerd en is weggegooid. Bij de goede: "het genoemde uur is het startpunt van
de meting, dat betekent dat 24 dus het eerste uur van de volgende dag is. Van de
dagen is 1 de maandag en 7 zondag."

Op de vraag of de kromme openbaar in de code mag: "Deze kromme mag niet
openbaar in de code. Maak er maar een functie van die "Laad Dagkrommen", met
een csv als input. De uren kloppen."

**De krommen van Jay staan nergens in de repo, ook niet in een test of in deze
overdracht.**

## 1. Inlezen

De knop **Laad dagkrommen** staat naast "of een map" (`#dagkrommen`).

- **De CSV:**
  - een kopregel;
  - dan per rij het uur en zeven kolommen, 1 = maandag … 7 = zondag;
  - het uur is het begin van de meting; 24 is 0:00–1:00 van de volgende dag,
    dus zondag 24 wordt maandag 0. Een uur 0 mag ook.
- **Scheiding:** `;`, tab of `,`, herkend aan de kopregel.
- **Getallen** (`krommenGetal`): `1.234,56`, `1234.56` en `2.345` (duizendtal)
  gaan alle drie goed. Een BOM mag.
- **Geweigerd, met de reden in de melding:**
  - minder dan 12 uren;
  - een uur buiten 0–24;
  - iets wat geen getal is;
  - een dag zonder passanten.
- **Bewaard** in `localStorage` (`telsuite.passanten.dagkrommen`): de naam en de
  7×24 getallen. Na herladen staan ze er nog.
- In de balk staat "Dagkrommen: naam.csv **wis**". Wis haalt ze weg, ook uit de
  browser.

## 2. Gebruik

Alleen de vorm telt; de absolute getallen horen bij die ene straat.

- **Weekoverzicht** (`krommenSchatter`, gekozen in `weekSchatter` als er
  krommen zijn):
  - het niveau van het stuk is Σ gemeten ÷ Σ kromme over de gemeten vakjes (niet
    te kort);
  - een niet gemeten uur tussen 9 en 21 is niveau × kromme[dag][uur], met ≈;
  - buiten 9–21 wordt niets geschat;
  - alle uren zijn te schatten, dus "≥" verdwijnt;
  - het sterretje volgt de gemeten vakjes (`sch.ster`);
  - de tooltip zegt "geschat met de dagkrommen (naam)" (`sch.bron`).
- **Dagcurve** (`krommenIndex`, `.dc-kromme`):
  - per dagtype dat er is een stippellijn in de kleur van dat dagtype; werkdag
    is het gemiddelde van maandag tot vrijdag;
  - index 100 = de kromme op dezelfde uren als `refK`, dus te vergelijken met
    de eigen curve;
  - de schaal neemt de kromme mee;
  - legenda rechts op de tweede regel als er plaats is, anders alleen in de
    uitleg.
- **Wanneer tellen?** rekent met de eigen dagcurve, zoals voorgesteld: dat gaat
  over wat de eigen tellingen weten.
- Zonder krommen werkt alles zoals in v3.56.

## 3. Tests

**`passantentest.py`: 114 (was 108).** Een nieuw deel aan het eind, op 390 px,
met een **zelfgemaakte** kromme: een driehoek rond 14 uur, per dag een andere
hoogte, Nederlandse getallen, en zondag 24 = 3.

- De CSV is goed gelezen, met maandag 0:00 = 3; naam in de balk; bewaard.
- Kapotte CSV's krijgen een reden; de getalvormen kloppen; tab mag.
- Het dagtotaal van zaterdag op de Voorstraat: het gemeten uur plus 11 × niveau
  × kromme, met ≈ en zonder ≥; de tooltip noemt de krommen.
- In de dagcurve de stippellijn, binnen 390 px, genoemd in de uitleg.
- Na herladen staan de krommen er nog; wis haalt ze weg.

## 4. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `passanten.html` | knop en status; inlezen, bewaren en wissen; `krommenSchatter`; `krommenIndex` en de stippellijn; de uitleg |
| `traffic_counter_help.html` | Laad dagkrommen, in de rij Klik op een stuk |
| `index.html` | versie v3.57 |
| `_archief/overpass_rig/passantentest.py` | zie §3 |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 5. Validatie

```
valideer.py           ALLES OK — de 3 verwachte bestanden
passantentest.py      114/114
volledige ronde lokaal: zie de PR
```
