# Overdracht v3.45 — erdoorheen is bezocht

Jay, met een autorit van 31 oktober 2026 (pocket simpel, fietsen geteld; het
origineel en de reconstructie): "Waarom zijn er heel veel linkjes die niet als
bezocht zijn gemarkeerd?" Na het voorstel: "1. is goed. 2. alleen in de
reconstructie".

## 0. Het gesprek vooraf

1. **De drempel is voor lopen gemaakt.** Een stuk telt als bezocht bij 5 s én
   3 gps-punten.
   - Lopend ben je zo'n 30 s op een stuk van 40 m. De drempel houdt dan alleen
     een afgesneden hoek buiten.
   - In de auto ben je er in 3–4 s doorheen. Deze rit reed mediaan 29 km/u
     (p90 51 km/u).
   - Van de 117 reeksen op een stuk in de opname haalden er 16 de drempel.
     86 hadden genoeg punten maar te weinig tijd.
   - Voorbeeld uit Jay's plaatje: Duinpan 7590147/4 16:07:10–13 (3 s), /3
     16:07:14–17 (3 s), /2 2 s, enzovoort.
2. **Een fout uit v3.41.** In de reconstructie stonden drie bezoeken met
   `duur_sec` 0 (1339068267, 416884979, 95202378).
   - De regel van v3.41 rekende op "minstens 2 punten, dus duur boven 0".
   - Deze telefoon geeft in de auto vaak twee punten in dezelfde seconde
     (168 keer in deze rit).
   - KNIME deelt door `duur_sec`.
3. **Het voorstel, door Jay goedgekeurd:**
   - een stuk telt ook als je erdoorheen kwam;
   - aanvullend: de oude regel blijft gelden;
   - alleen in de reconstructie.

## 1. De regel (`herbouwBezocht` in `telreconstructie.html`)

Een reeks die 5 s en 3 punten niet haalt, is toch een bezoek als:

- **De duur minstens 1 s is.** Dat geldt nu ook voor de korte stukjes van v3.41.
  Twee punten in dezelfde seconde zijn geen bezoek meer.
- **En je minstens de helft van het stuk zag** (`DOOR_DEEL` = 0,5). Dat is het
  deel van het stuk tussen waar je erop kwam en eraf ging, gemeten langs het
  stuk.
  - Gemeten wordt met de gps-punten van de reeks, plus het midden van het
    gaatje naar het punt ervoor en erna. Een gaatje telt alleen als het
    hooguit `DOOR_GAT` = 5 s is, zoals de gaatjes in Passanten (v3.40).
  - Elk van die punten wordt op het stuk gelegd (`langs`): de afstand langs het
    stuk tot het dichtstbijzijnde punt. Het verschil tussen de grootste en de
    kleinste is wat je zag (`gezien`).
  - Op het stuk gelegd, niet als afgelegde weg: een gps-sprong opzij of een
    afgesneden hoek beslaat zo maar een paar meter van het stuk.
- **Of** de regel van v3.41: een kort stuk (≤ 20 m) met een doorgang.

Het bezoek houdt de tijden van zijn eerste en laatste punt. In de auto is
`duur_sec` dus 1–4 s.

`RECON_VERSIE` is v3.45. Het staat in `_sessie.csv` en het reconstructielog.
Bestaande tellingen veranderen pas als je ze opnieuw reconstrueert.

**Niet in pocket** (Jay: "alleen in de reconstructie"). De live-snap houdt 5 s
en 3 punten.

## 2. Wat het doet

Nagebootst in Python op de reeksen uit de opname (de live-snap in `_gps.csv`),
met dezelfde regel. De reconstructie zelf kon hier niet draaien: die haalt het
netwerk vers op bij Overpass.

| telling | reeksen | oud | v3.45 |
|---|---|---|---|
| autorit 31 okt (kjh, pocket simpel) | 117 | 16 | 112 |
| winkelstraat usb | 14 | 9 | 10 |
| winkelstraat twf | 9 | 8 | 9 |
| winkelstraat knz | 13 | 13 | 13 |
| winkelstraat yxn | 12 | 11 | 11 |
| winkelstraat fwb | 21 | 12 | 13 |

- **Lopend** komt er hooguit een kort stukje bij (7–13 m in 2–4 s). Er valt
  niets af, want de regel is aanvullend.
- **De vijf** die bij de autorit overblijven:
  - drie hebben 2 punten en zagen 10–17 m van een stuk van 34–40 m (het begin
    van de rit, en een bocht);
  - één heeft maar 1 punt;
  - één heeft 2 punten in dezelfde seconde.
- **Grens:** bij 80 km/u met een punt per 2 s krijgt een stuk van 40 m één
  punt, en dat blijft grijs. Deze telefoon meet in de auto meestal elke seconde.
- **In telrapport** krijgt een stuk met een fietstik uit de auto nu een bezoek
  van een paar seconden. 40 m × 3 s is onder de 300 m·s, dus het staat grijs
  gestreept: "te kort gemeten". Eerder was het donkergrijs zonder bezoek.
  p/m·u is een maat voor lopen.
- **KNIME** (`n_tellingen × 60 / duur_sec`): de duur van een bezoek in de auto
  is kort, dus de flux per bezoek springt. Er is geen duur van 0 meer.

## 3. Tests

**`functest_bezocht.js`** (24, was 16). Voor het nieuwe deel liggen de punten
nu op een plek:

- **Bezocht:**
  - een auto over weg A en B, 10 m/s, elke seconde een punt: elk stuk van
    40 m (3–4 s, 4 punten) is bezocht, met de tijden van de punten en de tik;
  - het korte stukje X ertussen (2 punten, 1 s) ook.
- **Niet bezocht:**
  - een gps-sprong opzij (2 punten, 1 m van de 30 m, een sprong van 80 m
    erheen);
  - een afgesneden hoek;
  - een stuk met 1 m gezien en een gaatje van 23 s erna;
  - twee punten in dezelfde seconde op een kort stukje met een doorgang: geen
    bezoek meer, en nergens duur 0.
- **Lopend:** zoals altijd.
- **Versiestempel** v3.45.

## 4. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telreconstructie.html` | `herbouwBezocht`: `DOOR_DEEL`, `DOOR_GAT`, `langs`, `gezien`, duur ≥ 1 s; `RECON_VERSIE` v3.45 |
| `traffic_counter_help.html` | drempels van `_bezocht.csv`: de uitzondering van v3.45 |
| `zip_format_reference.html` | rij `_bezocht.csv` na een reconstructie |
| `index.html` | versie v3.45 |
| `_archief/overpass_rig/functest_bezocht.js`, `valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 5. Validatie

```
valideer.py            ALLES OK — precies de 4 verwachte bestanden gewijzigd; RECON_VERSIE v3.45
functest_bezocht.js    24/24
volledige ronde lokaal: zie de PR
```
