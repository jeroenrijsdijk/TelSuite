# Overdracht v3.56 — Passanten: het dagtotaal 9–21

Jay vroeg eerst hoe het daggemiddelde van v3.55 berekend wordt. Na de uitleg:
"Ik zou in in die kolom het geschatte dagtotaal willen hebben, tussen 9:00 en
20:59 uur. De missende tellingen mag je schatten uit de dagkromme."

## 1. Wat er in de laatste kolom staat

De kolom heet nu **dag 9–21**. Per weekdag de som van de uren 9 tot en met 20
(`DAG_VAN`, `DAG_TOT`).

- **Gemeten** (niet te kort): `schat(c, seg).q`, zoals in het vakje.
- **Niet of te kort gemeten:** geschat met de dagcurve (`weekSchatter`, v3.55):
  3600 · Σ A · F · D × ophoging × `IJKFACTOR`. Er staat **≈** voor het totaal.
- **Een uur zonder dagcurve**: het gebied heeft daar te weinig, of het stuk
  hangt niet aan de rest. Dat uur is niet te schatten en valt weg. Het totaal
  is dan een ondergrens, met **≥** ervoor. ≥ gaat voor ≈.
- **\*** erachter als er opgehoogd is (één richting).
- **Vet:** minstens 80% van de 12 uur gemeten (10 uur). Anders grijs.
- **Het hoekvakje:** het gemiddelde dagtotaal over de dagen die een totaal
  hebben.
- **De tooltip** noemt hoeveel uur gemeten en geschat is, en welke uren
  wegvielen.
- **De rij gem. onderaan** blijft het gemiddelde per uur van v3.55.

## 2. Wat je kunt verwachten

Op de gemaakte sets heeft niemand na 18 uur geteld, dus de dagcurve heeft 18,
19 en 20 uur niet. Daar is elk dagtotaal ≥: ruwweg 9 van de 12 uur.

Bij Jays echte tellingen hangt het ervan af of er 's avonds geteld is.
Mogelijk vervolg, als ≥ te vaak voorkomt:

- het venster korter maken (bijvoorbeeld 9–18);
- of de avond schatten met een aanname, maar die is niet gemeten.

## 3. Tests

**`passantentest.py`: 108 (was 106).** In de testset heeft alleen zaterdag
13 uur een dagcurve.

- De kop heet "dag 9–21". Zaterdag en donderdag hebben ≥ met hun ene gemeten
  uur. Het hoekvakje is ≥ het gemiddelde van die twee.
- De tooltip noemt de 11 weggevallen uren. De cel is grijs.
- Zonder de meting van zaterdag 13 wordt dat uur geschat (622 tegen gemeten
  628). Het totaal is ≥, omdat de rest wegvalt.
- Met een schatter voor elk uur staat er ≈ en geen ≥: het gemeten uur plus
  11 × de schatting.
- De rij gem. per uur is zoals in v3.55.
- **Bewust aangepast:** de Kerkstraat (één richting). Het dagtotaal is
  ≥ … \*; de ophoging × 2 blijft.

## 4. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `passanten.html` | `DAG_VAN`, `DAG_TOT`, `dagTotaal`, `dagTekst`, `dagTotaalTd`; de kop en de uitleg boven de tabel |
| `traffic_counter_help.html` | het dagtotaal in de rij Klik op een stuk |
| `index.html` | versie v3.56 |
| `_archief/overpass_rig/passantentest.py` | zie §3 |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 5. Validatie

```
valideer.py           ALLES OK — de 3 verwachte bestanden
passantentest.py      108/108
volledige ronde lokaal: zie de PR
```
