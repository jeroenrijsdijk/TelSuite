# Overdracht v3.43 — Passanten: de dagcurve

Jay: "zou je uit een grote set winkelstraat tellingen ook algemenere dagcurves
kunnen maken? wat basisdata om factoren uit te halen." Met `catalogus.csv`
erbij: "Onze tabel moet een plekje krijgen in passanten".

## 0. Het gesprek vooraf

1. **Wat er is.** De catalogus van Archief telt 101 unieke
   winkelstraattellingen, van 16 juni tot 29 oktober 2026. 88 daarvan liggen
   in hetzelfde centrum, dus dezelfde straten zijn vaak op verschillende
   momenten gelopen. De tellingen duren een paar minuten en vallen elk in één
   uur.
2. **Waar ze vallen** (de tabel uit de catalogus, tellingen per weekdag en
   beginuur):
   - de uren 11–16 zijn goed gedekt, de werkdagen samen 83 tellingen;
   - zaterdag 15, zondag 3;
   - vrijdag maar 7;
   - voor 9 en na 17 uur bijna niets.
3. **Waarom niet gewoon middelen per uur.** Dan meng je de straat met het
   uur: liep je de drukke straat vooral op zaterdag, dan lijkt de zaterdag
   drukker dan hij is. Daarom een model met een niveau per stuk straat en een
   factor per moment.
4. **"Onze tabel"** is die dekkingstabel. Hij staat nu in het tabblad, als
   *Waar gemeten is*, uit de tellingen die je inleest. Daarboven staan de
   factoren.

## 1. Het model

```
verwachte tegemoetkomers = venster/3600 · A[stuk|richting] · F[dagtype:uur] · D[weekdag]
```

- **Venster** = lengte ÷ 1,1 + tijd, zoals overal in Passanten. Dus inclusief
  de gaatjes van v3.40.
- **Dagtype:** werkdag (ma–vr), zaterdag, zondag.
- **D** geldt alleen voor de werkdagen: hetzelfde verloop over de dag, met een
  eigen niveau per dag.
- **Het uur** is het uur van het midden van de passage, zoals in de kaart.
- **Schatten:** grootste aannemelijkheid (Poisson). Om de beurt worden A, F en
  D bijgewerkt tot het stilstaat (iterative proportional fitting; stopt bij
  een relatieve verandering onder 10⁻⁹, hooguit 3000 rondes).
  - Passages met hetzelfde stuk, dezelfde richting, weekdag en uur gaan eerst
    samen.
  - Een stuk dat maar op één moment geteld is, valt vanzelf weg: zijn A neemt
    het op.
- **Wat te scheiden is** (`dcGroepen`, union-find in twee stappen):
  1. Stukken en momenten (weekdag:uur) hangen samen als een stuk op dat moment
     geteld is. Alleen de grootste groep doet mee. Een andere straat op een
     ander moment zegt niets: komt het verschil dan van de straat of van het
     uur?
  2. Een werkdagmoment is uur × weekdag. Uren en weekdagen zijn pas uit elkaar
     te halen als ze via gemeten combinaties samenhangen (ma 15, di 15, di 12,
     …). Alleen die groep krijgt een werkdagcurve en weekdagfactoren.

  Wat buiten valt, krijgt geen getal, maar een streepje: "niet te scheiden van
  de straat". Zonder die stap zou de pagina voor zo'n vakje een getal tonen dat
  alleen van het startpunt van de berekening afhangt.
- **De schaal** (`dcNormeer`):
  - de werkdagen met genoeg metingen zijn samen gemiddeld 1 (zijn er geen: alle
    werkdagen die te scheiden zijn);
  - **index 100** = het gemiddelde werkdaguur van 11 tot 16 uur (`DC_REF`), over
    de uren daar met genoeg metingen;
  - is daar niets, dan het gemiddelde van de werkdaguren met genoeg; anders van
    alle uren met genoeg. De uitleg zegt welke.
- **Genoeg:** minstens 2 tellingen en 10 tegemoetkomers (`DC_MIN_TELLINGEN`,
  `DC_MIN_TIKKEN`), en te scheiden. Anders een streepje in de tabel en geen punt
  in de grafiek.
- **Marge (95%):** dezelfde schatting op 200 trekkingen van hele tellingen,
  met teruglegging (`DC_TREKKINGEN`), het 2,5- en het 97,5-percentiel.
  - Elke trekking krijgt dezelfde schaal (dezelfde dagen en referentie-uren).
    Een trekking waarin die niet te scheiden zijn, telt niet mee.
  - Het zaad ligt vast (mulberry32, 343): dezelfde gegevens geven dezelfde
    marge.
  - Pas vanaf 20 bruikbare trekkingen staat er een marge.
  - Een vakje met maar één telling heeft een te smalle marge: de trekking ziet
    dan alleen de rest bewegen. Daarom de drempel van 2.
- **IJking en ophogen spelen geen rol.** Het gaat om verhoudingen, per gemeten
  stroom. De × 1,05 valt weg, en de ophoging van een richting ook.

Alles staat in de pagina, buiten het blok `PASSANTEN`. Het rekenrig en de
rekenkern veranderen niet.

## 2. Het tabblad

- **Twee knoppen boven de kaart:** *Kaart* en *Dagcurve*. Ze zijn er zodra er
  tellingen zijn.
  - De kaart, de keuze en de uitleg staan in `#tab-kaart`.
  - Terug naar de kaart roept `invalidateSize()` aan.
- **Rekenen** gebeurt bij het openen. Eerst staat er "Rekent de dagcurve …";
  bij 100 tellingen duurt het ongeveer een seconde (200 trekkingen).
  `herbereken()` leegt de uitkomst (`DAGCURVE`).
- **Uitleg:** hoe de curve gemaakt is, wat index 100 is, hoe je omrekent, wat
  een streepje betekent, en de marge.
- **Grafiek** (SVG, zo breed als het vak, dus ook op 390 px leesbaar):
  - per dagtype een lijn met een band (werkdag `#2f5d62`, zaterdag `#b0342b`,
    zondag `#8a7a2b`);
  - onderbroken waar een uur niet genoeg heeft;
  - een stippellijn op 100;
  - is er nergens genoeg: "Nog te weinig gemeten voor een curve".
- **Tabellen:**
  - uur × werkdag/zaterdag/zondag: de index met de marge; de tooltip noemt de
    tellingen en tegemoetkomers;
  - de weekdagfactoren ma–vr, met marge en tellingen;
  - *Waar gemeten is*: tellingen per weekdag en uur. Een telling telt in elk
    uur waarin ze passages heeft.
- **Twee knoppen:** `dagcurve.csv` en `passages.csv (basisdata)`, als download.

**Omrekenen.** Een telling op een werkdag om 14 uur met Q passanten per uur
geeft voor een gemiddeld werkdaguur Q × 100 ÷ index(werkdag 14). Daarna nog
÷ de factor van die weekdag. Op zaterdag om 13 uur: Q × 100 ÷ index(zaterdag 13).

## 3. De CSV's (nieuw, in de ZIP-referentie)

Het zijn uitvoerbestanden: niets leest ze terug, en aan de ZIP's en KNIME
verandert niets. De kolommen zijn een voorstel; Jay kan ze nog laten aanpassen.

- **`passages.csv`:**
  `sessie_id;datum;weekdag;uur;osm_way_id;segment_index;straat;richting;lengte_m;tijd_s;venster_s;tegemoet;stilstaand`.
  - Een regel per passage zoals Passanten hem gebruikt (de reconstructie waar
    die er is).
  - `tijd_s` is inclusief de gaatjes.
  - Hieruit is alles na te rekenen; de browsertest doet dat (§5).
- **`dagcurve.csv`:** `soort;dag;uur;index;onder;boven;tellingen;tegemoet;genoeg`.
  - `soort` = `uur`: een regel per dagtype en uur.
  - `soort` = `weekdag`: ma–vr, als index (100 × de factor).
  - Leeg waar niets te scheiden is; `genoeg` = `ja`/`nee`.

## 4. Wat het doet met Jay's tellingen

- **Met de zes ZIP's van deze weken** (twf, usb, knz, yxn, xmw, fwb) valt er
  weinig te zien.
  - Elke telling ligt in één uur, op een andere dag.
  - Alleen de twee maandagen (12 en 16 uur) hangen via dezelfde stukken
    samen.
  - De rest is niet te scheiden. De grafiek zegt "Nog te weinig gemeten".
- **Met de 101 uit de catalogus** is het naar verwachting anders, al is het niet
  nagerekend: de ZIP's zelf zijn hier niet.
  - De werkdaguren 11–16 halen ruim genoeg.
  - Zaterdag heeft per uur 1 à 6 tellingen; een deel krijgt een streepje.
  - Zondag (3 tellingen) en vrijdag (7) worden dun.
  - De uren voor 9 en na 17 krijgen streepjes.
- **De seizoenen zitten erdoor** (juni tot oktober). Eén curve voor alles; het
  model heeft geen maand.

Op gemaakte tellingen (101: 83 op werkdagen, 15 op zaterdag, 3 op zondag; 40 straten) ziet het
tabblad eruit zoals verwacht: werkdag 42 → 112 → 58 van 9 tot 17 uur, zaterdag
daarboven, marges van ± 5–10% op de werkdag.

## 5. Tests

- **`functest_dagcurve.js`** (nieuw, 27). Het knipt het rekendeel uit
  `passanten.html` en draait het in Node:
  - Precies: met de verwachte aantallen komen de echte factoren terug, tot
    10⁻⁶ (werkdag, zaterdag, weekdagen). In de pagina telt een vrijdag met
    één telling niet mee in het gemiddelde van 1.
  - De straat en het uur niet verwarren: een drukke straat alleen op zaterdag.
    Het gewone gemiddelde zegt 2,67, het model de echte 1,33.
  - Wat niet te scheiden is:
    - een los stuk op zondag krijgt geen index en geen marge, en de rest
      blijft precies gelijk;
    - ma 9 en di 10 met hetzelfde stuk: één van de twee valt weg.
  - Toevalsgetallen (100 tellingen):
    - in 1,1–1,4 s;
    - de marge bevat de echte index in 15 van de 16 uren;
    - de index ligt gemiddeld 1% ernaast;
    - 4 van de 5 weekdagfactoren liggen binnen hun marge;
    - het is herhaalbaar.
  - Eén telling: geen marge en niets genoeg.
  - De CSV's: kolommen, rijen, decimalen en vensters.
- **`passantentest.py`** (76, was 62), nieuw deel DC:
  - de tabbladen en wat er zichtbaar is;
  - de vakjes van de testgegevens: zaterdag 13 uur met 2 tellingen, werkdag
    11 uur met 1;
  - index 100 = zaterdag 13, omdat er op werkdagen te weinig is;
  - werkdag 11 los nagerekend met hetzelfde model in Python
    (`dagcurve_ipf`), en nog eens uit `passages.csv` alleen;
  - de tabel, *Waar gemeten is*, de twee downloads, terug naar de kaart, en
    `herbereken()`;
  - op 390 px past alles.
- **`test_zipref.py`** kijkt nu ook naar `passanten.html` (de kopregel van
  `passages.csv`).

## 6. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `passanten.html` | tabbladen; blok *Dagcurve* (`dcWaarnemingen`, `dcGroepen`, `dcSchat`, `dcNormeer`, `dagcurve`, grafiek, tabellen, CSV's); CSS |
| `traffic_counter_help.html` | Passanten: rij *Dagcurve* |
| `zip_format_reference.html` | nieuw: *Passanten exports (dagcurve.csv, passages.csv)* |
| `index.html` | versie v3.43 |
| `_archief/overpass_rig/functest_dagcurve.js` | nieuw |
| `_archief/overpass_rig/passantentest.py`, `test_zipref.py`, `valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 7. Validatie

```
valideer.py            ALLES OK — precies de 4 verwachte bestanden gewijzigd
functest_dagcurve.js   27/27
passantentest.py       76/76
test_zipref.py         REFERENTIE SLUIT AAN OP DE CODE
volledige ronde lokaal: zie de PR
```
