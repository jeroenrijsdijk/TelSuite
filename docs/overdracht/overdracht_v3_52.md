# Overdracht v3.52 — Passanten: stippen in de dagcurve

Jay: "zou de dagcurve grafiek niet beter een boxplot zijn?" Na het voorstel
(een stip per telling): "Het gaat om het aangeven van de spreiding - aangeven
dat het gemiddelde niet als waarheid moeten worden gezien - je stippen zijn een
mooi idee".

## 0. Waarom geen boxplot

- Per uur zijn er 2 tot 20 tellingen. Een doos van 2 of 3 waarden zegt weinig,
  en de doos verbergt wie er afwijkt.
- De band van de dagcurve is iets anders dan de spreiding: hij zegt hoe zeker
  het **gemiddelde** is (95%, uit de trekkingen). Hoe ver één telling ervan af
  kan liggen, staat er niet in. Dat laten de stippen zien.
- De lijn en de band blijven staan. Alleen de stippen komen erbij.

## 1. Wat een stip is

Eén telling in één uur (vakje `dagtype:uur`). De index van een stip:

```
index = 100 · (m ÷ e) · gem ÷ r        (gem alleen op werkdagen)
m = de tegemoetkomers van die telling in dat uur
e = Σ w · A[stuk|richting] · D[weekdag]   over haar waarnemingen in dat uur
```

- `e` is wat het model voor die telling verwacht zonder het uur: het venster,
  het niveau van de straat en de weekdag.
- `gem` en `r` komen uit `dcNormeer`: dezelfde schaal als de curve, index
  100 = een gemiddeld werkdaguur van 11 tot 16 uur.
- Bij convergentie is `F[k] = Σm ÷ Σe` over het vakje. Het gemiddelde van de
  stippen, gewogen met `e`, is dus precies de index van de curve. Met verwachte
  aantallen zonder ruis valt elke stip op de curve. Beide staan in de test.
- Alleen vakjes die te scheiden zijn (niet `los`), en alleen getekend waar de
  curve een punt heeft (`genoeg`). Een stuk zonder één tegemoetkomer heeft
  `A = 0` en `e = 0`: geen stip. Ook geen bijdrage aan de curve.

## 2. Code (`passanten.html`)

- **`dcWaarnemingen`**: per waarneming ook `t`, de seconden op de stukken.
- **`dcSchat`** geeft `A` en `uNr` mee, **`dcNormeer`** geeft `gem` en `r` mee.
  Verder niets veranderd.
- **`dcStippen(s0, basis, cel)`**: loopt één keer over `s0.mee`, telt per
  telling en vakje `m`, `e`, passages en seconden op. Geeft
  `{ sid, k, type, dag, uur, index, tikken, passages, seconden, gewicht }`.
  `dagcurveVan` zet de lijst in `stippen`, ook voor een keuze.
- **`dcOpzij(id)`**: FNV-hash van de sessie-id, −0,5 … 0,5. Een telling staat in
  elk uur even ver opzij (± 0,3 uur van het midden).
- **`dcGrafiek`**:
  - de stippen eerst, onder de band, de lijn en de punten;
  - kleur van het dagtype, dekking 0,35;
  - straal 1,6 tot 3, met de wortel van de minuten op de stukken in dat uur
    (vol vanaf een half uur): een paar minuten is een kleine stip;
  - de schaal neemt de stippen mee tot het 97,5e percentiel; wat hoger ligt,
    wordt een driehoekje bovenaan (`dc-stip boven`);
  - tooltip: sessie-id, weekdag en datum, uur, index, tegemoetkomers en
    minuten;
  - band, lijnen en foutlijnen `pointer-events="none"`, zodat de tooltip van
    een stip eronder werkt;
  - in de legenda, tweede regel, "één telling". Met stippen is de bovenrand
    dus altijd 44 (was 30 zonder keuze).
  - Bij een keuze alleen de stippen van de keuze, niet die van alle stukken.
- **Uitleg** boven de grafiek: een zin over de stippen, en het verschil met de
  marge.

## 3. Wat niet verandert

- De curve, de marges, de factoren en de tabellen. Op een gemaakte set van 300
  tellingen is `DAGCURVE` zonder `stippen` gelijk aan v3.51.
- **`dagcurve.csv`** blijft zoals hij is. De stippen als CSV (een rij per
  telling per uur) zou een schemawijziging zijn: eerst aan Jay voorleggen. Ze
  zijn na te rekenen uit `passages.csv`.
- De rekentijd: 300 tellingen 0,8–1,2 s, in v3.51 hetzelfde (`dcStippen` is één
  lus).

## 4. Handleiding

In de rij Dagcurve van Passanten: *De stippen* (sinds v3.52). Wat een stip is,
het verschil met de marge, de kleine stip en het driehoekje, en dat je een stip
kunt aanwijzen.

## 5. Tests

- **`functest_dagcurve.js`: 53 (was 46).** Nieuw deel "v3.52: de stippen":
  - zonder ruis (het eerste plan): elke stip precies op de index, één per
    telling per uur;
  - met ruis (100 tellingen): één stip per telling en uur, alleen in vakjes die
    te scheiden zijn;
  - per vakje: het gewogen gemiddelde = de index, en de tegemoetkomers samen =
    die van het vakje;
  - ze liggen niet op de curve (werkdag 12);
  - een keuze: alleen tellingen die de gekozen stukken liepen.
  - De vergelijking met de oude union-find (v3.51) leest de oude nummering op
    `o.u`; de test past de ene regel in `dcStippen` daarop aan, en vergelijkt
    dan nog steeds de hele dagcurve, stippen inbegrepen.
- **`passantentest.py`: 96 (was 93).** Twee stippen in zaterdag 13, gewogen
  samen 100, de een eronder en de ander erboven; alleen die twee getekend (werkdag
  11 heeft geen curve), in de zaterdagkleur, met tooltip; onder de curve, en
  "één telling" in de legenda.

## 6. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `passanten.html` | `dcStippen`, `dcOpzij`; `t` in `dcWaarnemingen`; `A`/`uNr` uit `dcSchat`, `gem`/`r` uit `dcNormeer`; `dcGrafiek` en de uitleg |
| `traffic_counter_help.html` | *De stippen* in de rij Dagcurve |
| `index.html` | versie v3.52 |
| `_archief/overpass_rig/functest_dagcurve.js`, `passantentest.py` | zie §5 |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 7. Validatie

```
valideer.py              ALLES OK — de 3 verwachte bestanden
functest_dagcurve.js     53/53
passantentest.py         96/96
300 tellingen            DAGCURVE zonder stippen gelijk aan v3.51
volledige ronde lokaal: zie de PR
```
