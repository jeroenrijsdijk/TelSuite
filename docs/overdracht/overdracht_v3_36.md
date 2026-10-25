# Overdracht v3.36 — één looprichting × 2 in Passanten

Jay: "De linkjes die maar in 1 richting gelopen zijn - doe je die
passantentelling x 2 om op te hogen naar een 2-richtingen waarde?"

## 0. Het gesprek vooraf

1. **Tot nu toe** (v3.34) verdubbelde Passanten niet. Een stuk dat maar één kant
   op gelopen was, toonde de ene gemeten stroom met een sterretje. Dat was mijn
   voorstel, zodat er nooit een getal op de kaart staat dat niet gemeten is.
2. **Het nadeel:** op de kaart lijkt zo'n stuk ongeveer half zo druk als zijn
   buren. Wie op de kleur afgaat, ziet een rustige straat die het niet is.
3. **Mijn voorstel:** wel × 2, maar zichtbaar.
   - Het sterretje blijft.
   - In de details staat wat gemeten is.
   - De marge gaat mee.
   - Bij *gem.* alleen ophogen als in het geheel maar één richting voorkomt.
   - Slimmer ophogen, met de verhouding die elders in dezelfde straat gemeten
     is, heb ik genoemd maar niet gebouwd.
4. **Jay:** "ja".

Aan de rekenkern (het gedeelde blok `passanten`), het rekenrig, de ZIP's en
het schema verandert niets. Het ophogen gebeurt in `passanten.html`, bij het
tonen.

## 1. De regel: `schat(c)`

- **Precies één gemeten stroom** (A, B of een onbekende richting) en dus niet
  compleet: q × 2. De aanname is dat er in dat uur evenveel mensen de andere
  kant op lopen.
- **Beide richtingen:** de som van de twee stromen, zoals altijd.
- **Twee stromen waarvan één een onbekende richting heeft** (A plus ?): dan
  het gemeten totaal, niet opgehoogd, wel met een sterretje. De onbekende
  passage kan de andere richting zijn geweest. Ophogen zou dan dubbel tellen.
- `c` kan een cel zijn of de uitkomst van `samen()`. Die geeft nu ook
  `nStromen`, zodat *gem.* dezelfde regel volgt.

## 2. Waar het geldt

- **Kaart:** de kleur van een stuk, de labels (*356\**), welk label voorgaat
  bij overlap, en het maximum van de kleurschaal.
- **Weekoverzicht:** de cellen en *gem.*
- **Details:** bij één richting staat er nu:

  > "\* maar één looprichting gemeten: 178 per uur, de stroom die je tegemoet
  > kwam. Aangenomen dat er evenveel mensen de andere kant op lopen: × 2."

  Bij een deels onbekende richting staat er dat het het gemeten totaal is,
  niet opgehoogd.
- **Marge:** × 2 als de waarde × 2 is. De onzekerheid van de aanname zelf zit
  er niet in.
- **Teksten:**
  - de legenda zegt "\* niet in beide richtingen gemeten; één richting: × 2";
  - het weekoverzicht en de uitleg onder de kaart zeggen hetzelfde;
  - in de handleiding staat in de rij *Richting* ook een waarschuwing: bij een
    station of een parkeergarage aan één kant kan de verdeling scheef zijn,
    loop daar heen en terug.

## 3. Tests

**`passantentest.py`** 40 (was 35):
- De testgegevens hebben er een passage bij: in de tweede zaterdag een
  passage "ter plekke" op het Steegje (GPS-verschil 3 m, dus richting
  onbekend). Het Steegje heeft op zaterdag nu A plus ?.
- De Kerkstraat (alleen heen): het label is tweemaal de gemeten stroom, met
  sterretje.
- Het Steegje: het gemeten totaal, niet × 2, wel met sterretje.
- Het maximum van de schaal komt uit de opgehoogde waarden.
- Het weekoverzicht van de Kerkstraat:
  - de cel is × 2;
  - de details tonen wat gemeten is, en × 2;
  - de marge is precies tweemaal de ongeschaalde, en omsluit de opgehoogde
    waarde;
  - *gem.* is ook × 2.

`functest_passanten.js` is ongewijzigd (19), want de rekenkern verandert niet.

**Bekeken:** de kaart met *267\**, *356\** (Kerkstraat, × 2) en *373\**
(Steegje, deels onbekend, niet × 2).

## 4. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `passanten.html` | `schat()`, `OPHOGEN`; overal gebruikt; teksten |
| `index.html` | versie v3.36 |
| `traffic_counter_help.html` | rij *Richting* |
| `_archief/overpass_rig/passantentest.py`, `valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 5. Validatie

```
VALIDATIE_HIER
```
