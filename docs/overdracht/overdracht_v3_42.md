# Overdracht v3.42 — te kort gemeten: geen kleur

Jay, met de telling van 15 oktober 2026: "Nu de korte linkjes op de kaart staan
verstoren het beeld van het resultaat. 1 tik op een korte link is al gauw enorm
druk. Zie link 136445442 in deze telling."

## 0. Het gesprek vooraf

1. **Wat er gebeurde.** Stuk 136445442 is 6,6 m.
   - Sinds v3.41 heeft het een eigen passage: 2 gps-punten, 2 s, met één tik
     (een stilstaander).
   - Telrapport rekent per stuk tikken ÷ (lengte × aanwezigheid). Dat geeft 1 ÷
     (6,6 m × 2 s) = 274 p/m·u, Extreem druk, terwijl de rest van de
     Stadhuispassage op 47–61 zit.
   - In Passanten stond hetzelfde stuk op 0\* (een stilstaander is geen
     stroom). Maar het stukje 462608742 (19 m, één tegemoet, venster 27 s) stond
     op 276\*, met een marge van 0–2.041.
2. **Het getal is niet fout, de meting is te klein.** Vóór v3.41 vielen zulke
   stukjes weg. Nu tellen ze terecht mee in de tijd en de tikken, maar ze
   kregen ook een kleur.
3. **Drie mogelijkheden**, Jay koos 1:
   1. pas kleuren als er genoeg gemeten is;
   2. een kort stuk laten lenen van zijn buren (krimpen);
   3. stukken onder 20 m nooit kleuren.

## 1. Telrapport (pocket, p/m·u)

- **`PMU_MIN_MS` = 300 meter·seconde.**
  - Gemeten als lengte × aanwezigheid, alle zichtbare tellingen samen.
  - 300 is ongeveer 15 m × 20 s, een derde van een gewone passage. In Jay's
    zeven tellingen is de mediaan 890 en het 10e percentiel 273.
- **`pmuMeting(key)`** geeft `{ pmu, ms, kort }`, of `null` (geen tikken of geen
  aanwezigheid, zoals voorheen).
  - `pmuForKey` geeft alleen een waarde als het stuk niet te kort gemeten is.
  - `wayHeat` en dus de kleur volgen daaruit.
- **Kaart:** dun grijs gestreept (`KORT_KLEUR`, `dashArray '2 5'`). De tooltip
  zegt "te kort gemeten: 13 meter·seconde (lengte × aanwezigheid; een kleur
  vanaf 300)".
- **Weekprofiel:** een noot bovenaan. De cellen en de tabel tonen de cijfers
  zoals altijd, met hun marge.
- **Legenda:** "te kort gemeten".
- **GeoPackage** (laag `wegvakken`): status `te kort gemeten`, klasse `kort`,
  grijs en gestreept. `waarde` houdt de p/m·u. Bijgewerkt in de ZIP-referentie.
- **Zonder tikken** blijft het zoals het was: "bezocht, geen waarnemingen". Een
  kort stuk zonder tikken is nooit druk.

## 2. Passanten

- **`KORT_VENSTER` = 30 s.**
  - Gemeten als het ontmoetingsvenster (lengte ÷ 1,1 + tijd), alle passages in
    de cel samen, alle richtingen.
  - 30 s is ongeveer een halve gewone passage.
  - `venster(c)` en `teKort(c)` staan buiten het blok `PASSANTEN`.
- **Kaart:** grijs gestreept, zonder label, en buiten `MAXQ` (de kleurschaal).
  Klikken opent het weekoverzicht.
- **Weekoverzicht:**
  - een te korte cel is grijs met een punt, en blijft aan te klikken;
  - *gem.* volgt dezelfde regel met de vensters samen. Een kort stuk dat je
    vaker liep, krijgt daar dus een getal.
- **Details:** bovenaan "Te kort gemeten: een ontmoetingsvenster van 27 s.
  Vanaf 30 s krijgt een stuk een kleur en een getal op de kaart. …". Daaronder
  de cijfers zoals altijd.
- **Teksten:** de legenda, de uitleg onder de kaart en de handleiding (rij
  *Kaart*).

Aan de rekenkern `PASSANTEN`, het rekenrig, de ijking, de ZIP's en het schema
verandert niets.

## 3. Wat het doet met Jay's telling van 15 oktober

| stuk | lengte | meting | telrapport | Passanten |
|---|---|---|---|---|
| 136445442 | 6,6 m | 2 s, 1 stilstaand | 13 m·s: grijs (was 274 p/m·u) | venster 12 s: grijs (was 0\*) |
| 462608742 | 19,2 m | 9 s, 1 tegemoet + 1 stilstaand | 173 m·s: grijs (was 42) | venster 27 s: grijs (was 276\*) |
| 1485744212 | 17,7 m | 16 s, 3 tikken | 284 m·s: grijs (was 38) | venster 42 s: gekleurd (727\*) |
| de rest | 36–52 m | | gekleurd zoals voorheen | gekleurd zoals voorheen |

Het derde stukje laat zien dat de twee maten verschillen. Telrapport kijkt naar
lengte × tijd; Passanten ook naar L/v, de tijd dat een tegemoetkomer in het stuk
is. Een stuk van 18 m in 16 s is voor Passanten net genoeg, voor telrapport net
niet.

**Bekeken:**
- de kaart van telrapport en van Passanten met deze telling;
- het weekoverzicht van 462608742.

## 4. Tests

- **`functest_kort.js`** (nieuw, 12). Het knipt de functies uit `telrapport.html`
  en draait ze in Node:
  - een gewoon stuk krijgt zijn waarde en zijn kleur;
  - Jay's stukje (6,6 m × 2 s, 1 tik) heeft 273 p/m·u, maar is te kort: geen
    waarde, geen kleur, dun grijs gestreept, met de tekst;
  - twee tellingen samen (6,6 m × 52 s) geven wel een kleur; met één verborgen
    is het weer te kort;
  - zonder tikken: "bezocht, geen waarnemingen", zoals altijd.
- **`passantentest.py`** (62, was 55), nieuw deel T:
  - in de testgegevens is niets te kort;
  - met de drempel even net boven het kleinste venster: dat stuk is grijs
    gestreept, zonder label en buiten de schaal;
  - de legenda, de details en het weekoverzicht (grijze cel met een punt);
  - de drempel terug: alles weer gekleurd.

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telrapport.html` | `PMU_MIN_MS`, `pmuMeting`, `KORT_KLEUR`, `kortTekst`; kaart, tooltip, weekprofiel, legenda, GeoPackage |
| `passanten.html` | `KORT_VENSTER`, `venster`, `teKort`; kaart, `MAXQ`, legenda, weekoverzicht, details, uitleg |
| `traffic_counter_help.html` | Passanten (rij *Kaart*) en telrapport (*Te kort gemeten*) |
| `zip_format_reference.html` | GeoPackage `wegvakken`: status `te kort gemeten` |
| `index.html` | versie v3.42 |
| `_archief/overpass_rig/functest_kort.js` | nieuw |
| `_archief/overpass_rig/passantentest.py`, `valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 6. Validatie

```
valideer.py            ALLES OK — precies de 5 verwachte bestanden gewijzigd
functest_kort.js       12/12
passantentest.py       62/62
volledige ronde lokaal: zie de PR
```
