# Overdracht v3.36 — één looprichting opgehoogd in Passanten

Jay: "De linkjes die maar in 1 richting gelopen zijn - doe je die
passantentelling x 2 om op te hogen naar een 2-richtingen waarde?"

## 0. Het gesprek vooraf

1. **Tot v3.36 verdubbelde Passanten niet.** Een stuk dat maar één kant op
   gelopen was, toonde de ene gemeten stroom met een sterretje. Dat was mijn
   voorstel bij v3.34, zodat er nooit een getal op de kaart staat dat niet
   gemeten is.
2. **Het nadeel:** op de kaart lijkt zo'n stuk ongeveer half zo druk als zijn
   buren. Wie op de kleur afgaat, ziet een rustige straat die het niet is.
3. **Mijn voorstel:** wel × 2, maar zichtbaar. Het sterretje blijft, de details
   tonen wat gemeten is, en de marge gaat mee. Slimmer ophogen, met de
   verhouding die elders in dezelfde straat gemeten is, heb ik genoemd als
   vervolg. Jay: "ja".
4. **PR #51 bevatte eerst alleen × 2.** Daarna vroeg Jay: "bouw dat slimme
   ophogen ook maar gelijk in dezelfde PR #51". Deze overdracht beschrijft beide.

Aan de rekenkern (het gedeelde blok `passanten`), het rekenrig, de ZIP's en het
schema verandert niets. Het ophogen gebeurt in `passanten.html`, bij het tonen.

## 1. De regel: `schat(c, seg)`

- **Beide richtingen gemeten:** de som van de twee stromen, zoals altijd.
- **Precies één stroom gemeten, met bekende richting (A of B):**
  - Is elders in **dezelfde straat** op **hetzelfde moment** (weekdag en uur)
    wél in beide richtingen gelopen, dan:
    - opgehoogd = gemeten × (1 + ρ);
    - ρ = (de andere kant op) ÷ (deze kant op), elk als 3600 · Σm / Σvenster
      over die stukken samen (`verhouding`).
  - Anders × 2: evenveel mensen de andere kant op.
- **Precies één stroom met onbekende richting:** × 2. Welke verhouding er hoort,
  is dan niet te zeggen.
- **Twee stromen waarvan één een onbekende richting heeft (A plus ?):** het
  gemeten totaal, niet opgehoogd, wel met een sterretje. De onbekende passage
  kan de andere richting zijn geweest, en ophogen zou dan dubbel tellen.

Details van `verhouding(seg, momenten, r)`:
- **Dezelfde straat:** dezelfde straatnaam (hoofdletters tellen niet; een stuk
  zonder naam doet niet mee). Een straat kan uit meer OSM-wegen bestaan, en die
  zijn niet allemaal dezelfde kant op getekend.
- **Richting gelijk trekken:** van elk stuk is de tekenrichting bekend, dat is
  de richting A met oplopende `segment_index`.
  - Ligt een ander stuk dezelfde kant op (cosinus > 0,5), dan telt zijn A als
    A.
  - Ligt het de andere kant op (< −0,5), dan telt zijn A als B.
  - Een stuk dat er dwars op staat, doet niet mee.
- **Alleen stukken die op dat moment in beide richtingen gelopen zijn**, en
  het stuk zelf niet.
- **Drempel:** minstens `MIN_TEGEN` (10) tegenliggers per richting in de
  vergelijking. Anders × 2. Zo wordt een verhouding uit een handvol tikken niet
  de basis.
- **Bij *gem.*** (een dag of een uur samen) gaat het om de vergelijking over
  dezelfde momenten samen (`samen()` geeft `cks` mee).
- **Geheugen:** `SCHATTINGEN` per stuk en moment. `herbereken()` maakt het
  leeg. Zonder stuk wordt er niets onthouden: dan is het × 2.

## 2. Waar het geldt

- **Kaart:** de kleur van een stuk, de labels, welk label voorgaat bij overlap,
  en het maximum van de kleurschaal.
- **Weekoverzicht:** de cellen en *gem.*
- **Details:**
  - Met een verhouding:

    > "\* maar één looprichting gemeten: N per uur, de stroom die je tegemoet
    > kwam. Elders in de Voorstraat is op zaterdag 13:00 wél in beide
    > richtingen gelopen (5 stukken): daar liep 0,82 keer zoveel de andere kant
    > op. Opgehoogd: × 1,82."

  - Zonder verhouding: "In deze straat is op zaterdag 13:00 niet genoeg in
    beide richtingen geteld om de verhouding te nemen, dus aangenomen dat er
    evenveel mensen de andere kant op lopen: × 2."
  - Met een onbekende richting: "… De richting is onbekend …: × 2."
  - Met een deels onbekende richting: het gemeten totaal, niet opgehoogd.
- **Marge:** gaat mee met de ophoging. De onzekerheid van de verhouding of van
  de aanname zelf zit er niet in.
- **Teksten:**
  - De legenda zegt "\* niet in beide richtingen gemeten: opgehoogd (zie de
    details)".
  - Het weekoverzicht en de uitleg onder de kaart zeggen hetzelfde.
  - De handleiding legt beide manieren uit (rij *Richting*), met een
    voorbeeld en de waarschuwing over een station of parkeergarage aan één
    kant.

## 3. Tests

**`passantentest.py`** 46 (was 35). De testgegevens hebben er twee stukken
Voorstraat bij, elk maar heen gelopen:
- 1004 ligt dezelfde kant op getekend als de Voorstraat;
- 1005 ligt andersom getekend (oost naar west).

Daarnaast heeft de tweede zaterdag een passage "ter plekke" op het Steegje
(richting onbekend).

De verwachte waarden rekent de test zelf (`schat_slim`).

- **C.**
  - De labels volgens de ophoging.
  - Kerkstraat: × 2 (er is geen andere Kerkstraat).
  - Steegje: A plus ?, dus het gemeten totaal.
  - 12 stukken, en de sterretjes.
  - Het maximum van de schaal.
- **S. Slimmer ophogen:**
  - 1004 is opgehoogd met de verhouding uit de Voorstraat (× 1,82, niet × 2).
  - 1005 krijgt de omgedraaide verhouding (× 2,22 = 1 + 1/0,82).
  - De pagina rekent dezelfde ρ, over 5 stukken.
  - De details noemen de bron.
  - Bij de Kerkstraat staat waarom × 2.
  - Met de drempel tijdelijk op 1000 valt hij terug op × 2.
- **W.** In het weekoverzicht van de Kerkstraat zijn de cel, de details, de
  marge (precies × 2) en *gem.* × 2.

`functest_passanten.js` is ongewijzigd (19).

**Bekeken:** de kaart met de Voorstraat-oost (*307\**, *384\**, *560\**, *280\**,
met verhouding) en de Kerkstraat (*267\**, *356\**, × 2).

## 4. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `passanten.html` | `schat(c, seg)`, `verhouding`, `richtingVan`, `ophoogTekst`, `MIN_TEGEN`, `SCHATTINGEN`; overal gebruikt; teksten |
| `index.html` | versie v3.36 |
| `traffic_counter_help.html` | rij *Richting* |
| `_archief/overpass_rig/passantentest.py`, `valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 5. Validatie

```
VALIDATIE_HIER
```
