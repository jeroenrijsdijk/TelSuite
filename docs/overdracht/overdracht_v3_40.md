# Overdracht v3.40 — Passanten: tikken tussen twee stukken tellen mee

Jay, bij het rekenvoorbeeld: "Kunnen deze tikken niet gewoon meetellen?" Na het
voorstel: "ga".

## 0. Het gesprek vooraf

1. **Het probleem.** `_bezocht.csv` komt uit de GPS-punten, en de GPS meet om
   de paar seconden. Tussen het laatste punt in het ene stuk en het eerste in
   het volgende zit daardoor een gaatje: in Jay's tellingen meestal 4 s, en 9
   op de 10 hooguit 9 s.
   - Passanten liet die tijd tot v3.40 weg, en ook de tikken die erin vielen.
   - In Jay's zes tellingen waren dat 51 van de 494 tikken.
   - In de telling van 26 oktober (het rekenvoorbeeld) waren het er 6 van 31.
2. **Het voorstel.**
   - Elk gaatje in het midden delen: de eerste helft bij de passage ervoor, de
     tweede bij die erna.
   - Tijd en tikken gaan samen mee.
   - Een tik telt bij de passage waarin hij op tijd valt. Niet het stuk dat de
     reconstructie erbij zette, want dan gaan tijd en tikken elk een eigen kant
     op.
3. **De ijkfactor moet mee.** De 1,1 van v3.39 compenseerde voor een deel juist
   deze tikken. Daarom heb ik de simulatie opnieuw gedraaid met de nieuwe kern
   (§2).
4. **Hooguit 5 s per kant**, niet de 10 s uit het voorstel.
   - De simulatie maakt geen lange gaten, dus daar maakt het niets uit.
   - In Jay's tellingen wel. Een lang gat (12–25 s, vijf keer in zes tellingen)
     is meestal een kort stukje zonder eigen passage. In de telling van 26
     oktober is dat een stukje van 15 m in een gat van 25 s.
   - Met 10 s per kant zou het grootste deel van zo'n gat naar de buren gaan.
     Met 5 s gaan de normale gaatjes (tot 10 s) helemaal mee, en van een lang
     gat blijft het midden leeg.

## 1. Wat er veranderd is

**In de rekenkern `PASSANTEN`.** Byte-identiek in `passanten.html` en
`winkelstraat_rekenrig.html`, dus het rekenrig rekent nu ook zo. Het commentaar
bovenin het blok legt het uit.
- `GAT_MAX = 5` (s), ook geëxporteerd.
- **`sessie()`:**
  - de passages op tijd gezet;
  - per passage een venster `van`–`tot`: het midden van het gaatje ervoor en
    erna, hooguit `GAT_MAX` van de GPS-tijd af;
  - `t` = `duur_sec` + wat er aan beide kanten bij kwam;
  - elke tik (tegemoet of stilstaand) telt bij de eerste passage waarvan het
    venster hem bevat, op tijd. Een tik precies op de grens hoort bij de
    eerste.
- `t0` en `t1` blijven de GPS-tijden. Ze worden nog steeds gebruikt voor de
  richting (GPS-punten binnen de passage) en het uur (het midden).
- Een wees is nu een tik vóór de eerste passage, na de laatste, of midden in
  een lang gat.

**In `passanten.html`, buiten de kern:**
- `IJKFACTOR = 1.05` (was 1.1), met het commentaar bijgewerkt.
- De legenda en de details tonen de factor met twee decimalen ("× 1,05").
- De uitleg onder de kaart: tikken tussen twee stukken tellen mee, elk gaatje
  wordt in het midden gedeeld; geijkt × 1,05, omdat je af en toe iemand mist.

**Handleiding** (`traffic_counter_help.html#passanten`):
- een nieuwe rij *Tussen twee stukken*;
- *IJking* gaat naar 1,05, met de reden;
- *Wat meedoet* zegt welke tikken nog buiten vallen.

Aan de ZIP's, het schema en het veldwerk verandert niets. Elke telling wordt bij
het inlezen opnieuw gerekend.

## 2. De simulatie opnieuw

Dezelfde simulatie als bij v3.39 (`_archief/passantensim/` op branch
`claude/passantensim`), met het blok `PASSANTEN` uit deze versie van
`passanten.html`. Het waren 3000 rondes per regel, met de kolommen en
scenario's van `batch.js`.

| scenario | p̄ | F v3.39 | F v3.40 | dispersie φ | marge × 1,4 dekt | wezen v3.39 → v3.40 |
|---|---|---|---|---|---|---|
| alles gezien (systematisch) | 100% | 1,07 | 0,98 | 2,2 | 96% | 18% → 2% |
| Jay: 95% voor alles | 93% | 1,15 | **1,05** | 2,1 | 97% | 18% → 2% |
| 95% voor alles, zicht 4000 | 73% | 1,46 | 1,33 | 2,0 | 98% | 18% → 2% |
| standaard (95% / 75% overkant / 85% groep / zicht 4000) | 63% | 1,69 | 1,55 | 1,9 | 98% | 18% → 2% |

- Met `GAT_MAX` = 0 geeft de nieuwe kern precies de oude uitkomsten (F 1,07 en
  1,15). Dat bevestigt dat de verandering alleen in de gaatjes zit.
- `GAT_MAX` 5, 10 of onbeperkt maakt in de simulatie niets uit.
- De spreiding per vak (sd ln) gaat van 0,67 naar 0,65.
- Het systematische deel is nu bijna weg (0,98), en wat overblijft is de
  trefkans: F ≈ 0,98 / 0,93 = 1,05.
- Bij v3.39 werd 1,14 naar 1,1 afgerond, omdat er in het echt minder wezen
  waren dan in de simulatie. Dat verschil doet er nu nauwelijks meer toe.
- `MARGE_BREED` blijft 1,4: φ ≈ 2,1, en met × 1,4 dekt de marge 97%.

## 3. Wat het doet met Jay's tellingen

| telling | tikken | wezen v3.39 → v3.40 | ruw (zonder ijking) | getoond (met ijking) |
|---|---|---|---|---|
| 25 aug | 95 | 8 → 0 | +6,5% | +1,7% |
| 22 sep | 142 | 15 → 0 | +3,1% | −1,6% |
| 5 okt | 73 | 9 → 0 | +7,0% | +2,1% |
| 10 okt | 65 | 2 → 0 | −1,8% | −6,3% |
| 17 okt | 88 | 11 → 0 | +7,0% | +2,1% |
| 26 okt | 31 | 6 → 1 | +3,0% | −1,7% |

*Ruw* is de hele ronde samen (Σm / Σvenster), de *getoonde* waarde is dat
× 1,05/1,1.

- Gemiddeld blijft het getoonde getal vrijwel gelijk. Per stuk verschuift het
  wel, en dan meer naar wat er echt gebeurde.
- In de telling van 26 oktober gaat het voorbeeldstuk van 499\* naar 426\*.
  - De 4 tegemoet blijven: 12:25:02 gaat nu naar het stuk ervoor, 12:25:04
    (stilstaand) naar dit stuk.
  - t wordt 37,5 s in plaats van 30 s: 2,5 s ervoor en 5 s erna, van een gat
    van 25 s.

## 4. Tests

- **`functest_passanten.js`** heeft nu 26 tests (was 19).
  - Heen en terug: de passages zijn een halve seconde per buur langer, want
    tussen de passages zit steeds 1 s.
  - Nieuw deel *gaatjes*:
    - `GAT_MAX` = 5;
    - een gaatje van 4 s: elke kant 2 s, en de GPS-tijden blijven;
    - de tikken in het gaatje tellen op tijd, ook als de reconstructie ze bij
      het buurstuk zette;
    - een tik op de grens hoort bij de eerste passage;
    - een gat van 30 s: 5 s per kant, en een tik in het midden is een wees;
    - het zit in de formule;
    - het uur volgt de GPS-tijden.
- **`passantentest.py`** heeft nu 55 tests (was 54).
  - `verwacht()` rekent de gaatjes zelf uit. `IJK` = 1,05, en de teksten
    gebruiken `IJK_TEKST`.
  - Nieuw: in een sessie zijn de eerste en de laatste passage een halve seconde
    langer, de rest een hele.
  - De uitleg onder de kaart noemt de gaatjes.
- **`valideer.py`**: de groep `passanten` (2 bestanden) heeft een nieuwe md5, en
  is gelijk in beide.

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `passanten.html` | blok `PASSANTEN` (gaatjes, `GAT_MAX`); `IJKFACTOR` 1,05, twee decimalen, uitleg |
| `winkelstraat_rekenrig.html` | blok `PASSANTEN`, byte-identiek |
| `traffic_counter_help.html` | rij *Tussen twee stukken*, *IJking*, *Wat meedoet* |
| `index.html` | versie v3.40 |
| `_archief/overpass_rig/functest_passanten.js`, `passantentest.py`, `valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

Het rekenvoorbeeld in het project (`claude/passanten_rekenvoorbeeld.md`) is
bijgewerkt naar v3.40.

## 6. Validatie

```
valideer.py            ALLES OK — precies de 4 verwachte bestanden gewijzigd; gedeelde blokken OK (passanten: 2 bestanden)
functest_passanten.js  26/26 (deel gaatjes nieuw)
passantentest.py       55/55
simulatie              3000 rondes per scenario, zie §2
```
