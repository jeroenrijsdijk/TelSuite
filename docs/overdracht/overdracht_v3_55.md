# Overdracht v3.55 — Passanten: vijf klusjes

Jay verzamelde vier kleine klussen ("ga niet gelijk aan het werk") en gaf
daarna het sein: "Dit is de laatste aanpassig voor nu, je mag aan de slag".

## 1. Het origineel naast zijn reconstructie niet in de melding

Jay: "Je geeft na het inlezen van winkelstraat zips een lijst bestanden die je
niet gebruikt hebt . De recon/origineel hoef je daar niet te laten zien."

- De melding "Niet meegenomen" slaat de reden `RECON_REDEN` ("origineel; de
  reconstructie doet mee") over. Dat geldt ook voor een origineel dat pas op
  `sessie_id` herkend is.
- `OVERGESLAGEN` houdt het wel, en de tests kijken daar ook naar.
- Is er niets anders over, dan is de melding niet meer oranje.

## 2. Gemiddelden in het weekoverzicht

Jay: "Aan het einde van de rij geef je een dag gemiddelde maar dat is bij een
half getelde week geen betrouwbare waarde". Na de opties: "Je mag bijschaven met
de dagcurve, maar zet er een duidelijk sterretje bij dat het geschat is.
Markeer ook als het aantal tellingen genoeg dekt".

- **Voorheen** waren alle gemeten passages van die dag of dat uur samen
  gerekend. Een dag met alleen 13 uur gemeten kreeg dus de waarde van 13 uur.
- **Nu loopt een gemiddelde over de vakjes (dag, uur):**
  - waar de dagcurve van het gebied er is (`dcKern`, `genoeg`);
  - plus de vakjes die gemeten zijn.
- **Gemeten** (niet te kort): `schat(c, seg).q`.
- **Niet of te kort gemeten:** `3600 · Σ A[stuk|richting] · F[dagtype:uur] · D[weekdag]`.
  - A geeft tegemoetkomers per seconde venster, dus dit is direct passanten per
    uur.
  - Daarna × de ophoging van het hele stuk (`schat(samen(alle cellen)).f`) en
    × `IJKFACTOR`.
  - Hangt het stuk niet aan de grootste groep, dan valt er niets te schatten.
    Die uren tellen als "open" (niet gemeten en niet geschat).
- **Het gemiddelde** is het gewone gemiddelde van de vakjes, niet meer
  gepoold.
- **Teken:**
  - **≈** voor het getal betekent: deels geschat. Het sterretje betekent in die
    tabel al "één richting, opgehoogd". Dat blijft zo, en staat er ook bij
    een geschatte waarde als het stuk opgehoogd wordt.
  - Kanttekening: in het detail staat al jaren "≈ 486 passanten per uur" in de
    betekenis van "ongeveer". Het teken is dus niet helemaal exclusief.
- **Markering:**
  - **vet** (`gedekt`): minstens `WEEK_GEDEKT` = 80% van de vakjes gemeten, en
    er is minstens één uur met een dagcurve;
  - **grijs** (`dun`): anders.

  De tooltip zegt hoeveel uur gemeten, geschat en open is.
- **Klopt de schatting?** Op de gemaakte set van 300 tellingen: over 4.705
  gemeten vakjes is de som van de schattingen 0,994 keer de som van de
  metingen. Per vakje is de spreiding groot (dagen verschillen).

## 3. De kop boven het detail

Jay: "Maak wel de naam van de dag het het uurtarief wat duidelijker: als ik op
een uur klik in de tabel verschijnt onderin alleen de waarde van dat uur. De
tekst van dat dag-uur mag wat duidelijker".

Boven het detail staat nu een kop: "Zaterdag 13:00–14:00 · 17-10, 24-10"
(`.week-moment`). Het aangeklikte vakje had al een rand.

## 4. Vijf momenten

Jay: "Je geeft nu bij de link-details 3 momenten waarop we zouden moeten
tellen. Daar mag je 5 momenten van maken."

`PLAN_ADVIES` = 5. De legenda volgt vanzelf ("eerst tellen (1–5)").

## 5. Inzoomen op de laatste tellingen

Jay, na het sein: "Toch nog iets - je mag na het laden inzoomen naar de laatst
gedane tellingen".

- Na elk inlezen zoomt de kaart naar de stukken van de laatst gedane
  tellingen (`zoomLaatste`, `pad(0.15)`, hooguit zoom 18). Dat zijn alle
  tellingen van de laatste datum (`laatsteTellingen`).
- Voorheen paste de kaart zich alleen bij het eerste inlezen aan, aan alle
  stukken.
- Op de gemaakte set liggen de twee laatste tellingen over het hele gebied;
  daar is het zoomniveau dus hetzelfde.

## 6. Tests

- **`passantentest.py`: 106 (was 102).**
  - Het origineel staat niet in de melding.
  - Gem. over alles is het gemiddelde van de twee vakjes, niets geschat.
  - Zaterdag is vet; donderdag (geen dagcurve) grijs.
  - Zonder de meting van zaterdag 13 wordt dat uur geschat: ≈, 0 van 1
    gemeten, 622 tegen gemeten 628.
  - De kop boven het detail.
  - Hooguit 5 momenten.
  - Na het inlezen: de laatste telling (24-10) gekozen, al haar stukken in
    beeld, op het zoomniveau dat daarbij hoort.
- **Bewust aangepast:** "gem. over alles: beide cellen samen gerekend, niet het
  gemiddelde". Het is nu juist het gemiddelde.
- **`functest_dagcurve.js`: 63**, de eis voor het advies naar hooguit 5.

## 7. Gewijzigde bestanden

| bestand | wat |
|---|---|
| `passanten.html` | `RECON_REDEN`; `weekSchatter`, `weekGem`, `weekGemTd`; `.week-moment`; `PLAN_ADVIES`; `laatsteTellingen`, `zoomLaatste`; de uitleg boven de tabel; CSS |
| `traffic_counter_help.html` | Passanten: inlezen en inzoomen, gem., de kop, vijf momenten |
| `index.html` | versie v3.55 |
| `_archief/overpass_rig/passantentest.py`, `functest_dagcurve.js` | zie §5 |
| `_archief/overpass_rig/valideer.py`, `README.md`, `docs/OVERDRACHT_STAND_VAN_ZAKEN.md` | bijgewerkt |

## 8. Validatie

```
valideer.py              ALLES OK — de 3 verwachte bestanden
passantentest.py         106/106
functest_dagcurve.js     63/63
300 tellingen            schatting ÷ meting 0,994 over 4.705 vakjes
volledige ronde lokaal: zie de PR
```
