# Overdracht v3.59 — Passanten: het etmaal op de kaart

Jay vroeg welke dagkromme het dagtotaal in de dag-uurtabel gebruikt. Het
antwoord: de geladen dagkrommen, en anders de eigen dagcurve. Daarna: "Maak er
in passanten.html maar een etmaal-knop bij, met knoppen voor de 7 dagen - teken
dan op het netwerk de geschatte etmaal totaal."

## 1. Wat je ziet

- **De knop etmaal** staat aan het eind van de rij Uur.
- **De dagknoppen** ma–zo kiezen dan de weekdag. In de etmaalstand zijn alle
  zeven dagen te kiezen, ook een dag waarop niet geteld is; dat is juist het
  nut van een schatting.
- **Elk stuk** krijgt een kleur en een getal: het geschatte totaal van 0:00 tot
  24:00 op die weekdag.
  - ≥ betekent dat er uren niet te schatten waren: minstens dit.
  - \* betekent dat er opgehoogd is (één richting gemeten).
  - Grijs: niet te schatten.
- **De legenda** "Passanten per etmaal · <dag>, geschat" noemt de bron
  (dagkrommen of dagcurve). Een eigen kleurschaal loopt over alle stukken en
  alle zeven dagen (`MAXE`). De regels over ≥ en \* staan er alleen als ze op
  de kaart voorkomen.
- **Een uur kiezen** brengt je terug naar passanten per uur.
- **Een stuk aanklikken** opent het weekoverzicht, zoals altijd.

## 2. De rekening

`etmaalVan(seg, d)` = `dagTotaal(seg, weekSchatter(seg, 0, 23), d, 0, 23)`: dezelfde
rekening als het dagtotaal 9–21 in het weekoverzicht (v3.56), over 24 uur.

- **Gemeten uren** (niet te kort): `schat(c, seg).q`.
- **Met dagkrommen**: niveau van het stuk × kromme[dag][uur]. Elk uur is te
  schatten, dus er is geen ≥.
- **Zonder dagkrommen**: de eigen dagcurve. Hebben de nachturen geen curve
  (er is 's nachts niet geteld), dan vallen ze weg en staat er ≥.
- Het venster 9–21 van de tabel verandert niet: `dagTotaal`, `weekSchatter` en
  `krommenSchatter` krijgen een venster mee, en zonder venster blijft het 9–21.

## 3. Code

- `ETMAAL`, `MAXE` (`herbereken` en `zetDagkrommen` maken hem leeg), `etmaalVan`,
  `etmaalMax`, `kiesEtmaal`, `tekenEtmaal`.
- `tekenKaart` gaat in de etmaalstand naar `tekenEtmaal`. `kiesUur` zet
  `ETMAAL` uit. `kiesDag` houdt in de etmaalstand het uur zoals het is.
- `kleur(q, max)`: een eigen maximum voor het etmaal.
- `GEMETEN` heeft nu `q` en `tekst` per label (en `c` in de uurstand,
  `etmaal` in de etmaalstand). `tekenLabels` sorteert op `q`.
- 250 stukken × 7 dagen voor de schaal: ruim binnen een halve seconde, eenmalig.

## 4. Tests

**`passantentest.py`: 117 (was 114).**

- Zonder krommen, zaterdag: de Voorstraat is ≥ het gemeten uur 13 (de andere
  uren hebben geen dagcurve). Alle dagen zijn te kiezen; de legenda staat per
  etmaal; elke lijn is getekend.
- Een uur kiezen: terug naar per uur.
- Met de zelfgemaakte kromme, zaterdag: de Voorstraat is het gemeten uur 13
  plus het niveau × de kromme over de andere 23 uur, zonder ≥. De legenda noemt
  de krommen en geen ≥.
- **Bewust aangepast:** "uur: alleen 13" telt nu ook de knop etmaal.

## 5. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `passanten.html` | §3 |
| `traffic_counter_help.html` | Etmaal, in de inleiding van Passanten |
| `index.html` | versie v3.59 |
| `_archief/overpass_rig/passantentest.py` | zie §4 |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 6. Validatie

```
valideer.py           ALLES OK — de 3 verwachte bestanden
passantentest.py      117/117
functest_passanten    26/26, functest_dagcurve 63/63
volledige ronde lokaal: zie de PR
```
