# Overdracht v3.41 — een kort stukje krijgt een eigen passage

Jay: "een stukje van 15 meter zijn eigen passage - dat wil ik graag". Na het
voorstel: "ga".

## 0. Het gesprek vooraf

1. **De aanleiding.** In het rekenvoorbeeld (telling van 26 oktober 2026, in het
   project: `claude/passanten_rekenvoorbeeld.md`) zat een gat van 25 s tussen
   twee passages, met daarin een tik.
2. **Wat er gebeurde.** In die 25 s lagen zes gps-punten. Jay sloeg daar een
   hoek om:
   - eerst nog een paar meter van het lange stuk;
   - dan een stukje van 15 m;
   - dan een paar meter van nog een klein stukje, tot de volgende straat.

   Elk van die drie kreeg 1 à 3 punten, binnen een paar seconden. Een bezoek in
   `_bezocht.csv` moet minstens 5 s duren en 3 punten hebben, dus alle drie
   vielen weg.
3. **Waar de stukken en de gaten vandaan komen** (Jay vroeg het):
   - de stukken zitten in het netwerk (`_netwerk.csv`): wegen uit OSM, geknipt in
     stukken van ongeveer 30–45 m, aaneensluitend;
   - de passages komen uit de gps-opname: een reeks punten op hetzelfde stuk;
   - de gaten zitten dus in de gps-tijdlijn, niet in de straat.
4. **Het voorstel, door Jay goedgekeurd:**
   - een korte reeks blijft toch een passage als je erdoorheen liep en het stuk
     hooguit 20 m is;
   - alleen in de reconstructie, waar de route echt aansluit;
   - het versienummer van de reconstructie gaat naar v3.41.
5. **Bij het bouwen erbij: minstens 2 punten.** Begin en eind van een bezoek zijn
   de tijden van het eerste en laatste punt. Eén punt geeft dus duur 0, en de
   ZIP-referentie en de handleiding rekenen in KNIME
   `n_tellingen × 60 / duur_sec`. Een stukje met één punt is meestal maar een
   paar meter.

## 1. De regel (`herbouwBezocht` in `telreconstructie.html`)

Een reeks gps-punten die de drempels (5 s én 3 punten) niet haalt, blijft toch
een bezoek als aan alle voorwaarden is voldaan:
- **Een doorgang.** De reeks ervoor en de reeks erna liggen op verschillende
  wegen, en geen van beide op de weg van dit stuk.
  - A → X → A (een uitstapje, of gps-ruis bij een kruising) valt af.
  - A → X → A verderop valt ook af.
  - Aan het begin of eind van de route is er geen doorgang.
- **Een kort stuk.** Het stuk is hooguit `KORT_MAX` = 20 m.
  - Zo'n stuk is altijd een hele korte weg: wegen onder `SEGMENT_MIN_M` (60 m)
    worden niet geknipt, en een geknipt stuk is minstens 30 m.
  - Een kort bezoek aan een lang stuk is een afgesneden hoek: je liep er maar
    een paar meter van, en een passage zou de hele lengte claimen.
- **Minstens 2 punten**, zodat `duur_sec` boven 0 blijft.

Het bezoek houdt de tijden van zijn eerste en laatste punt. Passanten deelt de
gaatjes ernaast (v3.40).

De lengte wordt gemeten zoals de knip hem maakt: `splitWayIntoSegments` op de
geometrie van de weg (`stukLengte`).

**Niet in de live-snap van pocket** (`buildBezochtCsv`). Die is ruiziger, en
Jay reconstrueert zijn winkelstraattellingen altijd.

## 2. Gevolgen

- **Het geldt voor elke reconstructie vanaf nu**, ook transect, simpel en
  parkeren. Daar telt een kort stukje waar je doorheen liep nu ook als bezocht
  (in telrapport gestreept als er niets geteld is).
- **`RECON_VERSIE` is v3.41.** Het staat in `_sessie.csv` (kolom
  *reconstructie*) en in `_reconstructie_log.csv`, zodat je in elke ZIP ziet
  welke regel gold.
- **Bestaande tellingen** veranderen pas als je ze opnieuw reconstrueert; de
  originelen staan in Archief. De gaatjes uit v3.40 vangen het meeste al op.
- **Aan de kolommen verandert niets.** Er kunnen alleen rijen bij komen, met een
  `duur_sec` van minstens 1.

## 3. Niet nagegaan op echte gegevens

De regel is niet nagerekend op de telling van 26 oktober. Daarvoor is het
origineel nodig, en een Overpass-verbinding die de testomgeving niet heeft. Op
afstand tot de stukken lijkt het zo uit te pakken:
- het stukje van 15 m krijgt 2 à 3 punten (12:25:44, 12:25:47, 12:25:51) en
  wordt een passage;
- het stukje erna wordt het waarschijnlijk ook;
- de hoek van de lange straat niet.

Jay kan het nagaan door het origineel van 26 oktober opnieuw te reconstrueren.

## 4. Tests

**`functest_bezocht.js`** (nieuw, 16). Het knipt `herbouwBezocht`,
`splitWayIntoSegments` en de hulpfuncties uit de pagina en draait ze in Node,
op een klein netwerk met vijf wegen: A (120 m, 3 stukken), X en Z (15 m), Y
(30 m, één stuk) en B (80 m).
- **Gewone bezoeken:** zoals altijd, met de tijden van het eerste en laatste
  punt.
- **Nieuwe passages:**
  - A → X (2 punten, 3 s) → B: X is een passage, met zijn tijden en de tik in
    zijn venster;
  - twee korte stukjes achter elkaar zijn allebei een passage.
- **Geen passage:**
  - X met 1 punt (en nergens een duur van 0);
  - Y (30 m): een afgesneden hoek;
  - A → Z → A, en A → Z → A verderop;
  - een kort bezoek aan een stuk van een lange weg;
  - een kort stukje aan het begin of eind van de route.
- **Versiestempel:** v3.41.

Met de oude `herbouwBezocht` falen de vier tests die een nieuwe passage
verwachten.

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `telreconstructie.html` | `herbouwBezocht`: `KORT_MAX`, `stukLengte`, de regel; `RECON_VERSIE` v3.41 |
| `traffic_counter_help.html` | drempels van `_bezocht.csv`: "5 seconden én 3 GPS-punten" (er stond "of"; de code was altijd "en") en de uitzondering |
| `zip_format_reference.html` | rij `_bezocht.csv` na een reconstructie |
| `index.html` | versie v3.41 |
| `_archief/overpass_rig/functest_bezocht.js` | nieuw |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 6. Validatie

```
valideer.py            ALLES OK — precies de 4 verwachte bestanden gewijzigd; RECON_VERSIE v3.41
functest_bezocht.js    16/16
overige functests, test_zipref, check_encoding en de browsertests rond telreconstructie lokaal groen; de rest op GitHub
```
