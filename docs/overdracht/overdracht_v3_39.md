# Overdracht v3.39 — Passanten geijkt, met een bredere marge

Jay: "Ik zou het fijn vinden om de winkelstraat omrekening naar aantal passanten
te kalibreren." En daarna: "Waarom simuleren we het niet? Veel leuker!"

## 0. Het gesprek vooraf

1. **Wat er al lag.**
   - Op de backlog stond "de loopsnelheid ijken met een Static-telling op één
     punt".
   - Jay heeft nog geen Static-telling met voetgangers in een winkelstraat.
2. **Vijf echte tellingen van Jay** gaven de vingerafdruk van zijn manier van
   tellen:
   - één ronde van 4–9 minuten, elk stuk één keer;
   - een eigen tempo van ongeveer 1,4 m/s;
   - 18% van de looptijd in gaten tussen de bezoeken, met daarin 10% van de
     tikken (wezen);
   - de tikken in groepjes.

   Daaruit is een startpunt voor een aparte chat geschreven (in het project:
   `claude/startpunt_simulatie_passanten.md`).
3. **De simulatie.** Code in `_archief/passantensim/` op branch
   `claude/passantensim`. De uitslag staat in het project:
   `claude/simulatie_passanten_uitslag_v1.md`.
   - In een ideale wereld geeft het échte blok `PASSANTEN` precies de waarheid
     (F = 1,00).
   - Los van de trefkans F ≈ 1,07, vooral door de gps-gaten en de wezen.
   - De trefkans overheerst: F ≈ 1,06 / p̄. Jay tikt tegemoetkomers (ook aan de
     overkant) en stilstaanders, en mist naar eigen zeggen ongeveer 5%. Met 95%
     geeft de simulatie F ≈ 1,14.
   - In Jay's echte tellingen vallen minder tikken in gaten dan in de simulatie
     (10% wezen tegen 18%). Daarom voorlopig **F = 1,1**.
   - Groepjes maken de spreiding ongeveer twee keer die van Poisson (φ ≈ 2). De
     Garwood-marge dekte 86–91% in plaats van 95%; met × √2 ≈ 1,4 klopt hij
     weer.
4. **Een factor, geen nieuwe rekenkern.** Jay kalibreert op de huidige
   telmethode: er liggen al ongeveer 100 tellingen.

De opdracht voor deze release kwam uit de simulatiechat. Het laatste punt
onder "Wat níet verandert" was afgebroken ("Geen …"). Ik heb het gelezen als:
geen wijziging aan de ZIP's, het schema of de rekenkern.

## 1. Wat er veranderd is (alleen `passanten.html`)

- **Twee constanten**, naast `OPHOGEN` en `MIN_TEGEN`, met de uitleg in het
  commentaar erboven:
  - `IJKFACTOR = 1.1`: voorlopig, uit de simulatie (okt 2026), te vervangen
    door een Static-ijking;
  - `MARGE_BREED = 1.4`: overdispersie door groepjes, φ ≈ 2.
- **`schat(c, seg)`**: in alle drie de takken is `q` × `IJKFACTOR`. De takken
  zijn beide richtingen, × 2, en de verhouding uit de straat.
  - `f` (de ophoging van de richting) en `gemeten` blijven ongeijkt.
  - Er is een veld `ijk` bij gekomen.
  - Labels, kleuren, `MAXQ`, de volgorde van de labels en het weekoverzicht
    (cellen en *gem.*) lopen allemaal via `schat(...).q`, en gaan dus vanzelf
    mee. Nagekeken: nergens anders komt een getoonde passantenwaarde
    rechtstreeks uit `c.q`. Alleen de gemeten stromen in de details
    (`c.stromen[r].q`) blijven ruw, zoals bedoeld.
- **`marge(c, seg)`**: eerst Garwood × waarde per tik × f × `IJKFACTOR`. Dan
  verbreed rond de schatting s:
  - onder = max(0, s − 1,4 · (s − onder));
  - boven = s + 1,4 · (boven − s).
- **Uitleg:**
  - Legenda: onder de loopsnelheid "geijkt: × 1,1 (voorlopig, uit simulatie)".
  - Details (popup en weekoverzicht): "geijkt: de berekende waarde × 1,1
    (voorlopig, uit een simulatie); de gemeten stromen hierboven niet. De marge
    is ruimer dan bij puur toeval, omdat mensen in groepjes lopen."
  - De uitleg onder de kaart: één zin over de ijking.
- **Handleiding** (`traffic_counter_help.html#passanten`):
  - een rij *IJking*;
  - bij *Klik op een stuk* een zin over de bredere marge;
  - "de enige aanname" is weg bij de loopsnelheid.
- **`verantwoording.html`** legt de berekening van Passanten niet uit en is niet
  gewijzigd.

## 2. Wat niet verandert

- Het gedeelde blok `PASSANTEN` is byte-identiek, in `passanten.html` en in
  `winkelstraat_rekenrig.html` (md5-groep `passanten` in `valideer.py`).
- Het rekenrig krijgt geen factor: dat blijft de ruwe methode.
- `c.q` en de gemeten stromen zijn ongeijkt.
- De ZIP's, het schema, KNIME en de veld-apps.

## 3. Later: de echte ijking

Volgens de simulatie werkt dit het beste:
- Static tegelijk met 10–20 rondes;
- vergeleken met het gemiddelde van de hele ronde, niet per vak.

Dat geeft F binnen ongeveer ±10%. Daarna wordt `IJKFACTOR` vervangen.

Nog open uit de simulatie: in het echt vallen half zo veel tikken in gps-gaten
als in het model.

## 4. Tests

**`passantentest.py`** heeft nu 54 tests (was 46).
- De verwachte labels, kleuren, `MAXQ`, de weekwaarden en de details zijn
  × 1,1. De marge-test van de Kerkstraat rekent de nieuwe formule.
- **Nieuw deel K:**
  - `schat()` in alle drie de takken: q = gemeten × ophoging × 1,1, `ijk` = 1,1,
    en `f` en `gemeten` ongeijkt;
  - `c.q` volgt nog de formule, en het rekenrig kent geen `IJKFACTOR`;
  - de legenda heeft de regel onder de loopsnelheid;
  - de popup toont de stromen ruw, de waarde geijkt, en de zin;
  - de marge rekent precies Garwood × 1,1 en dan × 1,4 vanaf de schatting, en
    is aan beide kanten breder;
  - in elke cel is de ondergrens ≥ 0 en ligt de schatting binnen de marge;
  - de uitleg onder de kaart noemt de ijking.

**Bekeken:** de kaart met de legenda, en het weekoverzicht met de details op
390 px.

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `passanten.html` | `IJKFACTOR`, `MARGE_BREED`, `schat`, `marge`, legenda, details, uitleg |
| `traffic_counter_help.html` | rij *IJking*, zin over de marge |
| `index.html` | versie v3.39 |
| `_archief/overpass_rig/passantentest.py`, `valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 6. Validatie

```
valideer.py            ALLES OK — precies de 3 verwachte bestanden gewijzigd; gedeelde blokken OK (passanten: 2 bestanden)
passantentest.py       54/54 (deel K nieuw)
functest_passanten.js  19/19 (de rekenkern, ongewijzigd)
```
